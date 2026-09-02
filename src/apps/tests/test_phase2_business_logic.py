import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.attendance.models import Attendance
from apps.category.models import Category
from apps.common.context import set_current_tenant, clear_current_tenant
from apps.course.models import Group
from apps.course.models.course import Course
from apps.course.models.group_schedule import GroupSchedule
from apps.course.models.lesson import Lesson
from apps.course.services.lesson_generator import generate_lessons_for_group
from apps.course.services.lesson_lifecycle import complete_lesson, cancel_lesson
from apps.enrollment.models import Enrollment
from apps.enrollment.services.lifecycle import (
    transfer_student,
    graduate_student,
    dropout_student,
    freeze_student,
    unfreeze_student,
)
from apps.history.models import History
from apps.organization.models import Organization
from apps.users.models import User, TeacherProfile, StudentProfile

def make_org(name="Test Org"):
    return Organization.objects.create(name=name)


def _counter():
    return User.objects.count()


def make_user(org, role=User.Status.TEACHER, phone=None):
    phone = phone or f"+998{_counter() + 900000000:09d}"
    return User.objects.create_user(
        phone=phone, password="pass123", role=role,
        organization=org, is_active=True,
        is_staff=(role != User.Status.STUDENT),
    )


def make_teacher(org):
    u = make_user(org, User.Status.TEACHER)
    return TeacherProfile.objects.create(user=u, organization=org, subject="Math")


def make_student(org):
    u = make_user(org, User.Status.STUDENT)
    return StudentProfile.objects.create(
        user=u, organization=org,
        parent_phone="+998901234567",
        status=StudentProfile.StudentStatus.ACTIVE,
    )


def make_admin(org):
    return make_user(org, User.Status.ADMIN)


def make_course(org):
    cat = Category.objects.create(name=f"Cat-{_counter()}", organization=org)
    return Course.objects.create(
        title="Test Course", category=cat, organization=org,
        duration="3 months", lesson_count=30, price=500_000,
    )


def make_group(org, course, name="Group A", teacher=None):
    return Group.objects.create(
        organization=org, course=course, name=name,
        teacher=teacher, start_date=datetime.date.today(),
    )


def make_schedule(group, days=None):
    """Create a GroupSchedule for the given group on the specified days."""
    days = days or [GroupSchedule.DAYS.MONDAY, GroupSchedule.DAYS.WEDNESDAY, GroupSchedule.DAYS.FRIDAY]
    return GroupSchedule.all_objects.create(
        group=group,
        selected_days=days,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 30),
    )


def make_lesson(group, date=None, status=Lesson.Status.PLANNED):
    return Lesson.objects.create(
        group=group,
        date=date or datetime.date.today(),
        status=status,
    )


def enroll(student, group):
    return Enrollment.objects.create(
        student=student, group=group, status=Enrollment.Status.ACTIVE
    )


class LessonGenerationServiceTest(TestCase):

    def setUp(self):
        self.org = make_org("Gen Org")
        set_current_tenant(organization_id=self.org.id)
        self.teacher = make_teacher(self.org)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course, teacher=self.teacher)

    def tearDown(self):
        clear_current_tenant()

    def test_generate_creates_lessons_on_scheduled_days(self):
        """Service generates PLANNED lessons only on the days in GroupSchedule."""
        # Monday=0, Wednesday=2, Friday=4
        GroupSchedule.all_objects.create(
            group=self.group,
            selected_days=[GroupSchedule.DAYS.MONDAY, GroupSchedule.DAYS.WEDNESDAY],
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
        )
        start = datetime.date(2026, 9, 1)  # Tuesday
        end = datetime.date(2026, 9, 14)  # Two weeks
        self.group.start_date = start
        self.group.save()

        created = generate_lessons_for_group(group=self.group, end_date=end)

        # Mondays in range: 7, 14 Sept; Wednesdays: 2, 9 Sept → 4 lessons
        self.assertEqual(len(created), 4)
        for lesson in created:
            self.assertIn(lesson.date.weekday(), [0, 2],
                          "All lessons must fall on Monday(0) or Wednesday(2)")
            self.assertEqual(lesson.status, Lesson.Status.PLANNED)

    def test_generate_skips_existing_lessons(self):
        """Generator does not create duplicate lessons for dates that already exist."""
        GroupSchedule.all_objects.create(
            group=self.group,
            selected_days=[GroupSchedule.DAYS.MONDAY],
            start_time=datetime.time(9, 0), end_time=datetime.time(10, 30),
        )
        monday = datetime.date(2026, 9, 7)
        self.group.start_date = monday
        self.group.save()

        # Pre-create a lesson for that Monday
        Lesson.objects.create(group=self.group, date=monday, status=Lesson.Status.PLANNED)
        created = generate_lessons_for_group(group=self.group, end_date=monday)

        self.assertEqual(len(created), 0, "Should not duplicate existing lesson")

    def test_generate_raises_without_schedule(self):
        """Raises ValueError if no GroupSchedule exists for the group."""
        with self.assertRaises(ValueError, msg="No schedule → ValueError"):
            generate_lessons_for_group(group=self.group)

    def test_generate_assigns_group_teacher_to_lessons(self):
        """Generated lessons get the group's assigned teacher."""
        GroupSchedule.all_objects.create(
            group=self.group,
            selected_days=[GroupSchedule.DAYS.FRIDAY],
            start_time=datetime.time(10, 0), end_time=datetime.time(11, 0),
        )
        friday = datetime.date(2026, 9, 4)
        self.group.start_date = friday
        self.group.save()
        created = generate_lessons_for_group(group=self.group, end_date=friday)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].teacher, self.teacher)


# ---------------------------------------------------------------------------
# 2.2 — GroupSchedule Signal
# ---------------------------------------------------------------------------

class GroupScheduleSignalTest(TestCase):
    """When a GroupSchedule is saved, lessons are auto-generated via signal."""

    def setUp(self):
        self.org = make_org("Signal Org")
        set_current_tenant(organization_id=self.org.id)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course)
        # Set start_date to a known Monday
        self.group.start_date = datetime.date(2026, 9, 7)
        self.group.save()

    def tearDown(self):
        clear_current_tenant()

    def test_schedule_create_triggers_lesson_generation(self):
        """Creating a GroupSchedule should auto-generate PLANNED lessons."""
        initial_count = Lesson.all_objects.filter(group=self.group).count()
        GroupSchedule.all_objects.create(
            group=self.group,
            selected_days=[GroupSchedule.DAYS.MONDAY, GroupSchedule.DAYS.THURSDAY],
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        final_count = Lesson.all_objects.filter(group=self.group).count()
        self.assertGreater(final_count, initial_count,
                           "Creating a schedule should auto-generate lessons")


# ---------------------------------------------------------------------------
# 2.3 — Lesson Complete → Auto-Attendance
# ---------------------------------------------------------------------------

class LessonCompleteTest(TestCase):

    def setUp(self):
        self.org = make_org("Complete Org")
        set_current_tenant(organization_id=self.org.id)
        self.admin = make_admin(self.org)
        self.teacher = make_teacher(self.org)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course, teacher=self.teacher)
        self.lesson = make_lesson(self.group)
        # 3 enrolled students
        self.students = [make_student(self.org) for _ in range(3)]
        for s in self.students:
            enroll(s, self.group)

    def tearDown(self):
        clear_current_tenant()

    def test_complete_creates_absent_attendance_for_all_enrolled(self):
        """Completing a lesson creates ABSENT records for all active enrolled students."""
        lesson, attendances = complete_lesson(
            lesson=self.lesson,
            performed_by=self.admin,
            organization=self.org,
        )
        self.assertEqual(lesson.status, Lesson.Status.COMPLETED)
        self.assertEqual(len(attendances), 3)
        for att in attendances:
            self.assertEqual(att.status, Attendance.Status.ABSENT)
            self.assertEqual(att.lesson, lesson)

    def test_complete_skips_frozen_students(self):
        """Frozen students do NOT get attendance records."""
        frozen = self.students[0]
        frozen.status = StudentProfile.StudentStatus.FROZEN
        frozen.save()

        _, attendances = complete_lesson(
            lesson=self.lesson,
            performed_by=self.admin,
            organization=self.org,
        )
        attendance_student_ids = [a.student_id for a in attendances]
        self.assertNotIn(frozen.pk, attendance_student_ids)
        self.assertEqual(len(attendances), 2)

    def test_complete_raises_if_already_completed(self):
        """Cannot complete a lesson that's already completed."""
        self.lesson.status = Lesson.Status.COMPLETED
        self.lesson.save()
        with self.assertRaises(ValueError):
            complete_lesson(lesson=self.lesson, performed_by=self.admin, organization=self.org)

    def test_complete_writes_history(self):
        """Completing a lesson writes a LESSON_COMPLETED history entry."""
        complete_lesson(lesson=self.lesson, performed_by=self.admin, organization=self.org)
        entry = History.objects.filter(action=History.Action.LESSON_COMPLETED).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.organization, self.org)


# ---------------------------------------------------------------------------
# 2.4 — Lesson Cancel
# ---------------------------------------------------------------------------

class LessonCancelTest(TestCase):

    def setUp(self):
        self.org = make_org("Cancel Org")
        set_current_tenant(organization_id=self.org.id)
        self.admin = make_admin(self.org)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course)
        self.lesson = make_lesson(self.group)

    def tearDown(self):
        clear_current_tenant()

    def test_cancel_requires_reason(self):
        with self.assertRaises(ValueError, msg="Cancellation without reason must raise"):
            cancel_lesson(lesson=self.lesson, reason="", performed_by=self.admin, organization=self.org)

    def test_cancel_transitions_to_cancelled(self):
        lesson = cancel_lesson(
            lesson=self.lesson, reason="National holiday",
            performed_by=self.admin, organization=self.org,
        )
        self.assertEqual(lesson.status, Lesson.Status.CANCELLED)
        self.assertEqual(lesson.reason, "National holiday")

    def test_cancel_rejects_already_completed_lesson(self):
        self.lesson.status = Lesson.Status.COMPLETED
        self.lesson.save()
        with self.assertRaises(ValueError):
            cancel_lesson(lesson=self.lesson, reason="Test", performed_by=self.admin, organization=self.org)

    def test_cancel_writes_history(self):
        cancel_lesson(lesson=self.lesson, reason="Teacher sick", performed_by=self.admin, organization=self.org)
        entry = History.objects.filter(action=History.Action.LESSON_CANCELLED).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.meta['reason'], "Teacher sick")


# ---------------------------------------------------------------------------
# 2.5 — Student Transfer
# ---------------------------------------------------------------------------

class StudentTransferTest(TestCase):

    def setUp(self):
        self.org = make_org("Transfer Org")
        set_current_tenant(organization_id=self.org.id)
        self.admin = make_admin(self.org)
        self.course = make_course(self.org)
        self.group_a = make_group(self.org, self.course, name="Group A")
        self.group_b = make_group(self.org, self.course, name="Group B")
        self.student = make_student(self.org)
        self.enrollment = enroll(self.student, self.group_a)

    def tearDown(self):
        clear_current_tenant()

    def test_transfer_closes_old_enrollment_opens_new(self):
        new_enrollment = transfer_student(
            enrollment=self.enrollment, to_group=self.group_b,
            performed_by=self.admin, organization=self.org,
        )
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.DROPPED)
        self.assertIsNotNone(self.enrollment.left_at)
        self.assertEqual(new_enrollment.group, self.group_b)
        self.assertEqual(new_enrollment.status, Enrollment.Status.ACTIVE)

    def test_transfer_to_same_group_raises(self):
        with self.assertRaises(ValueError):
            transfer_student(
                enrollment=self.enrollment, to_group=self.group_a,
                performed_by=self.admin, organization=self.org,
            )

    def test_transfer_writes_history_with_meta(self):
        transfer_student(
            enrollment=self.enrollment, to_group=self.group_b,
            performed_by=self.admin, organization=self.org,
        )
        entry = History.objects.filter(action=History.Action.STUDENT_TRANSFERRED).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.meta['from_group_name'], "Group A")
        self.assertEqual(entry.meta['to_group_name'], "Group B")


# ---------------------------------------------------------------------------
# 2.6 — Graduate / Dropout
# ---------------------------------------------------------------------------

class StudentGraduateDropoutTest(TestCase):

    def setUp(self):
        self.org = make_org("Grad Org")
        set_current_tenant(organization_id=self.org.id)
        self.admin = make_admin(self.org)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course)

    def tearDown(self):
        clear_current_tenant()

    def test_graduate_sets_profile_status_graduated(self):
        student = make_student(self.org)
        enrollment = enroll(student, self.group)
        graduate_student(enrollment=enrollment, performed_by=self.admin, organization=self.org)
        student.refresh_from_db()
        enrollment.refresh_from_db()
        self.assertEqual(student.status, StudentProfile.StudentStatus.GRADUATED)
        self.assertEqual(enrollment.status, Enrollment.Status.FINISHED)
        self.assertIsNotNone(enrollment.left_at)

    def test_dropout_sets_profile_status_dropped(self):
        student = make_student(self.org)
        enrollment = enroll(student, self.group)
        dropout_student(enrollment=enrollment, performed_by=self.admin, organization=self.org, reason="left city")
        student.refresh_from_db()
        enrollment.refresh_from_db()
        self.assertEqual(student.status, StudentProfile.StudentStatus.DROPPED)
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)

    def test_graduate_writes_history(self):
        student = make_student(self.org)
        enrollment = enroll(student, self.group)
        graduate_student(enrollment=enrollment, performed_by=self.admin, organization=self.org)
        entry = History.objects.filter(action=History.Action.STUDENT_GRADUATED).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.student, student)

    def test_dropout_writes_history(self):
        student = make_student(self.org)
        enrollment = enroll(student, self.group)
        dropout_student(enrollment=enrollment, performed_by=self.admin, organization=self.org)
        entry = History.objects.filter(action=History.Action.STUDENT_DROPPED).first()
        self.assertIsNotNone(entry)


# ---------------------------------------------------------------------------
# 2.7 — Freeze / Unfreeze
# ---------------------------------------------------------------------------

class StudentFreezeTest(TestCase):

    def setUp(self):
        self.org = make_org("Freeze Org")
        set_current_tenant(organization_id=self.org.id)
        self.admin = make_admin(self.org)
        self.student = make_student(self.org)

    def tearDown(self):
        clear_current_tenant()

    def test_freeze_sets_status_frozen(self):
        freeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, StudentProfile.StudentStatus.FROZEN)

    def test_freeze_already_frozen_raises(self):
        freeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        with self.assertRaises(ValueError):
            freeze_student(student=self.student, performed_by=self.admin, organization=self.org)

    def test_unfreeze_restores_active(self):
        freeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        unfreeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        self.student.refresh_from_db()
        self.assertEqual(self.student.status, StudentProfile.StudentStatus.ACTIVE)

    def test_unfreeze_not_frozen_raises(self):
        with self.assertRaises(ValueError):
            unfreeze_student(student=self.student, performed_by=self.admin, organization=self.org)

    def test_frozen_student_skipped_in_lesson_complete(self):
        """Frozen students do not receive attendance records when a lesson is completed."""
        course = make_course(self.org)
        group = make_group(self.org, course)
        enroll(self.student, group)
        lesson = make_lesson(group)

        freeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        self.student.refresh_from_db()

        _, attendances = complete_lesson(lesson=lesson, performed_by=self.admin, organization=self.org)
        att_student_ids = [a.student_id for a in attendances]
        self.assertNotIn(self.student.pk, att_student_ids)

    def test_freeze_writes_history(self):
        freeze_student(student=self.student, performed_by=self.admin, organization=self.org, reason="vacation")
        entry = History.objects.filter(action=History.Action.STUDENT_FROZEN).first()
        self.assertIsNotNone(entry)

    def test_unfreeze_writes_history(self):
        freeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        unfreeze_student(student=self.student, performed_by=self.admin, organization=self.org)
        entry = History.objects.filter(action=History.Action.STUDENT_UNFROZEN).first()
        self.assertIsNotNone(entry)


# ---------------------------------------------------------------------------
# 2.8 — Lesson UniqueConstraint (one lesson per group per date)
# ---------------------------------------------------------------------------

class LessonUniqueDateConstraintTest(TestCase):

    def setUp(self):
        self.org = make_org("UniqueLesson Org")
        set_current_tenant(organization_id=self.org.id)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course)

    def tearDown(self):
        clear_current_tenant()

    def test_duplicate_lesson_for_same_group_and_date_is_rejected(self):
        date = datetime.date(2026, 9, 10)
        Lesson.objects.create(group=self.group, date=date, status=Lesson.Status.PLANNED)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lesson.objects.create(group=self.group, date=date, status=Lesson.Status.PLANNED)

    def test_same_date_different_groups_is_allowed(self):
        org2 = make_org("Org2")
        course2 = make_course(org2)
        group2 = make_group(org2, course2)
        date = datetime.date(2026, 9, 10)
        Lesson.objects.create(group=self.group, date=date)
        # Must not raise
        Lesson.objects.create(group=group2, date=date)
        self.assertEqual(Lesson.all_objects.filter(date=date).count(), 2)

"""
Phase 1 Model Fix Tests
=======================
Tests for all data model changes made in Phase 1 of the Flowhub CRM roadmap:

1. Attendance.lesson FK replaces raw date+group fields
2. Payment model overhaul (enrollment, due_date, for_month, received_by, manual payment_date)
3. TeacherProfile + StaffProfile are now tenant-scoped (TenantBaseModel)
4. Group.name uniqueness is per-organization, not global

Run:
    python manage.py test apps.tests.test_phase1_fixes -v 2
"""
import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from apps.attendance.models import Attendance
from apps.common.context import set_current_tenant, clear_current_tenant
from apps.course.models import Group
from apps.course.models.lesson import Lesson
from apps.enrollment.models import Enrollment
from apps.organization.models import Organization
from apps.payment.models import Payment
from apps.users.models import User, TeacherProfile, StaffProfile, StudentProfile
from apps.course.models.course import Course
from apps.category.models import Category


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_org(name="Test Org"):
    return Organization.objects.create(name=name)


def make_user(phone, org, role=User.Status.TEACHER):
    return User.objects.create_user(
        phone=phone,
        password="testpass123",
        role=role,
        organization=org,
        is_active=True,
        is_staff=(role != User.Status.STUDENT),
    )


def make_course(org):
    cat = Category.objects.create(name=f"Cat-{org.id}", organization=org)
    return Course.objects.create(
        title="Test Course",
        category=cat,
        organization=org,
        duration="3 months",
        lesson_count=30,
        price=500_000,
    )


def make_group(org, course, name="Group A", teacher=None):
    return Group.objects.create(
        organization=org,
        course=course,
        name=name,
        teacher=teacher,
        start_date=datetime.date.today(),
    )


def make_lesson(group, date=None):
    return Lesson.objects.create(
        group=group,
        date=date or datetime.date.today(),
        status=Lesson.Status.COMPLETED,
    )


def make_student(org):
    user = make_user(
        phone=f"+9989{User.objects.count():08d}",
        org=org,
        role=User.Status.STUDENT,
    )
    return StudentProfile.objects.create(
        user=user,
        organization=org,
        parent_phone="+998901234567",
        status=StudentProfile.StudentStatus.ACTIVE,
    )


# ---------------------------------------------------------------------------
# 1. Attendance Model Tests
# ---------------------------------------------------------------------------

class AttendanceModelTest(TestCase):
    """Tests that Attendance is now anchored to a Lesson, not a raw date."""

    def setUp(self):
        self.org = make_org("Erasmus")
        set_current_tenant(organization_id=self.org.id)

        teacher_user = make_user("+998901111111", self.org, User.Status.TEACHER)
        self.teacher_profile = TeacherProfile.objects.create(
            user=teacher_user,
            organization=self.org,
            subject="Math",
        )
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course, teacher=self.teacher_profile)
        self.lesson = make_lesson(self.group, date=datetime.date(2026, 8, 11))
        self.student = make_student(self.org)

    def tearDown(self):
        clear_current_tenant()

    def test_attendance_requires_lesson_fk(self):
        """Attendance must be created with a lesson FK, not a raw date."""
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        self.assertIsNotNone(attendance.pk)
        self.assertEqual(attendance.lesson, self.lesson)

    def test_attendance_date_property_derives_from_lesson(self):
        """attendance.date should return the lesson's date, not a stored field."""
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        self.assertEqual(attendance.date, datetime.date(2026, 8, 11))

    def test_attendance_group_property_derives_from_lesson(self):
        """attendance.group should return the lesson's group."""
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.ABSENT,
            organization=self.org,
        )
        self.assertEqual(attendance.group, self.group)

    def test_attendance_unique_per_lesson_per_student(self):
        """A student cannot have two Attendance records for the same Lesson."""
        Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(
                    lesson=self.lesson,
                    student=self.student,
                    status=Attendance.Status.ABSENT,
                    organization=self.org,
                )

    def test_attendance_no_longer_has_raw_date_field(self):
        """The `date` column should not be a database field on Attendance."""
        field_names = [f.name for f in Attendance._meta.get_fields()]
        self.assertNotIn('date', field_names,
                         "Attendance.date should be a property, not a DB column")

    def test_attendance_no_longer_has_raw_group_field(self):
        """The `group` column should not be a database field on Attendance."""
        field_names = [f.name for f in Attendance._meta.get_fields()]
        self.assertNotIn('group', field_names,
                         "Attendance.group should be a property, not a DB column")


# ---------------------------------------------------------------------------
# 2. Payment Model Tests
# ---------------------------------------------------------------------------

class PaymentModelTest(TestCase):
    """Tests for the overhauled Payment model."""

    def setUp(self):
        self.org = make_org("Big Ben Academy")
        set_current_tenant(organization_id=self.org.id)

        self.admin_user = make_user("+998902222222", self.org, User.Status.ADMIN)
        self.student = make_student(self.org)
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course, name="Group B")
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            group=self.group,
            status=Enrollment.Status.ACTIVE,
        )

    def tearDown(self):
        clear_current_tenant()

    def test_payment_with_manual_date(self):
        """payment_date is now a manual DateField — backdating must work."""
        past_date = datetime.date(2026, 7, 1)
        payment = Payment.objects.create(
            student=self.student,
            organization=self.org,
            amount=500_000,
            payment_date=past_date,
            payment_type=Payment.PaymentType.CASH,
            status=Payment.Status.PAID,
        )
        self.assertEqual(payment.payment_date, past_date)

    def test_payment_with_enrollment_fk(self):
        """Payment can be linked to a specific enrollment (group/course)."""
        payment = Payment.objects.create(
            student=self.student,
            enrollment=self.enrollment,
            organization=self.org,
            amount=500_000,
            payment_date=datetime.date.today(),
            payment_type=Payment.PaymentType.CARD,
            status=Payment.Status.PAID,
        )
        self.assertEqual(payment.enrollment, self.enrollment)
        self.assertEqual(payment.enrollment.group, self.group)

    def test_payment_with_due_date(self):
        """Payment can carry a due_date for upcoming-payment tracking."""
        due = datetime.date(2026, 9, 1)
        payment = Payment.objects.create(
            student=self.student,
            organization=self.org,
            amount=500_000,
            payment_date=datetime.date.today(),
            due_date=due,
            payment_type=Payment.PaymentType.CASH,
            status=Payment.Status.PENDING,
        )
        self.assertEqual(payment.due_date, due)

    def test_payment_with_for_month(self):
        """Payment can specify which calendar month it covers."""
        for_month = datetime.date(2026, 9, 1)
        payment = Payment.objects.create(
            student=self.student,
            organization=self.org,
            amount=500_000,
            payment_date=datetime.date.today(),
            for_month=for_month,
            payment_type=Payment.PaymentType.CASH,
            status=Payment.Status.PAID,
        )
        self.assertEqual(payment.for_month, for_month)

    def test_payment_received_by_staff(self):
        """Payment can record which staff member registered it."""
        payment = Payment.objects.create(
            student=self.student,
            organization=self.org,
            amount=500_000,
            payment_date=datetime.date.today(),
            payment_type=Payment.PaymentType.CASH,
            status=Payment.Status.PAID,
            received_by=self.admin_user,
        )
        self.assertEqual(payment.received_by, self.admin_user)

    def test_payment_has_overdue_status(self):
        """Payment now supports OVERDUE as a status choice."""
        payment = Payment.objects.create(
            student=self.student,
            organization=self.org,
            amount=500_000,
            payment_date=datetime.date.today(),
            payment_type=Payment.PaymentType.CASH,
            status=Payment.Status.OVERDUE,
        )
        self.assertEqual(payment.status, Payment.Status.OVERDUE)


# ---------------------------------------------------------------------------
# 3. Group.name Uniqueness Tests (per-org constraint)
# ---------------------------------------------------------------------------

class GroupNameUniqueConstraintTest(TestCase):
    """
    Tests that Group.name uniqueness is now scoped per-organization.
    Two orgs CAN share a group name. One org CANNOT have two groups with the same name.
    """

    def setUp(self):
        self.org1 = make_org("Erasmus Center")
        self.org2 = make_org("Big Ben Academy")

        # Set global admin context so TenantManager doesn't filter
        set_current_tenant(organization_id=None, is_global=True)

        self.course1 = make_course(self.org1)
        self.course2 = make_course(self.org2)

    def tearDown(self):
        clear_current_tenant()

    def test_same_name_allowed_in_different_orgs(self):
        """
        Two organizations CAN both have a group named 'Group A'.
        This verifies the fix for the global unique=True bug.
        """
        group1 = Group.objects.create(
            organization=self.org1,
            course=self.course1,
            name="Group A",
            start_date=datetime.date.today(),
        )
        # Must NOT raise — this is the core bug we fixed
        group2 = Group.objects.create(
            organization=self.org2,
            course=self.course2,
            name="Group A",
            start_date=datetime.date.today(),
        )
        self.assertNotEqual(group1.pk, group2.pk)
        self.assertEqual(Group.objects.filter(name="Group A").count(), 2)

    def test_same_name_forbidden_within_same_org(self):
        """A single organization CANNOT have two groups with the same name."""
        Group.objects.create(
            organization=self.org1,
            course=self.course1,
            name="Group A",
            start_date=datetime.date.today(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Group.objects.create(
                    organization=self.org1,
                    course=self.course1,
                    name="Group A",
                    start_date=datetime.date.today(),
                )

    def test_different_names_in_same_org_allowed(self):
        """Different names in the same org are of course still fine."""
        Group.objects.create(
            organization=self.org1,
            course=self.course1,
            name="Group A",
            start_date=datetime.date.today(),
        )
        Group.objects.create(
            organization=self.org1,
            course=self.course1,
            name="Group B",
            start_date=datetime.date.today(),
        )
        self.assertEqual(Group.objects.filter(organization=self.org1).count(), 2)


# ---------------------------------------------------------------------------
# 4. TeacherProfile / StaffProfile Tenant Scoping Tests
# ---------------------------------------------------------------------------

class ProfileTenantScopingTest(TestCase):
    """Tests that TeacherProfile and StaffProfile are now org-scoped."""

    def setUp(self):
        self.org1 = make_org("Org One")
        self.org2 = make_org("Org Two")

    def test_teacher_profile_has_organization_field(self):
        """TeacherProfile should now have an organization FK."""
        field_names = [f.name for f in TeacherProfile._meta.get_fields()]
        self.assertIn('organization', field_names,
                      "TeacherProfile must have an organization FK from TenantBaseModel")

    def test_staff_profile_has_organization_field(self):
        """StaffProfile should now have an organization FK."""
        field_names = [f.name for f in StaffProfile._meta.get_fields()]
        self.assertIn('organization', field_names,
                      "StaffProfile must have an organization FK from TenantBaseModel")

    def test_teacher_profile_tenant_manager_scopes_by_org(self):
        """TenantManager on TeacherProfile must return only the current org's teachers."""
        # Create teachers in two different orgs
        user1 = make_user("+998903333333", self.org1, User.Status.TEACHER)
        user2 = make_user("+998904444444", self.org2, User.Status.TEACHER)
        TeacherProfile.objects.create(user=user1, organization=self.org1, subject="Math")
        TeacherProfile.objects.create(user=user2, organization=self.org2, subject="English")

        # Simulate a request from org1 context
        set_current_tenant(organization_id=self.org1.id)
        try:
            qs = TeacherProfile.objects.all()
            org_ids = list(qs.values_list('organization_id', flat=True))
            self.assertTrue(
                all(str(oid) == str(self.org1.id) for oid in org_ids),
                "TenantManager must only return org1's teachers when org1 context is set"
            )
        finally:
            clear_current_tenant()

    def test_staff_profile_tenant_manager_scopes_by_org(self):
        """TenantManager on StaffProfile must return only the current org's staff."""
        user1 = make_user("+998905555555", self.org1, User.Status.MANAGER)
        user2 = make_user("+998906666666", self.org2, User.Status.ADMIN)
        StaffProfile.objects.create(user=user1, organization=self.org1)
        StaffProfile.objects.create(user=user2, organization=self.org2)

        set_current_tenant(organization_id=self.org2.id)
        try:
            qs = StaffProfile.objects.all()
            org_ids = list(qs.values_list('organization_id', flat=True))
            self.assertTrue(
                all(str(oid) == str(self.org2.id) for oid in org_ids),
                "TenantManager must only return org2's staff when org2 context is set"
            )
        finally:
            clear_current_tenant()

    def test_teacher_all_objects_returns_all_orgs(self):
        """all_objects manager on TeacherProfile bypasses tenant scoping."""
        user1 = make_user("+998907777777", self.org1, User.Status.TEACHER)
        user2 = make_user("+998908888888", self.org2, User.Status.TEACHER)
        TeacherProfile.objects.create(user=user1, organization=self.org1, subject="Math")
        TeacherProfile.objects.create(user=user2, organization=self.org2, subject="English")

        set_current_tenant(organization_id=self.org1.id)
        try:
            self.assertEqual(TeacherProfile.all_objects.count(), 2,
                             "all_objects must return teachers from all orgs")
        finally:
            clear_current_tenant()


# ---------------------------------------------------------------------------
# 5. Integration Test — Full Lesson → Attendance chain
# ---------------------------------------------------------------------------

class LessonAttendanceChainTest(TestCase):
    """Integration test: verifies the full GroupSchedule→Lesson→Attendance flow."""

    def setUp(self):
        self.org = make_org("Integration Org")
        set_current_tenant(organization_id=self.org.id)

        teacher_user = make_user("+998909999999", self.org, User.Status.TEACHER)
        self.teacher = TeacherProfile.objects.create(
            user=teacher_user, organization=self.org, subject="Science"
        )
        self.course = make_course(self.org)
        self.group = make_group(self.org, self.course, teacher=self.teacher)

        self.student1 = make_student(self.org)
        self.student2 = make_student(self.org)

        # Enroll both students
        Enrollment.objects.create(
            student=self.student1, group=self.group, status=Enrollment.Status.ACTIVE
        )
        Enrollment.objects.create(
            student=self.student2, group=self.group, status=Enrollment.Status.ACTIVE
        )

        # Create a completed lesson
        self.lesson = Lesson.objects.create(
            group=self.group,
            date=datetime.date(2026, 8, 11),
            status=Lesson.Status.COMPLETED,
        )

    def tearDown(self):
        clear_current_tenant()

    def test_attendance_chain_integrity(self):
        """Creating attendance per student per lesson works correctly."""
        a1 = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student1,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        a2 = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student2,
            status=Attendance.Status.ABSENT,
            organization=self.org,
        )

        # Both records link back to the same lesson
        self.assertEqual(a1.lesson, self.lesson)
        self.assertEqual(a2.lesson, self.lesson)

        # Date and group derive correctly
        self.assertEqual(a1.date, datetime.date(2026, 8, 11))
        self.assertEqual(a1.group, self.group)
        self.assertEqual(a2.group, self.group)

        # Lesson has two attendance records
        self.assertEqual(self.lesson.attendances.count(), 2)

        # Query absent students for this lesson
        absent = Attendance.objects.filter(
            lesson=self.lesson, status=Attendance.Status.ABSENT
        )
        self.assertEqual(absent.count(), 1)
        self.assertEqual(absent.first().student, self.student2)

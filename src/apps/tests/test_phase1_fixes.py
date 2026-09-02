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
from django.test import TestCase

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


def make_student(org, phone_suffix="0000"):
    phone = f"+9989{phone_suffix[:8]:>08}"
    # Ensure unique phone
    counter = User.objects.filter(phone__startswith="+998").count()
    phone = f"+998{counter + 900000000:09d}"
    user = make_user(phone=phone, org=org, role=User.Status.STUDENT)
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
        """Attendance must be created with a lesson FK."""
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        self.assertIsNotNone(attendance.pk)
        self.assertEqual(attendance.lesson, self.lesson)

    def test_attendance_date_property_derives_from_lesson(self):
        """attendance.date returns the lesson's date — not a stored DB column."""
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            status=Attendance.Status.PRESENT,
            organization=self.org,
        )
        self.assertEqual(attendance.date, datetime.date(2026, 8, 11))

    def test_attendance_group_property_derives_from_lesson(self):
        """attendance.group returns the lesson's group — not a stored DB column."""
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

    def test_attendance_has_no_raw_date_db_column(self):
        """The `date` column must NOT exist as a DB field on Attendance."""
        concrete_field_names = [
            f.name for f in Attendance._meta.get_fields()
            if hasattr(f, 'column')
        ]
        self.assertNotIn('date', concrete_field_names,
                         "Attendance.date should be a @property, not a DB column")

    def test_attendance_has_no_raw_group_db_column(self):
        """The `group` column must NOT exist as a DB field on Attendance."""
        concrete_field_names = [
            f.name for f in Attendance._meta.get_fields()
            if hasattr(f, 'column')
        ]
        self.assertNotIn('group', concrete_field_names,
                         "Attendance.group should be a @property, not a DB column")


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

    def test_payment_with_manual_backdate(self):
        """payment_date is a manual DateField — staff can backdate payments."""
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
        """Payment linked to an enrollment knows its group/course."""
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
        """Payment carries a due_date for upcoming-payment tracking."""
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
        """Payment specifies which calendar month it covers."""
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
        """Payment records which staff member registered it."""
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

    def test_payment_overdue_status(self):
        """Payment now supports the OVERDUE status choice."""
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
    Tests that Group.name uniqueness is now per-organization.
    Two orgs CAN share a group name. One org CANNOT have duplicates.
    """

    def setUp(self):
        self.org1 = make_org("Erasmus Center")
        self.org2 = make_org("Big Ben Academy")
        # Global admin context so TenantManager doesn't filter
        set_current_tenant(organization_id=None, is_global=True)
        self.course1 = make_course(self.org1)
        self.course2 = make_course(self.org2)

    def tearDown(self):
        clear_current_tenant()

    def test_same_name_allowed_across_different_orgs(self):
        """
        Two organizations CAN both have 'Group A'.
        This is the core bug that was fixed — previously this raised IntegrityError.
        """
        Group.objects.create(
            organization=self.org1, course=self.course1,
            name="Group A", start_date=datetime.date.today(),
        )
        # Must NOT raise
        Group.objects.create(
            organization=self.org2, course=self.course2,
            name="Group A", start_date=datetime.date.today(),
        )
        self.assertEqual(Group.objects.filter(name="Group A").count(), 2)

    def test_duplicate_name_within_same_org_is_rejected(self):
        """One organization CANNOT have two groups with the same name."""
        Group.objects.create(
            organization=self.org1, course=self.course1,
            name="Group A", start_date=datetime.date.today(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Group.objects.create(
                    organization=self.org1, course=self.course1,
                    name="Group A", start_date=datetime.date.today(),
                )

    def test_different_names_within_same_org_are_allowed(self):
        """Different names in the same org are always fine."""
        Group.objects.create(
            organization=self.org1, course=self.course1,
            name="Group A", start_date=datetime.date.today(),
        )
        Group.objects.create(
            organization=self.org1, course=self.course1,
            name="Group B", start_date=datetime.date.today(),
        )
        self.assertEqual(Group.all_objects.filter(organization=self.org1).count(), 2)


# ---------------------------------------------------------------------------
# 4. TeacherProfile / StaffProfile Tenant Scoping Tests
# ---------------------------------------------------------------------------

class ProfileTenantScopingTest(TestCase):
    """Tests that TeacherProfile and StaffProfile are now org-scoped."""

    def setUp(self):
        self.org1 = make_org("Org One")
        self.org2 = make_org("Org Two")

    def test_teacher_profile_has_organization_field(self):
        """TeacherProfile must have the organization FK from TenantBaseModel."""
        field_names = [f.name for f in TeacherProfile._meta.get_fields()]
        self.assertIn('organization', field_names)

    def test_staff_profile_has_organization_field(self):
        """StaffProfile must have the organization FK from TenantBaseModel."""
        field_names = [f.name for f in StaffProfile._meta.get_fields()]
        self.assertIn('organization', field_names)

    def test_teacher_profile_objects_scoped_by_tenant(self):
        """TenantManager on TeacherProfile returns only current org's teachers."""
        user1 = make_user("+998903333333", self.org1, User.Status.TEACHER)
        user2 = make_user("+998904444444", self.org2, User.Status.TEACHER)
        TeacherProfile.objects.create(user=user1, organization=self.org1, subject="Math")
        TeacherProfile.objects.create(user=user2, organization=self.org2, subject="English")

        set_current_tenant(organization_id=self.org1.id)
        try:
            qs = TeacherProfile.objects.all()
            self.assertEqual(qs.count(), 1)
            self.assertEqual(str(qs.first().organization_id), str(self.org1.id))
        finally:
            clear_current_tenant()

    def test_staff_profile_objects_scoped_by_tenant(self):
        """TenantManager on StaffProfile returns only current org's staff."""
        user1 = make_user("+998905555555", self.org1, User.Status.MANAGER)
        user2 = make_user("+998906666666", self.org2, User.Status.ADMIN)
        StaffProfile.objects.create(user=user1, organization=self.org1)
        StaffProfile.objects.create(user=user2, organization=self.org2)

        set_current_tenant(organization_id=self.org2.id)
        try:
            qs = StaffProfile.objects.all()
            self.assertEqual(qs.count(), 1)
            self.assertEqual(str(qs.first().organization_id), str(self.org2.id))
        finally:
            clear_current_tenant()

    def test_teacher_all_objects_bypasses_tenant_scope(self):
        """all_objects manager bypasses tenant scoping — global admin access."""
        user1 = make_user("+998907777777", self.org1, User.Status.TEACHER)
        user2 = make_user("+998908888888", self.org2, User.Status.TEACHER)
        TeacherProfile.objects.create(user=user1, organization=self.org1, subject="Math")
        TeacherProfile.objects.create(user=user2, organization=self.org2, subject="English")

        set_current_tenant(organization_id=self.org1.id)
        try:
            self.assertEqual(TeacherProfile.all_objects.count(), 2)
        finally:
            clear_current_tenant()

    def test_no_cross_org_teacher_leak(self):
        """Org1 admin context must never see org2's teachers via .objects."""
        user1 = make_user("+998910000001", self.org1, User.Status.TEACHER)
        user2 = make_user("+998910000002", self.org2, User.Status.TEACHER)
        t1 = TeacherProfile.objects.create(user=user1, organization=self.org1, subject="Math")
        t2 = TeacherProfile.objects.create(user=user2, organization=self.org2, subject="Science")

        set_current_tenant(organization_id=self.org1.id)
        try:
            ids = list(TeacherProfile.objects.values_list('pk', flat=True))
            self.assertIn(t1.pk, ids)
            self.assertNotIn(t2.pk, ids,
                             "org2's teacher must NOT appear in org1's scoped queryset")
        finally:
            clear_current_tenant()


# ---------------------------------------------------------------------------
# 5. Integration — Full Lesson → Attendance chain
# ---------------------------------------------------------------------------

class LessonAttendanceChainIntegrationTest(TestCase):
    """Verifies the complete GroupSchedule→Lesson→Attendance chain works end-to-end."""

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

        Enrollment.objects.create(
            student=self.student1, group=self.group, status=Enrollment.Status.ACTIVE
        )
        Enrollment.objects.create(
            student=self.student2, group=self.group, status=Enrollment.Status.ACTIVE
        )

        self.lesson = Lesson.objects.create(
            group=self.group,
            date=datetime.date(2026, 8, 11),
            status=Lesson.Status.COMPLETED,
        )

    def tearDown(self):
        clear_current_tenant()

    def test_full_chain_integrity(self):
        """Attendance links correctly to lesson, derives date/group, and is queryable."""
        a1 = Attendance.objects.create(
            lesson=self.lesson, student=self.student1,
            status=Attendance.Status.PRESENT, organization=self.org,
        )
        a2 = Attendance.objects.create(
            lesson=self.lesson, student=self.student2,
            status=Attendance.Status.ABSENT, organization=self.org,
        )

        # FK integrity
        self.assertEqual(a1.lesson, self.lesson)
        self.assertEqual(a2.lesson, self.lesson)

        # Derived properties
        self.assertEqual(a1.date, datetime.date(2026, 8, 11))
        self.assertEqual(a1.group, self.group)
        self.assertEqual(a2.group, self.group)

        # Reverse relation
        self.assertEqual(self.lesson.attendances.count(), 2)

        # Business query: who was absent?
        absent_qs = Attendance.objects.filter(
            lesson=self.lesson, status=Attendance.Status.ABSENT
        )
        self.assertEqual(absent_qs.count(), 1)
        self.assertEqual(absent_qs.first().student, self.student2)

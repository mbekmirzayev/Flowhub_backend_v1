"""
Lesson Lifecycle Service
========================
Handles the two critical lesson state transitions:

  PLANNED → COMPLETED : Class was taught. Auto-creates Attendance records
                        for every actively enrolled student (default: ABSENT).
                        Teacher then bulk-marks present/excused via the bulk API.

  PLANNED → CANCELLED : Class was skipped. Writes reason + History entry.
                        No attendance records are created.
"""
from django.db import transaction

from apps.attendance.models import Attendance
from apps.course.models.lesson import Lesson
from apps.enrollment.models import Enrollment
from apps.history.services.writer import log_lesson_completed, log_lesson_cancelled
from apps.users.models import StudentProfile


def complete_lesson(
    *,
    lesson: Lesson,
    performed_by,
    organization,
    teacher_profile=None,
) -> tuple[Lesson, list[Attendance]]:
    """
    Mark a lesson as COMPLETED and auto-create Attendance records.

    Auto-attendance strategy:
        - One record per ACTIVE enrolled student
        - Default status = ABSENT
        - Staff/Teacher then calls the bulk API to flip students to PRESENT/EXCUSED

    Args:
        lesson:          The Lesson instance to complete.
        performed_by:    The User performing this action.
        organization:    The tenant Organization.
        teacher_profile: Optional TeacherProfile override (substitute teacher).

    Returns:
        (updated_lesson, list_of_created_attendance_records)

    Raises:
        ValueError: If lesson is already COMPLETED or CANCELLED.
    """
    if lesson.status != Lesson.Status.PLANNED:
        raise ValueError(
            f"Cannot complete lesson with status '{lesson.status}'. "
            "Only PLANNED lessons can be marked as completed."
        )

    with transaction.atomic():
        # 1. Update lesson state
        lesson.status = Lesson.Status.COMPLETED
        if teacher_profile:
            lesson.teacher = teacher_profile
        lesson.save(update_fields=['status', 'teacher'])

        # 2. Get all active students enrolled in this group
        active_enrollments = Enrollment.all_objects.filter(
            group=lesson.group,
            status=Enrollment.Status.ACTIVE,
        ).select_related('student')

        # 3. Bulk-create attendance records (default: ABSENT)
        # Skip students who already have an attendance for this lesson
        existing_student_ids = set(
            Attendance.objects.filter(lesson=lesson).values_list('student_id', flat=True)
        )

        attendance_records = []
        for enrollment in active_enrollments:
            student = enrollment.student
            # Skip frozen students — they don't receive attendance records
            if student.status == StudentProfile.StudentStatus.FROZEN:
                continue
            if student.pk in existing_student_ids:
                continue
            attendance_records.append(
                Attendance(
                    lesson=lesson,
                    student=student,
                    status=Attendance.Status.ABSENT,
                    organization=organization,
                    marked_by=performed_by,
                )
            )

        created_attendances = Attendance.objects.bulk_create(attendance_records)

        # 4. Write History
        log_lesson_completed(
            performed_by=performed_by,
            group=lesson.group,
            lesson=lesson,
            organization=organization,
        )

    return lesson, created_attendances


def cancel_lesson(
    *,
    lesson: Lesson,
    reason: str,
    performed_by,
    organization,
) -> Lesson:
    """
    Mark a lesson as CANCELLED.

    No attendance records are created. If the lesson already had attendance
    records from a previous completion, they remain intact (this shouldn't
    happen in practice but is a safe guard).

    Args:
        lesson:       The Lesson instance to cancel.
        reason:       Required explanation (holiday, illness, etc.).
        performed_by: The User performing this action.
        organization: The tenant Organization.

    Raises:
        ValueError: If the lesson is already CANCELLED or COMPLETED.
        ValueError: If reason is empty.
    """
    if not reason or not reason.strip():
        raise ValueError("A reason is required when cancelling a lesson.")

    if lesson.status == Lesson.Status.CANCELLED:
        raise ValueError("This lesson is already cancelled.")

    if lesson.status == Lesson.Status.COMPLETED:
        raise ValueError(
            "Cannot cancel a lesson that is already COMPLETED. "
            "Contact a system administrator if this was an error."
        )

    with transaction.atomic():
        lesson.status = Lesson.Status.CANCELLED
        lesson.reason = reason.strip()
        lesson.save(update_fields=['status', 'reason'])

        log_lesson_cancelled(
            performed_by=performed_by,
            group=lesson.group,
            lesson=lesson,
            reason=reason,
            organization=organization,
        )

    return lesson

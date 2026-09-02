"""
Enrollment Services
===================
All student lifecycle workflows that mutate Enrollment and StudentProfile state.
Each function is atomic and writes to History on success.

Functions:
    enroll_student         — create a new active enrollment
    transfer_student       — move student from one group to another
    graduate_student       — mark student as finished / graduated
    dropout_student        — mark student as dropped out (permanent)
    leave_student          — voluntarily leave a single group (status stays ACTIVE)
    freeze_student         — temporarily freeze a student's enrollment
    unfreeze_student       — restore a frozen student to active
"""
import datetime

from django.db import transaction
from django.utils import timezone

from apps.enrollment.models import Enrollment
from apps.history.services.writer import (
    log_student_joined,
    log_student_left,
    log_student_transferred,
    log_student_graduated,
    log_student_dropped,
    log_student_frozen,
    log_student_unfrozen,
)
from apps.users.models import StudentProfile


# ---------------------------------------------------------------------------
# Enroll
# ---------------------------------------------------------------------------

def enroll_student(
    *,
    student: StudentProfile,
    group,
    performed_by,
    organization,
) -> Enrollment:
    """
    Create a new ACTIVE enrollment for a student in a group.

    Raises:
        ValueError: If the student is already actively enrolled in that group.
    """
    if Enrollment.all_objects.filter(
        student=student, group=group, status=Enrollment.Status.ACTIVE
    ).exists():
        raise ValueError(
            f"{student} is already actively enrolled in group '{group.name}'."
        )

    with transaction.atomic():
        enrollment = Enrollment.objects.create(
            student=student,
            group=group,
            status=Enrollment.Status.ACTIVE,
        )
        log_student_joined(
            performed_by=performed_by,
            student=student,
            group=group,
            organization=organization,
        )

    return enrollment


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------

def transfer_student(
    *,
    enrollment: Enrollment,
    to_group,
    performed_by,
    organization,
    reason: str = "",
) -> Enrollment:
    """
    Atomically move a student from their current group to `to_group`.

    Steps:
        1. Close the current enrollment (status=DROPPED, left_at=today)
        2. Create a new ACTIVE enrollment in the target group
        3. Write STUDENT_TRANSFERRED to History

    Raises:
        ValueError: If the student is already in the target group.
    """
    from_group = enrollment.group
    student = enrollment.student

    if str(from_group.pk) == str(to_group.pk):
        raise ValueError("Cannot transfer a student to the same group they are already in.")

    if Enrollment.all_objects.filter(
        student=student, group=to_group, status=Enrollment.Status.ACTIVE
    ).exists():
        raise ValueError(
            f"{student} is already actively enrolled in '{to_group.name}'."
        )

    with transaction.atomic():
        # Close current enrollment
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.left_at = datetime.date.today()
        enrollment.save(update_fields=['status', 'left_at'])

        # Create new enrollment
        new_enrollment = Enrollment.objects.create(
            student=student,
            group=to_group,
            status=Enrollment.Status.ACTIVE,
        )

        log_student_transferred(
            performed_by=performed_by,
            student=student,
            from_group=from_group,
            to_group=to_group,
            organization=organization,
            reason=reason,
        )

    return new_enrollment


# ---------------------------------------------------------------------------
# Graduate
# ---------------------------------------------------------------------------

def graduate_student(
    *,
    enrollment: Enrollment,
    performed_by,
    organization,
) -> Enrollment:
    """
    Mark a student as graduated: close the enrollment and update StudentProfile.status.
    """
    student = enrollment.student
    group = enrollment.group

    with transaction.atomic():
        enrollment.status = Enrollment.Status.FINISHED
        enrollment.left_at = datetime.date.today()
        enrollment.save(update_fields=['status', 'left_at'])

        student.status = StudentProfile.StudentStatus.GRADUATED
        student.save(update_fields=['status'])

        log_student_graduated(
            performed_by=performed_by,
            student=student,
            group=group,
            organization=organization,
        )

    return enrollment


# ---------------------------------------------------------------------------
# Dropout
# ---------------------------------------------------------------------------

def dropout_student(
    *,
    enrollment: Enrollment,
    performed_by,
    organization,
    reason: str = "",
) -> Enrollment:
    """
    Mark a student as dropped out: close the enrollment and update StudentProfile.status.
    """
    student = enrollment.student
    group = enrollment.group

    with transaction.atomic():
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.left_at = datetime.date.today()
        enrollment.save(update_fields=['status', 'left_at'])

        student.status = StudentProfile.StudentStatus.DROPPED
        student.save(update_fields=['status'])

        log_student_dropped(
            performed_by=performed_by,
            student=student,
            group=group,
            organization=organization,
            reason=reason,
        )

    return enrollment


# ---------------------------------------------------------------------------
# Leave  (voluntarily quit a single group — StudentProfile stays ACTIVE)
# ---------------------------------------------------------------------------

def leave_student(
    *,
    enrollment: Enrollment,
    performed_by,
    organization,
    reason: str = "",
) -> Enrollment:
    """
    Close an enrollment because the student voluntarily left the group.

    **Difference from `dropout_student`:**
    - `dropout_student` is permanent: it also sets `StudentProfile.status = DROPPED`,
      indicating the student has left the programme entirely.
    - `leave_student` is group-scoped: only the enrollment is closed. The student
      profile status is NOT changed, because the student may still be in other
      active groups or may re-enroll later.

    Steps:
        1. Guard: enrollment must be ACTIVE.
        2. Mark enrollment as DROPPED with left_at = today.
        3. Write STUDENT_LEFT to History.

    Raises:
        ValueError: If the enrollment is not currently ACTIVE.
    """
    if enrollment.status != Enrollment.Status.ACTIVE:
        raise ValueError(
            f"Cannot leave: enrollment is already '{enrollment.status}', not ACTIVE."
        )

    student = enrollment.student
    group = enrollment.group

    with transaction.atomic():
        enrollment.status = Enrollment.Status.DROPPED
        enrollment.left_at = datetime.date.today()
        enrollment.save(update_fields=['status', 'left_at'])

        log_student_left(
            performed_by=performed_by,
            student=student,
            group=group,
            organization=organization,
            reason=reason,
        )

    return enrollment


# ---------------------------------------------------------------------------
# Freeze / Unfreeze
# ---------------------------------------------------------------------------


def freeze_student(
    *,
    student: StudentProfile,
    performed_by,
    organization,
    reason: str = "",
) -> StudentProfile:
    """
    Freeze a student's account. The enrollment(s) remain active but the student
    is marked as FROZEN — they will not receive attendance records while frozen.
    """
    if student.status == StudentProfile.StudentStatus.FROZEN:
        raise ValueError(f"{student} is already frozen.")

    with transaction.atomic():
        student.status = StudentProfile.StudentStatus.FROZEN
        student.save(update_fields=['status'])

        log_student_frozen(
            performed_by=performed_by,
            student=student,
            organization=organization,
            reason=reason,
        )

    return student


def unfreeze_student(
    *,
    student: StudentProfile,
    performed_by,
    organization,
) -> StudentProfile:
    """Restore a frozen student to ACTIVE status."""
    if student.status != StudentProfile.StudentStatus.FROZEN:
        raise ValueError(f"{student} is not currently frozen.")

    with transaction.atomic():
        student.status = StudentProfile.StudentStatus.ACTIVE
        student.save(update_fields=['status'])

        log_student_unfrozen(
            performed_by=performed_by,
            student=student,
            organization=organization,
        )

    return student

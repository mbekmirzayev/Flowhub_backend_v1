"""
History Writer Service
======================
Centralized functions for writing History records.

All domain services (enrollment, lesson, payment) call these functions
rather than creating History objects directly. This keeps the History
model decoupled from business logic and ensures every event is written
consistently with the correct fields.

Usage:
    from apps.history.services.writer import log_student_joined
    log_student_joined(performed_by=request.user, student=student, group=group, org=org)
"""
from apps.history.models import History


def _write(
    *,
    action: str,
    organization,
    performed_by=None,
    student=None,
    group=None,
    description: str = "",
    meta: dict = None,
) -> History:
    """Internal base writer — all public functions delegate here."""
    return History.objects.create(
        action=action,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=group,
        description=description,
        meta=meta or {},
    )


# ---------------------------------------------------------------------------
# Student lifecycle
# ---------------------------------------------------------------------------

def log_student_joined(*, performed_by, student, group, organization, description=""):
    return _write(
        action=History.Action.STUDENT_JOINED,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=group,
        description=description or f"{student} enrolled in {group}",
    )


def log_student_left(*, performed_by, student, group, organization, reason=""):
    return _write(
        action=History.Action.STUDENT_LEFT,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=group,
        description=reason or f"{student} left {group}",
    )


def log_student_transferred(
    *, performed_by, student, from_group, to_group, organization, reason=""
):
    return _write(
        action=History.Action.STUDENT_TRANSFERRED,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=to_group,
        description=reason or f"{student} transferred from {from_group} to {to_group}",
        meta={
            "from_group_id": str(from_group.pk),
            "from_group_name": from_group.name,
            "to_group_id": str(to_group.pk),
            "to_group_name": to_group.name,
        },
    )


def log_student_graduated(*, performed_by, student, group, organization):
    return _write(
        action=History.Action.STUDENT_GRADUATED,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=group,
        description=f"{student} graduated from {group}",
    )


def log_student_dropped(*, performed_by, student, group, organization, reason=""):
    return _write(
        action=History.Action.STUDENT_DROPPED,
        organization=organization,
        performed_by=performed_by,
        student=student,
        group=group,
        description=reason or f"{student} dropped out of {group}",
    )


def log_student_frozen(*, performed_by, student, organization, reason=""):
    return _write(
        action=History.Action.STUDENT_FROZEN,
        organization=organization,
        performed_by=performed_by,
        student=student,
        description=reason or f"{student} account frozen",
    )


def log_student_unfrozen(*, performed_by, student, organization):
    return _write(
        action=History.Action.STUDENT_UNFROZEN,
        organization=organization,
        performed_by=performed_by,
        student=student,
        description=f"{student} account unfrozen",
    )


# ---------------------------------------------------------------------------
# Lesson lifecycle
# ---------------------------------------------------------------------------

def log_lesson_completed(*, performed_by, group, lesson, organization):
    return _write(
        action=History.Action.LESSON_COMPLETED,
        organization=organization,
        performed_by=performed_by,
        group=group,
        description=f"Lesson on {lesson.date} completed for {group}",
        meta={"lesson_id": str(lesson.pk), "lesson_date": str(lesson.date)},
    )


def log_lesson_cancelled(*, performed_by, group, lesson, reason, organization):
    return _write(
        action=History.Action.LESSON_CANCELLED,
        organization=organization,
        performed_by=performed_by,
        group=group,
        description=f"Lesson on {lesson.date} cancelled: {reason}",
        meta={
            "lesson_id": str(lesson.pk),
            "lesson_date": str(lesson.date),
            "reason": reason,
        },
    )


# ---------------------------------------------------------------------------
# Teacher / group
# ---------------------------------------------------------------------------

def log_teacher_changed(*, performed_by, group, old_teacher, new_teacher, organization):
    return _write(
        action=History.Action.TEACHER_CHANGED,
        organization=organization,
        performed_by=performed_by,
        group=group,
        description=f"Teacher changed on {group}: {old_teacher} → {new_teacher}",
        meta={
            "old_teacher_id": str(old_teacher.pk) if old_teacher else None,
            "new_teacher_id": str(new_teacher.pk) if new_teacher else None,
        },
    )


# ---------------------------------------------------------------------------
# Financial
# ---------------------------------------------------------------------------

def log_payment_done(*, performed_by, student, organization, payment):
    return _write(
        action=History.Action.PAYMENT_DONE,
        organization=organization,
        performed_by=performed_by,
        student=student,
        description=f"Payment of {payment.amount} recorded for {student}",
        meta={
            "payment_id": str(payment.pk),
            "amount": str(payment.amount),
            "payment_type": payment.payment_type,
            "for_month": str(payment.for_month) if payment.for_month else None,
        },
    )

from django.db.models import TextChoices, ForeignKey, SET_NULL, CASCADE, JSONField
from django.db.models.fields import TextField, CharField
from django.utils.translation import gettext_lazy as _

from apps.common.models import CreateBaseModel, TenantBaseModel
from apps.course.models import Group
from apps.users.models import User, StudentProfile


class History(TenantBaseModel, CreateBaseModel):
    """
    Immutable audit log for all significant CRM lifecycle events.

    Rules:
    - Records are NEVER edited or deleted (use soft-delete only).
    - Every domain service (enrollment, attendance, payment, lesson)
      writes to this log via dedicated service functions or Django signals.
    - `meta` is a JSON field for structured extra context per action type,
      e.g. {"from_group": "Group A", "to_group": "Group B"} on STUDENT_TRANSFERRED.
    """

    class Action(TextChoices):
        # --- Student lifecycle ---
        STUDENT_JOINED = "STUDENT_JOINED", _("Student joined group")
        STUDENT_LEFT = "STUDENT_LEFT", _("Student left group")
        STUDENT_TRANSFERRED = "STUDENT_TRANSFERRED", _("Student transferred to another group")
        STUDENT_GRADUATED = "STUDENT_GRADUATED", _("Student graduated")
        STUDENT_DROPPED = "STUDENT_DROPPED", _("Student dropped out")
        STUDENT_FROZEN = "STUDENT_FROZEN", _("Student account frozen")
        STUDENT_UNFROZEN = "STUDENT_UNFROZEN", _("Student account unfrozen")

        # --- Group / course ---
        GROUP_CREATED = "GROUP_CREATED", _("Group created")
        TEACHER_CHANGED = "TEACHER_CHANGED", _("Teacher changed on group")

        # --- Lesson ---
        LESSON_COMPLETED = "LESSON_COMPLETED", _("Lesson marked as completed")
        LESSON_CANCELLED = "LESSON_CANCELLED", _("Lesson cancelled")

        # --- Financial ---
        PAYMENT_DONE = "PAYMENT_DONE", _("Payment recorded")

    performed_by = ForeignKey(
        User,
        on_delete=SET_NULL,
        null=True,
        related_name='actions_performed',
        verbose_name=_('Performed by'),
    )
    student = ForeignKey(
        StudentProfile,
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name='student_history',
        verbose_name=_('Student'),
    )
    group = ForeignKey(
        Group,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name='group_history',
        verbose_name=_('Group'),
    )
    action = CharField(
        max_length=255,
        choices=Action.choices,
        verbose_name=_('Action'),
        db_index=True,
    )
    description = TextField(
        null=True,
        blank=True,
        verbose_name=_('Description'),
    )
    meta = JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Meta'),
        help_text=_('Structured extra context for this action (e.g. transfer details).'),
    )

    class Meta:
        db_table = 'history'
        ordering = ['-created_at']
        verbose_name = _('History entry')
        verbose_name_plural = _('History entries')
        indexes = [
            __import__('django.db.models', fromlist=['Index']).Index(
                fields=['student', '-created_at'], name='history_student_created_idx'
            ),
        ]

    def __str__(self):
        return f"{self.action} by {self.performed_by} @ {self.created_at}"
from django.db.models import TextChoices, ForeignKey, CASCADE, SET_NULL, Manager
from django.db.models.fields import DateField, CharField
from django.utils.translation import gettext_lazy as _

from apps.common.managers.Linked_tenant_manager import LinkedTenantManager
from apps.common.models import UUIDBaseModel
from apps.course.models.group import Group


class Lesson(UUIDBaseModel):
    class Status(TextChoices):
        PLANNED = 'planned', _('Planned')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    group = ForeignKey(Group, CASCADE, related_name='lessons')
    teacher = ForeignKey(
        'users.TeacherProfile',
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name=_('Teacher'),
        help_text=_('Who taught this lesson. Defaults to the group teacher.'),
    )
    date = DateField(verbose_name=_('Date'))
    status = CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
        verbose_name=_('Status'),
    )
    reason = CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_('Reason'),
        help_text=_('Required when status is CANCELLED.'),
    )

    class Meta:
        ordering = ['date']
        verbose_name = _('Lesson')
        verbose_name_plural = _('Lessons')
        constraints = [
            # A group can only have one lesson per date
            __import__('django.db.models', fromlist=['UniqueConstraint']).UniqueConstraint(
                fields=['group', 'date'],
                name='unique_lesson_per_group_per_date',
            )
        ]

    objects = LinkedTenantManager(lookup_path='group__organization_id')
    all_objects = Manager()

    def __str__(self):
        return f"{self.group.name} — {self.date} [{self.status}]"

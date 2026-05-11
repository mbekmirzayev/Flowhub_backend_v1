from django.db.models import TextChoices, ForeignKey, CASCADE
from django.db.models.fields import DateField, CharField
from django.utils.translation import gettext_lazy as _

from apps.common.models import UUIDBaseModel
from apps.course.models.group import Group


class Lesson(UUIDBaseModel):
    class Status(TextChoices):
        PLANNED = 'planned', _('Rejalashtirilgan')
        COMPLETED = 'completed', _('O‘tildi')
        CANCELLED = 'cancelled', _('Qoldirildi (Bayram/Kasallik)')

    group = ForeignKey(Group, CASCADE, related_name='lessons')
    date = DateField()
    status = CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    reason = CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['date', 'status']

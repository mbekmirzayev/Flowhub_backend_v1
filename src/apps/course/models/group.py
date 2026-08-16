from django.db.models import TextChoices, ForeignKey, CASCADE, SET_NULL, UniqueConstraint
from django.db.models.fields import CharField, DateField
from django.utils.translation import gettext_lazy as _

from apps.common.models import CreateBaseModel, TenantBaseModel
from apps.course.models.course import Course
from apps.users.models import TeacherProfile


class Group(TenantBaseModel, CreateBaseModel):
    class Status(TextChoices):
        ACTIVE = 'active', _('Active')
        CLOSED = 'closed', _('Closed')

    course = ForeignKey(Course, CASCADE, related_name='groups')
    teacher = ForeignKey(TeacherProfile, SET_NULL, null=True, blank=True, related_name='groups')
    name = CharField(max_length=55)  # unique=True removed — constraint below handles this
    status = CharField(max_length=55, choices=Status.choices, default=Status.ACTIVE)
    start_date = DateField(verbose_name=_("Group start date"))

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        constraints = [
            UniqueConstraint(
                fields=['organization', 'name'],
                name='unique_group_name_per_org',
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.course})"

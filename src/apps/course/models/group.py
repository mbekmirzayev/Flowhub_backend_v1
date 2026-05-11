from django.db.models import TextChoices, ForeignKey, CASCADE, SET_NULL
from django.db.models.fields import CharField, DateField
from django.utils.translation import gettext_lazy as _
from apps.common.models import CreateBaseModel
from apps.course.models.course import Course
from apps.organization.models.organization import Organization
from apps.users.models import TeacherProfile


class Group(CreateBaseModel):
    class Status(TextChoices):
        ACTIVE = 'active', _('Active')
        CLOSED = 'closed', _('Closed')

    organization = ForeignKey(Organization, CASCADE, related_name='groups')
    course = ForeignKey(Course, CASCADE, related_name='groups')
    teacher = ForeignKey(TeacherProfile, SET_NULL, null=True, blank=True, related_name='groups')
    name = CharField(max_length=55)
    status = CharField(max_length=55, choices=Status.choices, default=Status.ACTIVE)
    start_date = DateField(verbose_name=_("Guruh boshlanish sanasi"))


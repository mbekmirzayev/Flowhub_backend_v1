from django.contrib.postgres.fields import ArrayField
from django.db.models import TextChoices, CASCADE, ForeignKey
from django.db.models.fields import CharField, TimeField
from django.utils.translation import gettext_lazy as _
from apps.common.models import UUIDBaseModel
from apps.course.models.group import Group


class GroupSchedule(UUIDBaseModel):
    class DAYS(TextChoices):
        MONDAY = 'mon', _('Monday')
        TUESDAY = 'tue', _('Tuesday')
        WEDNESDAY = 'wed', _('Wednesday')
        THURSDAY = 'thu', _('Thursday')
        FRIDAY = 'fri', _('Friday')
        SATURDAY = 'sat', _('Saturday')
        SUNDAY = 'sun', _('Sunday')

    group = ForeignKey(Group, CASCADE, related_name='schedule')
    selected_days = ArrayField(CharField(max_length=10, choices=DAYS.choices), size=7, verbose_name=_("Dars kunlari"))
    start_time = TimeField()
    end_time = TimeField()

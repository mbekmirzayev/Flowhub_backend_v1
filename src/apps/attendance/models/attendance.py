from django.db import models
from django.db.models import ForeignKey, SET_NULL
from django.db.models.fields import DateField, BooleanField

from apps.common.models import CreateBaseModel
from apps.enrollment.models import Enrollment


class Attendance(CreateBaseModel):
    enrollment = ForeignKey(Enrollment, SET_NULL, null=True, blank=True, related_name='attendances')
    date = DateField()
    present = BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enrollment', 'date'], name='unique_attendance')
        ]

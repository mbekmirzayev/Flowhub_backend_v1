from django.db.models import TextChoices, CASCADE, ForeignKey, UniqueConstraint, Q
from django.db.models.fields import CharField, DateField

from apps.common.models import CreateBaseModel
from apps.course.models import Group
from apps.users.models import StudentProfile


class Enrollment(CreateBaseModel):
    class Status(TextChoices):
        ACTIVE = 'active', 'Active'
        DROPPED = 'dropped', 'Dropped'
        FINISHED = 'finished', 'Finished'

    student = ForeignKey(StudentProfile, CASCADE, related_name='enrollments')
    group = ForeignKey(Group, CASCADE)
    status = CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    left_at = DateField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['student', 'group'],
                condition=Q(status='active'),
                name='unique_active_enrollment_per_group'
            ),
        ]

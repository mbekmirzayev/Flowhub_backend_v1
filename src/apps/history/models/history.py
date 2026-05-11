from django.db.models import TextChoices, ForeignKey, SET_NULL, CASCADE
from django.db.models.fields import TextField, CharField

from apps.common.models import CreateBaseModel
from apps.course.models import Group
from apps.users.models import User, StudentProfile


class History(CreateBaseModel):
    class Action(TextChoices):
        STUDENT_JOINED = "STUDENT_JOINED", "Student joined group"
        STUDENT_LEFT = "STUDENT_LEFT", "Student left group"
        GROUP_CREATED = "GROUP_CREATED", "Group created"
        PAYMENT_DONE = "PAYMENT_DONE", "Payment done"
        TEACHER_CHANGED = "TEACHER_CHANGED", "Teacher changed"

    performed_by = ForeignKey(User, SET_NULL, null=True, related_name='actions_performed')
    description = TextField(null=True, blank=True)
    student = ForeignKey(StudentProfile, CASCADE, null=True, blank=True, related_name='student_history')
    group = ForeignKey(Group, SET_NULL, null=True, blank=True, related_name='group_history')
    action = CharField(max_length=255, choices=Action.choices)

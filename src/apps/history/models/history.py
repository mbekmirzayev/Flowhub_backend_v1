from django.db.models import TextChoices, ForeignKey, SET_NULL, CASCADE, Manager
from django.db.models.fields import TextField, CharField

from apps.common.managers.Linked_tenant_manager import LinkedTenantManager
from apps.common.models import CreateBaseModel, TenantBaseModel
from apps.course.models import Group
from apps.users.models import User, StudentProfile


class History(TenantBaseModel, CreateBaseModel):
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

    class Meta:
        db_table = 'history'
        ordering = ['-created_at']  

    def __str__(self):
        return f"{self.action} by {self.performed_by}"
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import TextChoices, OneToOneField, CASCADE
from django.db.models.fields import CharField, DecimalField, BooleanField
from django.utils.translation import gettext_lazy as _
from apps.common.models import CreateBaseModel
from apps.users.models.users import User


class TeacherProfile(CreateBaseModel):
    class WorkType(TextChoices):
        FULL_TIME = 'full_time', _('Full_time')
        PART_TIME = 'part_time', _('Part_time')

    class SalaryType(TextChoices):
        FIXED = 'fixed', _('Fixed')
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED_PLUS_PERCENTAGE = 'fixed_percentage', _('fixed + percentage')

    user = OneToOneField(User, CASCADE, related_name='teacher_profile')
    subject = CharField(max_length=255)
    work_type = CharField(max_length=20, choices=WorkType.choices, default=WorkType.FULL_TIME)
    salary_type = CharField(max_length=55, choices=SalaryType.choices, default=SalaryType.FIXED)
    salary = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_deleted = BooleanField(default=False)
    is_active = BooleanField(default=True)

    def clean(self):
        if self.user.role != User.Status.TEACHER:
            raise ValidationError("User role must be TEACHER")

    def soft_delete(self):
        with transaction.atomic():
            self.is_deleted = True
            self.is_active = False
            self.save()
            if not self.user.is_deleted:
                self.user.soft_delete()

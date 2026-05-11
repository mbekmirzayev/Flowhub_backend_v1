from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import TextChoices, CASCADE, OneToOneField
from django.db.models.fields import CharField, BooleanField
from django.utils.translation import gettext_lazy as _

from apps.common.models import CreateBaseModel
from apps.users.models.users import User


class StudentProfile(CreateBaseModel):
    class StudentStatus(TextChoices):
        ACTIVE = 'active', _("Active")
        FROZEN = 'frozen', _('Frozen')
        GRADUATED = 'graduated', _('Graduated')
        DROPPED = 'dropped', _('Dropped')

    user = OneToOneField(User, CASCADE, related_name='student_profile')
    parent_phone = CharField(max_length=20)
    status = CharField(max_length=55, choices=StudentStatus.choices)
    is_deleted = BooleanField(default=False)
    is_active = BooleanField(default=True)

    def clean(self):
        if self.user.role != User.Status.STUDENT:
            raise ValidationError("User role must be STUDENT")

    def soft_delete(self):
        with transaction.atomic():
            self.is_deleted = True
            self.is_active = False
            self.save()
            if not self.user.is_deleted:
                self.user.soft_delete()

    def __str__(self):
        return f"{self.user.get_full_name()}"


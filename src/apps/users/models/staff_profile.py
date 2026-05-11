from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import CASCADE, OneToOneField
from django.db.models.fields import DecimalField, BooleanField

from apps.common.models import CreateBaseModel
from apps.users.models.users import User


class StaffProfile(CreateBaseModel):
    user = OneToOneField(User, CASCADE, related_name='staff_profile')
    salary = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_deleted = BooleanField(default=False)
    is_active = BooleanField(default=True)

    def clean(self):
        if self.user.role not in [
            User.Status.ADMIN,
            User.Status.MANAGER,
            User.Status.GLOBAL_ADMIN
        ]:
            raise ValidationError("User role must be staff type")

    def soft_delete(self):
        with transaction.atomic():
            self.is_deleted = True
            self.is_active = False
            self.save()
            if not self.user.is_deleted:
                self.user.soft_delete()

    def __str__(self):
        return f"{self.user.get_full_name()}"

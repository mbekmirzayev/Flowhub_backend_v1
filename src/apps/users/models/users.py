from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import TextChoices, ForeignKey, CASCADE
from django.db.models.fields import EmailField, CharField, BooleanField
from django.utils.translation import gettext_lazy as _

from apps.common.models.base import UUIDBaseModel, UserManager
from apps.organization.models.organization import Organization


class User(AbstractUser, UUIDBaseModel):
    class Status(TextChoices):
        GLOBAL_ADMIN = 'global_admin', _('Global admin')
        ADMIN = 'admin', _('Admin')
        MANAGER = 'manager', _('Manager')
        TEACHER = 'teacher', _('Teacher')
        STUDENT = 'student', _('Student')

    organization = ForeignKey(Organization, CASCADE, null=True, blank=True, related_name='users')
    email = EmailField(null=True, blank=True, max_length=255, unique=True)
    role = CharField(max_length=20, choices=Status.choices, default=Status.STUDENT)
    phone = CharField(max_length=20, unique=True)
    is_deleted = BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    username = None

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_global_admin(self):
        return self.role == self.Status.GLOBAL_ADMIN and self.is_superuser

    @property
    def is_local_admin(self):
        return self.role == self.Status.ADMIN and self.is_staff

    @property
    def is_manager(self):
        return self.role == self.Status.MANAGER

    @property
    def is_teacher(self):
        return self.role == self.Status.TEACHER

    @property
    def is_student(self):
        return self.role == self.Status.STUDENT

    def soft_delete(self):
        with transaction.atomic():
            if self.is_deleted:
                return
            self.is_deleted = True
            self.is_active = False
            self.save()

            for profile_attr in ['student_profile', 'teacher_profile', 'staff_profile']:
                if hasattr(self, profile_attr):
                    profile = getattr(self, profile_attr)
                    if not profile.is_deleted:
                        profile.is_deleted = True
                        profile.save()

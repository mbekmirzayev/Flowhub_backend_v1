import re
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.db.models import Func, Model
from django.db.models.fields import UUIDField, SlugField, DateTimeField
from django.utils.text import slugify




class GenRandomUUID(Func):
    function = 'gen_random_uuid'
    template = '%(function)s()'
    output_field = UUIDField()


class UUIDBaseModel(Model):
    id = UUIDField(primary_key=True, db_default=GenRandomUUID(), default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SlugBaseModel(Model):
    slug = SlugField(max_length=255, unique=True, db_index=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            if hasattr(self, 'name'):
                base_slug = slugify(self.name)
            elif hasattr(self, 'title'):
                base_slug = slugify(self.title)
            else:
                base_slug = self.id

            self.slug = base_slug
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class CreateBaseModel(UUIDBaseModel):
    created_at = DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    updated_at = DateTimeField(auto_now=True, blank=True, null=True, editable=False)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam bo'lishi shart")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Status.GLOBAL_ADMIN)

        return self.create_user(normalize_phone(phone), password, **extra_fields)

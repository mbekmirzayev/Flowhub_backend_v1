from django.core.exceptions import ValidationError
from django.db import models

from apps.common.context import is_global_admin_user, get_current_organization_id


class TenantManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()

        if is_global_admin_user():
            return queryset

        org_id = get_current_organization_id()
        if org_id:
            return queryset.filter(organization_id=org_id)

        return queryset


class TenantBaseModel(models.Model):
    organization = models.ForeignKey(
        'organization.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)ss"
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        if hasattr(self, 'role') and self.role == 'global_admin':
            return

        if is_global_admin_user():
            if not self.organization_id:
                raise ValidationError({"organization": "Global admin tashkilotni ko'rsatishi shart!"})
        else:
            org_id = get_current_organization_id()
            if org_id:
                self.organization_id = org_id
            else:
                if not self.organization_id:
                    raise ValidationError("Tashkilot aniqlanmadi.")
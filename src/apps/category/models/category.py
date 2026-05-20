from django.db.models.fields import CharField

from apps.common.models import UUIDBaseModel, SlugBaseModel, TenantBaseModel


class Category(TenantBaseModel, UUIDBaseModel, SlugBaseModel):
    name = CharField(max_length=255)

    class Meta:
        unique_together = (
            ('name', 'organization'),
            ('slug', 'organization'),
        )

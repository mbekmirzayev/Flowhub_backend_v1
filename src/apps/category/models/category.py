from django.db.models import CASCADE, ForeignKey
from django.db.models.fields import CharField

from apps.common.models import UUIDBaseModel, SlugBaseModel
from apps.organization.models.organization import Organization


class Category(UUIDBaseModel, SlugBaseModel):
    organization = ForeignKey(Organization, CASCADE, related_name='categories')
    name = CharField(max_length=255)

    class Meta:
        unique_together = (
            ('name', 'organization'),
            ('slug', 'organization'),
        )
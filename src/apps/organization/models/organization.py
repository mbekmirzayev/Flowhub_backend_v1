from django.db.models.fields import CharField, BooleanField
from django.utils.translation import gettext_lazy as _
from apps.common.models import CreateBaseModel, SlugBaseModel


class Organization(CreateBaseModel, SlugBaseModel):
    name = CharField(max_length=255)
    phone = CharField(max_length=255, blank=True, null=True, verbose_name=_("phone number"))
    is_active = BooleanField(default=True)
    is_deleted = BooleanField(default=False)


    class Meta:
        db_table = 'organizations'
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')
    def __str__(self):
        return self.name



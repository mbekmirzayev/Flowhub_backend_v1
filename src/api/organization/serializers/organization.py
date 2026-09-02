from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from apps.organization.models import Organization


class OrganizationModelSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'slug', 'name', 'phone', 'is_active', 'is_deleted', 'created_at')
        extra_kwargs = {
            'slug': {'read_only': True},
            'is_active': {'read_only': True},
            'is_deleted': {'read_only': True},
        }

    def validate_name(self, value):
        qs = Organization.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("An organization with this name already exists.")
        return value


class OrganizationTenantSerializer(ModelSerializer):
    """
    Restricted serializer for tenant admins viewing/editing their own organization.
    Name and core settings are read-only; only contact fields are writable.
    """
    class Meta:
        model = Organization
        fields = ('id', 'slug', 'name', 'phone', 'is_active', 'created_at')
        extra_kwargs = {
            'slug': {'read_only': True},
            'name': {'read_only': True},      # Tenants cannot rename their org
            'is_active': {'read_only': True},
        }


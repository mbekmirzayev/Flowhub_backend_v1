from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from apps.organization.models import Organization


class OrganizationModelSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = ('created_at', 'id', 'slug', 'name', 'is_active')
        extra_kwargs = {
            'slug': {'read_only': True}
        }

    def validate_name(self, value):
        if Organization.objects.filter(name__iexact=value).exists():
            raise ValidationError("This organization is already exists")
        return value


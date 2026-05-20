from jsonschema import ValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from apps.category.models import Category
from apps.organization.models import Organization
from apps.users import apps


class CategoryModelSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CategoryPostSerializer(ModelSerializer):
    organization_id = PrimaryKeyRelatedField(required=False, source='organization', queryset=Organization.objects.all())

    class Meta:
        model = Category
        fields = ('name', 'organization_id')


    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise ValidationError("Category is already exists")
        return value

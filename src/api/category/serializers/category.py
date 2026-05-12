from jsonschema import ValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from apps.category.models import Category


class CategoryModelSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['slug']

    def validate_name(self, value):
        if Category.objects.filter(name__iexact=value).exists():
            raise ValidationError("Category is already exists")
        return value

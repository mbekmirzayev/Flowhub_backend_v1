from django.utils.text import slugify
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from apps.category.models import Category
from apps.common.context import get_current_organization_id



class CategoryModelSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CategoryPostSerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "organization")

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None

        if user and (getattr(user, 'is_global_admin', False) or user.is_superuser):
            organization = attrs.get("organization")
            organization_id = organization.id if organization else None
        else:
            organization_id = get_current_organization_id()

        if not organization_id:
            raise ValidationError({"organization": "Tashkilot aniqlanmadi."})

        name = attrs.get("name")
        generated_slug = slugify(name)

        if Category.objects.filter(
                organization_id=organization_id,
                name__iexact=name
        ).exists():
            raise ValidationError({
                "name": f"category with name {name} already exists"
            })

        if Category.objects.filter(
                organization_id=organization_id,
                slug=generated_slug
        ).exists():
            raise ValidationError({
                "name": "slug already exist"
            })

        attrs["slug"] = generated_slug
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        if user and not (getattr(user, 'is_global_admin', False) or user.is_superuser):
            validated_data["organization_id"] = get_current_organization_id()

        return super().create(validated_data)

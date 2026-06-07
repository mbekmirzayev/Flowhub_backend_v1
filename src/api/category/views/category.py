from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from api.category.serializers.category import CategoryModelSerializer, CategoryPostSerializer
from apps.category.models import Category
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager


@extend_schema(tags=["Category"])
class CategoryModelViewSet(ModelViewSet):
    queryset = Category.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if getattr(user, 'is_global_admin', False) or user.is_superuser:
                return Category.all_objects.all()

            return Category.objects.all()

        return Category.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CategoryModelSerializer
        return CategoryPostSerializer

    def perform_create(self, serializer):
        user = self.request.user

        if getattr(user, 'is_global_admin', False) or user.is_superuser:
            if 'organization' not in serializer.validated_data and 'organization_id' not in serializer.validated_data:
                raise ValidationError({"organization": "Global admin tashkilotni ko'rsatishi shart."})
            serializer.save()
        else:
            serializer.save()
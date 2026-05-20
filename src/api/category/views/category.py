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

        if user.is_global_admin:
            return Category.objects.all()

        if user.is_local_admin or user.is_manager:
            return Category.objects.filter(organization=user.organization)

        return Category.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CategoryModelSerializer
        return CategoryPostSerializer

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_global_admin:
            # Global admin ixtiyoriy tashkilotni yuborishi shart
            if 'organization' not in serializer.validated_data:
                raise ValidationError({"organization_id": "Global admin tashkilotni ko'rsatishi shart."})
            serializer.save()

        elif user.is_local_admin or user.is_manager:
            # Local admin yoki manager uchun tashkilot avtomatik o'ziniki qilib biriktiriladi
            serializer.save(organization=user.organization)

        else:
            raise ValidationError("Sizda obyekt yaratish huquqi yo'q.")
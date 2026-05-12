from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet

from api.category.serializers.category import CategoryModelSerializer
from apps.category.models import Category
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager


@extend_schema(tags=["Category"])
class CategoryModelViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryModelSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return Category.objects.all()

        if user.is_local_admin or user.is_manager:
            return Category.objects.filter(organization=user.organization)

        return Category.objects.none()

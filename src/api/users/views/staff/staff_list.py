from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from api.users.serializers.staff import StaffListSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager, IsGlobalAdmin
from apps.users.models import StaffProfile


@extend_schema(tags=["Teachers "])
class StaffList(ListAPIView):
    serializer_class = StaffListSerializer
    permission_classes = (IsAdminOrManager, IsGlobalAdmin)
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user__organization', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    ordering_fields = ['created_at', 'user__first_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StaffProfile.objects.all().select_related('user', 'user__organization')

        return StaffProfile.objects.filter(organization_id=user.organization_id).select_related('user')

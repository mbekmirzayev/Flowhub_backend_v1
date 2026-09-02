from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from api.history.serializers.history import HistorySerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.history.models import History


@extend_schema(tags=["History"])
class HistoryListAPIView(ListAPIView):
    serializer_class = HistorySerializer
    permission_classes = (IsAdminOrManager,)
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'student', 'group']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return History.objects.all().select_related('performed_by', 'student', 'group')

        if user.is_local_admin or user.is_manager:
            return History.objects.filter(
                organization=user.organization
            ).select_related('performed_by', 'student', 'group')

        return History.objects.none()

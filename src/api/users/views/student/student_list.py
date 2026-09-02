from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from api.users.serializers.student import StudentListSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.users.models import StudentProfile


@extend_schema(tags=["List"])
class StudentList(ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = (IsAdminOrManager,)
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'is_active', 'status']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    ordering_fields = ['created_at', 'user__first_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_global_admin:
            return StudentProfile.objects.all().select_related('user', 'organization')
        return StudentProfile.objects.filter(
            organization=user.organization
        ).select_related('user')

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from api.users.serializers.teacher import TeacherListSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.users.models import TeacherProfile


@extend_schema(tags=["List"])
class TeacherList(ListAPIView):
    serializer_class = TeacherListSerializer
    permission_classes = (IsAdminOrManager, )
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization', 'user__is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone']
    ordering_fields = ['created_at', 'user__first_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_global_admin:
            return TeacherProfile.all_objects.all().select_related('user', 'organization')
        # TenantManager (objects) already scopes by org via ContextVar;
        # the explicit filter below is a belt-and-suspenders guard.
        return TeacherProfile.objects.filter(
            organization=user.organization
        ).select_related('user')
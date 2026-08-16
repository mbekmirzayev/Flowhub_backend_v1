from drf_spectacular.utils import extend_schema

from api.common.serializers.base import TenantBaseModelViewSet
from api.course.serializers.group import GroupPostSerializer, GroupGetSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.course.models import Group


@extend_schema(tags=["Group"])
class GroupModelViewSet(TenantBaseModelViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user
        is_read = self.action in ('list', 'retrieve')

        if user.is_global_admin:
            qs = Group.objects.all()
        elif user.is_local_admin or user.is_manager:
            qs = Group.objects.filter(organization=user.organization)
        else:
            return Group.objects.none()

        # Always join teacher + course to avoid per-row queries on those FK fields.
        qs = qs.select_related('teacher', 'course')

        if is_read:
            # prefetch_related fetches ALL schedule rows for the returned groups
            # in a single extra SQL query (IN clause), not one query per group.
            # This is the correct tool for reverse-FK / M2M relations.
            qs = qs.prefetch_related('schedule')

        return qs

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return GroupGetSerializer
        return GroupPostSerializer


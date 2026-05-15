from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet

from api.course.serializers.group import GroupPostSerializer, GroupGetSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.course.models import Group


@extend_schema(tags=["Group"])
class GroupModelViewSet(ModelViewSet):
    queryset = Group.objects.select_related('teacher', 'course').all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return Group.objects.all()

        if user.is_local_admin or user.is_manager:
            return Group.objects.filter(organization=user.organization)

        return Group.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupGetSerializer
        return GroupPostSerializer

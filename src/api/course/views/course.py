from drf_spectacular.utils import extend_schema

from api.common.serializers import TenantBaseModelViewSet
from api.course.serializers.course import CourseModelSerializer, CoursePostSerializer
from apps.common.permissions import IsAdminOrManager
from apps.course.models import Course


@extend_schema(tags=["Course"])
class CourseModelViewSet(TenantBaseModelViewSet):
    queryset = Course.objects.prefetch_related('teacher').all()
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return Course.objects.all()

        if user.is_local_admin or user.is_manager:
            return Course.objects.filter(organization=user.organization)

        return Course.objects.none()

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CourseModelSerializer
        return CoursePostSerializer

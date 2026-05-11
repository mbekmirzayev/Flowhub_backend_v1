from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView

from api.users.serializers.student import StudentListSerializer
from apps.category.models import Category
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsTeacher, IsAdminOrManager
from apps.users.models import StudentProfile


@extend_schema(tags=["Teachers "])
class TeacherStudentList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = StudentListSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager, IsTeacher)

    def get_queryset(self):
        teacher = self.request.user.teacher_profile

        return StudentProfile.objects.filter(
            enrollments__group__course__teacher=teacher).distinct().prefetch_related(
            'enrollments__group__course')

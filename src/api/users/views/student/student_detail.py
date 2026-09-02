from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from api.users.serializers.student.student_detail import StudentDetailSerializer, StudentUpdateSerializer
from apps.common.permissions import IsAdminOrManager
from apps.users.models import StudentProfile


@extend_schema(tags=["Students"])
class StudentDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user
        if user.is_global_admin:
            return StudentProfile.objects.all().select_related('user', 'organization')
        return StudentProfile.objects.filter(
            organization=user.organization
        ).select_related('user')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentDetailSerializer
        return StudentUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(
            {'detail': 'Student muvaffaqiyatli o\'chirildi.'},
            status=status.HTTP_204_NO_CONTENT,
        )

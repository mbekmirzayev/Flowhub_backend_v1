from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from api.users.serializers.teacher.teacher_detail import TeacherDetailSerializer, TeacherUpdateSerializer
from apps.common.permissions import IsAdminOrManager
from apps.users.models import TeacherProfile


@extend_schema(tags=["Teachers "])
class TeacherDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user
        if user.is_global_admin:
            return TeacherProfile.all_objects.all().select_related('user', 'organization')
        return TeacherProfile.objects.filter(
            organization=user.organization
        ).select_related('user')


    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TeacherDetailSerializer
        return TeacherUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(
            {'detail': 'O\'qituvchi muvaffaqiyatli o\'chirildi.'},
            status=status.HTTP_204_NO_CONTENT,
        )

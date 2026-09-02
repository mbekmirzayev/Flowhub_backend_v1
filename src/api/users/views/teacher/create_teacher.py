from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.teacher.create_teacher import CreateTeacherProfileSerializer
from apps.common.permissions import IsAdminOrManager


@extend_schema(tags=['Create user'])
class CreateTeacherAPIVIew(APIView):
    serializer_class = CreateTeacherProfileSerializer
    permission_classes = (IsAdminOrManager,)

    def post(self, request):
        serializer = CreateTeacherProfileSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        teacher_profile = serializer.save()

        response_data = {
            "message": "Teacher created successfully.",
            "user": {
                "id": str(teacher_profile.user.id),
                "phone": teacher_profile.user.phone,
                "first_name": teacher_profile.user.first_name,
                "last_name": teacher_profile.user.last_name,
                "role": teacher_profile.user.role,
            },
        }

        if teacher_profile._temp_password:
            response_data["temp_password"] = teacher_profile._temp_password

        return Response(response_data, status=status.HTTP_201_CREATED)

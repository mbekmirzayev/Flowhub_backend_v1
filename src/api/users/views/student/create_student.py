from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.student.create_student import CreateStudentProfileSerializer
from apps.common.permissions import IsAdminOrManager


@extend_schema(tags=['Create user'])
class CreateStudentAPIVIew(APIView):
    serializer_class = CreateStudentProfileSerializer
    permission_classes = (IsAdminOrManager,)

    def post(self, request):
        serializer = CreateStudentProfileSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        student_profile = serializer.save()

        response_data = {
            "message": "Student created successfully.",
            "user": {
                "id": str(student_profile.user.id),
                "phone": student_profile.user.phone,
                "first_name": student_profile.user.first_name,
                "last_name": student_profile.user.last_name,
                "role": student_profile.user.role,
            },
            "temp_password": student_profile._temp_password,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

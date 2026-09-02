from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.staff.create_staff import CreateStaffProfileSerializer
from apps.common.permissions import IsAdminOrManager


@extend_schema(tags=['Create user'])
class CreateStaffAPIView(APIView):
    serializer_class = CreateStaffProfileSerializer
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        staff_profile = serializer.save()

        response_data = {
            "message": "Staff member created successfully.",
            "user": {
                "id": str(staff_profile.user.id),
                "phone": staff_profile.user.phone,
                "first_name": staff_profile.user.first_name,
                "last_name": staff_profile.user.last_name,
                "role": staff_profile.user.role,
            },
        }

        if staff_profile._temp_password:
            response_data["temp_password"] = staff_profile._temp_password

        return Response(response_data, status=status.HTTP_201_CREATED)

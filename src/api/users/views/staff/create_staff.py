from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.staff import CreateStaffProfileSerializer
from api.utils.otp.send_check_otp import send_verification_code, get_temp_user_key
from apps.common.permissions import IsAdminOrManager, IsGlobalAdmin
from apps.users.models import User


class CreateStaffAPIView(APIView):
    serializer_class = CreateStaffProfileSerializer
    permission_classes = [IsAdminOrManager, IsGlobalAdmin]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        user_data = {
            'organization_id': serializer.validated_data.get('organization_id'),
            'phone': phone,
            'role': User.Status.MANAGER,
            'first_name': serializer.validated_data.get('first_name'),
            'last_name': serializer.validated_data.get('last_name'),
            'password': serializer.validated_data.get('password'),
        }
        cache.set(get_temp_user_key(phone), user_data, timeout=300)
        send_verification_code(phone)

        return Response({
            'message': f"Verification code sent to {phone}",
        }, status=status.HTTP_201_CREATED)

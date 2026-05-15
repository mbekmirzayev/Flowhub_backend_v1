from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.student import CreateStudentProfileSerializer
from api.utils.otp.send_check_otp import send_verification_code, get_temp_user_key
from api.utils.phone.normalize_phone import normalize_phone
from apps.common.permissions import IsAdminOrManager
from apps.users.models import User


@extend_schema(tags=['Create user'])
class CreateStudentAPIVIew(APIView):
    serializer_class = CreateStudentProfileSerializer
    permission_classes = (IsAdminOrManager,)

    def post(self, request):
        serializer = CreateStudentProfileSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        phone = normalize_phone(serializer.validated_data['phone'])
        user_data = {
            'organization_id': serializer.validated_data.get('organization_id'),
            'phone': phone,
            'role': User.Status.STUDENT,
            'first_name': serializer.validated_data.get('first_name'),
            'last_name': serializer.validated_data.get('last_name'),
            'parent_phone': serializer.validated_data.get('parent_phone'),
            'group_id': serializer.validated_data.get('group_id')
        }

        cache.set(get_temp_user_key(phone), user_data, timeout=300)

        send_verification_code(phone)

        return Response({
            "message": "Tasdiqlash kodi yuborildi",
            "phone": phone
        }, status=status.HTTP_200_OK)

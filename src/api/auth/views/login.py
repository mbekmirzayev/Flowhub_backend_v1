import hashlib

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth.serializers.login import LoginSerializer
from api.users.serializers.profile import UserModelSerializer
from apps.device.models import Device, UserSession
from apps.users.models import User


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@extend_schema(tags=["auth"])
class LoginAPI(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # --- ROLE CHECK ---
        # Studentlar tizimga kira olmaydi
        if user.role == User.Status.STUDENT:
            return Response(
                {'detail': 'Talabalar uchun tizimga kirish ruxsati yoʻq.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Qurilma ma'lumotlarini olish
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown_browser')
        device_id_hash = hashlib.md5(f"{user.id}-{user_agent}".encode()).hexdigest()

        # Qurilmani saqlash yoki yangilash
        device, _ = Device.objects.update_or_create(
            user=user,
            device_id=device_id_hash,
            defaults={
                'type': Device.DeviceType.WEB,
                'agent': user_agent,
                'is_active': True
            }
        )

        # Sessiya va Token yaratish
        session, tokens = UserSession.create_token(
            user=user,
            device=device,
            ip_address=get_client_ip(request)
        )

        return Response({
            'tokens': tokens,
            'user': UserModelSerializer(user).data
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["auth"])
class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_device_id = request.auth.get('device_id')

        if not token_device_id:
            return Response(
                {'detail': 'Token xato yoki qurilma identifikatori topilmadi.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count, _ = UserSession.objects.filter(
            user=request.user,
            device__device_id=token_device_id
        ).delete()

        if deleted_count > 0:
            return Response({'detail': 'Muvaffaqiyatli chiqildi.'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Sessiya allaqachon yakunlangan.'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["auth"])
class LogoutAllAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserSession.objects.filter(user=request.user).delete()

        return Response(
            {'detail': 'Barcha qurilmalardan muvaffaqiyatli chiqildi.'},
            status=status.HTTP_200_OK
        )

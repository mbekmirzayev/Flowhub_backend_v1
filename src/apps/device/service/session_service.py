from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from apps.device.models import Device
from apps.device.models.session import UserSession


class SessionService:
    @staticmethod
    def create_session(user, device_id, ip_address=None, agent=''):
        UserSession.objects.filter(device__device_id=device_id).delete()

        device_obj, _ = Device.objects.update_or_create(
            user=user,
            device_id=device_id,
            defaults={'agent': agent, 'is_active': True, 'last_active': timezone.now()}
        )

        refresh = RefreshToken.for_user(user)
        refresh['device_id'] = device_id

        UserSession.objects.create(
            user=user,
            device=device_obj,
            refresh_token=str(refresh),
            ip_address=ip_address
        )

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
from rest_framework.serializers import ModelSerializer

from api.device.serializers.device import DeviceSerializer
from apps.device.models import UserSession


class SessionSerializer(ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = UserSession
        fields = ('id', 'device', 'ip_address', 'created', 'last_used')

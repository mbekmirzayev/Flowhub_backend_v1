from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.device.models import Device


class DeviceSerializer(ModelSerializer):
    id = CharField(read_only=True)

    class Meta:
        model = Device
        fields = ('id', 'device_id', 'type', 'agent', 'last_active', 'is_active')
        read_only_fields = ('device_id', 'type', 'agent', 'last_active')

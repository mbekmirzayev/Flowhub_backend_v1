from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.device.serializers.device import DeviceSerializer
from apps.device.models import Device


@extend_schema(tags=["Devices"])
class DeviceListAPIView(ListAPIView):
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user, is_active=True)


@extend_schema(tags=["Devices"])
class DeviceDestroyAPIView(DestroyAPIView):
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deactivate()
        return Response(
            {'detail': 'Qurilma muvaffaqiyatli o\'chirildi.'},
            status=status.HTTP_200_OK,
        )

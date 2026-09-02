from django.urls import path

from api.device.views.device import DeviceListAPIView, DeviceDestroyAPIView
from api.device.views.session import SessionListAPIView, SessionDestroyAPIView, SessionDestroyAllAPIView

urlpatterns = [
    path('devices', DeviceListAPIView.as_view(), name='device-list'),
    path('devices/<uuid:pk>', DeviceDestroyAPIView.as_view(), name='device-destroy'),
    path('sessions', SessionListAPIView.as_view(), name='session-list'),
    path('sessions/all', SessionDestroyAllAPIView.as_view(), name='session-destroy-all'),
    path('sessions/<int:pk>', SessionDestroyAPIView.as_view(), name='session-destroy'),
]

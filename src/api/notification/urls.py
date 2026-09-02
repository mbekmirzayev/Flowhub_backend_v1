from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.notification.views.notification import NotificationModelViewSet, MarkAllNotificationsReadAPIView

router = DefaultRouter()
router.register(r'notification', NotificationModelViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('notification/mark-all-read', MarkAllNotificationsReadAPIView.as_view(), name='notification-mark-all-read'),
]

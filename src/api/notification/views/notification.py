from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.notification.serializers.notification import NotificationSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.notification.models import Notification


@extend_schema(tags=["Notification"])
class NotificationModelViewSet(ModelViewSet):
    serializer_class = NotificationSerializer
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        # Only admins can create (send) notifications; everyone sees their own
        if self.action == 'create':
            return [IsAdminOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # Each user only retrieves their own notifications
        return Notification.objects.filter(recipient=user)

    def perform_update(self, serializer):
        # Any PATCH/PUT on a notification marks it as read
        serializer.save(is_read=True)


@extend_schema(tags=["Notification"])
class MarkAllNotificationsReadAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response(
            {'detail': 'Barcha bildirishnomalar o\'qildi deb belgilandi.'},
            status=status.HTTP_200_OK,
        )

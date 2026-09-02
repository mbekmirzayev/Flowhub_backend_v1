from rest_framework.serializers import ModelSerializer

from apps.notification.models import Notification


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'title', 'message', 'notification_type', 'link', 'is_read', 'created_at')
        read_only_fields = ('is_read', 'created_at')

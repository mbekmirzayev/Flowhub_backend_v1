from django.db.models import DateTimeField, BooleanField, CharField, TextField, ForeignKey, CASCADE, TextChoices, Model

from apps.users.models import User


class Notification(Model):
    class Type(TextChoices):
        INFO = 'info', 'Information'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'

    recipient = ForeignKey(User, CASCADE, related_name='notifications')
    title = CharField(max_length=255)
    message = TextField()
    notification_type = CharField(max_length=10, choices=Type.choices, default=Type.INFO)

    link = CharField(max_length=255, null=True, blank=True)

    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.phone}: {self.title}"
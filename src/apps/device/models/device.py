from django.db.models import TextChoices, ForeignKey, CASCADE
from django.db.models.fields import CharField, TextField, BooleanField, DateTimeField

from apps.common.models import CreateBaseModel
from apps.users.models import User


class Device(CreateBaseModel):
    class DeviceType(TextChoices):
        WEB = 'web', 'Web Browser'

    user = ForeignKey(User, CASCADE, related_name='devices')
    device_id = CharField(max_length=255, db_index=True)
    type = CharField(max_length=20, choices=DeviceType.choices, default=DeviceType.WEB)
    agent = TextField(blank=True, default='')
    last_active = DateTimeField(auto_now=True)
    is_active = BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'device_id')
        ordering = ['-last_active']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        return f"{self.user.phone} - {self.type} ({self.device_id[:8]}...)"

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

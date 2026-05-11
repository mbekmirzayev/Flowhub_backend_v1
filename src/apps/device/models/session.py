from django.db.models import CASCADE, DateTimeField, TextField, GenericIPAddressField, OneToOneField, ForeignKey, Model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.device.models import Device
from apps.users.models import User


class UserSession(Model):
    user = ForeignKey(User, CASCADE, related_name='sessions')
    device = OneToOneField(Device, CASCADE, null=True, blank=True, related_name='session')
    ip_address = GenericIPAddressField(null=True, blank=True)
    refresh_token = TextField()
    created = DateTimeField(auto_now_add=True)
    last_used = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.phone} | {self.device.device_id[:8]}"

    @classmethod
    def create_token(cls, user, device, ip_address):
        # 1. Eski sessiyani o'chirish (Agar bitta qurilmada faqat bitta sessiya bo'lsin desangiz)
        if device:
            cls.objects.filter(user=user, device=device).delete()

        # 2. Yangi sessiya yaratish
        session = cls.objects.create(
            user=user,
            device=device,
            ip_address=ip_address
        )
        refresh = RefreshToken.for_user(user)

        # ⚠️ MUHIM: Middleware tekshirishi uchun tokenga device_id ni qo'shamiz
        if device:
            refresh['device_id'] = device.device_id

        # Tokenni bazaga saqlab qo'yamiz
        session.refresh_token = str(refresh)
        session.save()

        return session, {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def delete(self, *args, **kwargs):
        if self.device:
            self.device.deactivate()
        super().delete(*args, **kwargs)

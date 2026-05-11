from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import Serializer

from api.utils.phone.normalize_phone import normalize_phone
from apps.device.models import Device
from apps.users.models import User


class LoginSerializer(Serializer):
    phone = CharField(default="+998931970019")
    password = CharField(write_only=True, default="salom19")

    def validate(self, attrs):
        phone = normalize_phone(attrs.get('phone'))
        password = attrs.get('password')

        try:
            user = User.objects.only(
                'id', 'phone', 'password', 'first_name',
                'last_name', 'is_active'
            ).get(phone=phone)
        except User.DoesNotExist:
            raise ValidationError("Telefon raqam yoki parol noto'g'ri")

        if not user.is_active:
            raise ValidationError("Akkaunt faol emas")

        if not check_password(password, user.password):
            raise ValidationError("Telefon raqam yoki parol noto'g'ri")

        attrs['user'] = user
        return attrs

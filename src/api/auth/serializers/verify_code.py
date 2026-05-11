from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import Serializer

from api.utils.phone.normalize_phone import normalize_phone
from apps.users.models import User


class VerifyCodeSerializer(Serializer):
    phone = CharField(default="+998931970019")
    code = CharField()



    def validate_phone(self, value):
        value = normalize_phone(value)
        if User.objects.filter(phone=value).exists():
            raise ValidationError(" this number is already in use")
        return value

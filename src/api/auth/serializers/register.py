from django.core.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import Serializer

from api.utils.phone.normalize_phone import normalize_phone
from apps.users.models import User


class RegisterSerializer(Serializer):
    phone = CharField(default="+998931970019")
    organization_id = CharField(required=False, allow_blank=True)
    first_name = CharField(max_length=50, default="Botir")
    last_name = CharField(max_length=50, default="Qodirov")
    password = CharField(write_only=True, min_length=6, default="salom19")
    role = ChoiceField(choices=User.Status.choices, default=User.Status.STUDENT)
    parent_phone = CharField(default="+998901001010", required=False, allow_null=True)
    subject = CharField(default="MATH", required=False, allow_null=True)

    def validate_phone(self, value):
        value = normalize_phone(value)
        if User.objects.filter(phone=value).exists():
            raise ValidationError(" this number is already in use")
        return value

    def validate(self, attrs):
        request_obj = self.context.get('request')

        if not request_obj:
            raise ValidationError("Request not found !")

        if not request_obj or not request_obj.user:
            raise ValidationError("Sizda ushbu amalni bajarish uchun ruxsat yo'q (Login qilinmagan)")

        user = request_obj.user
        role = attrs.get('role')
        organization_id = attrs.get('organization_id')

        if user.role == User.Status.GLOBAL_ADMIN:
            if not organization_id:
                raise ValidationError('Error: organization_id field is required, cause you are global admin')
        else:
            attrs['organization_id'] = user.organization_id

        if not role:
            raise ValidationError('Error: role field is required')

        if role == User.Status.STUDENT:
            if not attrs.get('parent_phone'):
                raise ValidationError('Error: parent_phone field is required')
            attrs['subject'] = None

        elif role == User.Status.TEACHER:
            if not attrs.get('subject'):
                raise ValidationError('Error: subject field is required')
            attrs['parent_phone'] = None

        return attrs

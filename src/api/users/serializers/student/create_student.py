import random
import string

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from api.utils.phone.normalize_phone import normalize_phone
from apps.users.models import User, StudentProfile


def generate_temp_password(length: int = 6) -> str:
    """Generate a random numeric temporary password."""
    return ''.join(random.choices(string.digits, k=length))


def mock_sms(phone: str, password: str) -> None:
    """Mock SMS sender — replace with a real SMS provider in production."""
    print(f"[SMS] To: {phone} | Temp Password: {password}")


class CreateStudentProfileSerializer(ModelSerializer):
    phone = CharField()
    first_name = CharField()
    last_name = CharField()
    parent_phone = CharField(default='', allow_null=True, allow_blank=True)
    group_id = CharField(required=True)
    organization_id = CharField(required=False, allow_null=True)

    def validate_phone(self, value):
        value = normalize_phone(value)
        if User.objects.filter(phone=value).exists():
            raise ValidationError("This number is already in use.")
        return value

    def validate(self, attrs):
        request_obj = self.context.get('request')

        if not request_obj:
            raise ValidationError("Request not found!")

        if not request_obj.user:
            raise ValidationError("Sizda ushbu amalni bajarish uchun ruxsat yo'q (Login qilinmagan)")

        user = request_obj.user
        organization_id = attrs.get('organization_id')

        if user.role == User.Status.GLOBAL_ADMIN:
            if not organization_id:
                raise ValidationError('organization_id is required for global admin.')
        else:
            attrs['organization_id'] = str(user.organization_id)

        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        organization_id = validated_data.pop('organization_id')
        # Students don't log in, but we still set a temp password for consistency
        raw_password = generate_temp_password()

        mock_sms(phone, raw_password)

        with transaction.atomic():
            user = User.objects.create_user(
                phone=phone,
                password=raw_password,
                first_name=first_name,
                last_name=last_name,
                role=User.Status.STUDENT,
                organization_id=organization_id,
                is_active=True,
                is_staff=False,
            )
            student_profile = StudentProfile.objects.create(
                user=user,
                organization_id=organization_id,
                status=StudentProfile.StudentStatus.ACTIVE,
                **validated_data,
            )

        student_profile._temp_password = raw_password
        return student_profile

    class Meta:
        model = StudentProfile
        fields = ('id', 'phone', 'first_name', 'last_name', 'parent_phone', 'group_id', 'organization_id')

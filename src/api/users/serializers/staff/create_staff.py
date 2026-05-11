from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from api.utils.phone.normalize_phone import normalize_phone
from apps.users.models import User, StaffProfile


class CreateStaffProfileSerializer(ModelSerializer):
    phone = CharField(default="+998931970092")
    first_name = CharField(default="Enzo2")
    last_name = CharField(default="Ernandez2")
    organization_id = CharField(required=False, allow_null=True)
    password = CharField(required=True, write_only=True)

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
        organization_id = attrs.get('organization_id')

        if user.role == User.Status.GLOBAL_ADMIN:
            if not organization_id and len(user.organization_id) < 10 :
                raise ValidationError('Error: organization_id field is required, cause you are global admin')
        else:
            attrs['organization_id'] = user.organization_id

        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')
        organization_id = validated_data.pop('organization_id')
        with transaction.atomic():
            user = User.objects.create(
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                password=password,
                organization_id=organization_id
            )
        staff_profile = StaffProfile.objects.create(user=user, **validated_data)
        return staff_profile

    class Meta:
        model = StaffProfile
        fields = ('id', 'phone', 'first_name', 'last_name', 'organization_id', 'password')

from rest_framework.fields import CharField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.users.models import StudentProfile


class StudentDetailSerializer(ModelSerializer):
    id = CharField(read_only=True)
    first_name = CharField(source='user.first_name', read_only=True)
    last_name = CharField(source='user.last_name', read_only=True)
    phone = CharField(source='user.phone', read_only=True)
    organization_id = CharField(source='organization.id', read_only=True)
    is_deleted = BooleanField(read_only=True)
    is_active = BooleanField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            'id', 'first_name', 'last_name', 'phone',
            'parent_phone', 'status', 'is_deleted', 'is_active',
            'organization_id', 'created_at',
        )


class StudentUpdateSerializer(ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ('parent_phone', 'status', 'is_active')

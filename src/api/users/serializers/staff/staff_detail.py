from rest_framework.fields import CharField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.users.models import StaffProfile


class StaffDetailSerializer(ModelSerializer):
    id = CharField(source='user.id', read_only=True)
    first_name = CharField(source='user.first_name', read_only=True)
    last_name = CharField(source='user.last_name', read_only=True)
    phone = CharField(source='user.phone', read_only=True)
    organization_id = CharField(source='user.organization.id', read_only=True)
    is_deleted = BooleanField(read_only=True)
    is_active = BooleanField(read_only=True)

    class Meta:
        model = StaffProfile
        fields = (
            'id', 'first_name', 'last_name', 'phone',
            'salary', 'is_deleted', 'is_active',
            'organization_id', 'created_at',
        )


class StaffUpdateSerializer(ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ('salary', 'is_active')

from rest_framework.fields import CharField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.users.models import TeacherProfile


class TeacherDetailSerializer(ModelSerializer):
    id = CharField(read_only=True)
    first_name = CharField(source='user.first_name', read_only=True)
    last_name = CharField(source='user.last_name', read_only=True)
    phone = CharField(source='user.phone', read_only=True)
    organization_id = CharField(source='user.organization.id', read_only=True)
    is_deleted = BooleanField(read_only=True)
    is_active = BooleanField(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = (
            'id', 'first_name', 'last_name', 'phone',
            'subject', 'work_type', 'salary_type', 'salary',
            'is_deleted', 'is_active', 'organization_id', 'created_at',
        )


class TeacherUpdateSerializer(ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ('subject', 'work_type', 'salary_type', 'salary', 'is_active')

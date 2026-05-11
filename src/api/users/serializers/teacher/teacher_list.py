from rest_framework.fields import CharField, BooleanField
from rest_framework.serializers import ModelSerializer

from apps.users.models import TeacherProfile


class TeacherListSerializer(ModelSerializer):
    id = CharField(read_only=True)
    first_name = CharField(read_only=True)
    last_name = CharField(read_only=True)
    phone = CharField(read_only=True)

    is_deleted = BooleanField(read_only=True)
    subject = CharField(read_only=True)
    work_type = CharField(read_only=True)
    organization_id = CharField(source='user.organization.id', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ('id', 'first_name', 'last_name', 'phone', 'is_deleted', 'subject', 'work_type', 'organization_id')
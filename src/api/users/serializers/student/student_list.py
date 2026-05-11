from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.users.models import StudentProfile


class StudentListSerializer(ModelSerializer):
    first_name = CharField(source='user.phone', read_only=True)
    last_name = CharField(source='user.phone', read_only=True)
    phone = CharField(source='user.phone', read_only=True)

    class Meta:
        model = StudentProfile
        fields = 'id', 'first_name', 'last_name', 'phone'

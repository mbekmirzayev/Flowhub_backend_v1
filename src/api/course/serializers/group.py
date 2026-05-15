from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from apps.course.models import Group
from apps.users.models import TeacherProfile


class GroupPostSerializer(ModelSerializer):
    teacher_id = PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        source='teacher',  # Model maydoni nomi 'teacher'
        write_only=True,
        required=False,
        allow_null=True
    )
    class Meta:
        model = Group
        fields = ('course', 'name', 'status', 'teacher_id')


class GroupGetSerializer(ModelSerializer):
    id = CharField(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'

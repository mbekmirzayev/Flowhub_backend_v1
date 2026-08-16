from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from api.course.serializers.group_schedule import GroupScheduleReadSerializer
from apps.course.models import Group
from apps.users.models import TeacherProfile


class GroupPostSerializer(ModelSerializer):
    teacher_id = PrimaryKeyRelatedField(
        queryset=TeacherProfile.objects.all(),
        source='teacher',  # Model maydoni nomi 'teacher'
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Group
        fields = ('course', 'name', 'status', 'teacher_id', 'start_date')


class GroupGetSerializer(ModelSerializer):
    id = CharField(read_only=True)

    # Reverse FK: Group.schedule.all() — defined by related_name='schedule' on GroupSchedule.group
    # many=True because a group CAN have multiple schedule records (e.g. morning + afternoon slots)
    # read_only=True because schedules are managed via the dedicated /group/<id>/schedule endpoint
    schedule = GroupScheduleReadSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = (
            'id',
            'organization',
            'course',
            'teacher',
            'name',
            'status',
            'start_date',
            'schedule',       # ← nested schedule objects
            'created_at',
        )


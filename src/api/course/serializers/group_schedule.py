from rest_framework.serializers import ModelSerializer

from apps.course.models.group_schedule import GroupSchedule


class GroupScheduleSerializer(ModelSerializer):
    """Write serializer — used by GroupScheduleModelViewSet (POST/PUT/PATCH)."""

    class Meta:
        model = GroupSchedule
        fields = ('id', 'group', 'selected_days', 'start_time', 'end_time')
        extra_kwargs = {
            'group': {'read_only': True},
        }


class GroupScheduleReadSerializer(ModelSerializer):
    """
    Read-only serializer — nested inside GroupGetSerializer.
    We deliberately omit 'group' here because it is redundant: the consumer
    already knows which group they are looking at from the parent object.
    """

    class Meta:
        model = GroupSchedule
        fields = ('id', 'selected_days', 'start_time', 'end_time')


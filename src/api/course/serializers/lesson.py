from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.course.models.lesson import Lesson


class LessonGetSerializer(ModelSerializer):
    id = CharField(read_only=True)
    group = CharField(source='group_id', read_only=True)
    teacher = CharField(source='teacher_id', read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'group', 'teacher', 'date', 'status', 'reason')


class LessonPostSerializer(ModelSerializer):
    """Used when manually creating a single lesson."""

    class Meta:
        model = Lesson
        fields = ('date', 'status', 'reason', 'teacher')


class LessonCompleteSerializer(ModelSerializer):
    """Used for PATCH /lesson/<id>/complete — optionally override teacher."""

    class Meta:
        model = Lesson
        fields = ('teacher',)
        extra_kwargs = {
            'teacher': {'required': False, 'allow_null': True},
        }


class LessonCancelSerializer(ModelSerializer):
    """Used for PATCH /lesson/<id>/cancel — reason is required."""

    class Meta:
        model = Lesson
        fields = ('reason',)
        extra_kwargs = {
            'reason': {'required': True, 'allow_blank': False},
        }

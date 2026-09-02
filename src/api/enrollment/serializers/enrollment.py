from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.course.models import Group
from apps.enrollment.models import Enrollment
from apps.users.models import StudentProfile


class EnrollmentGetSerializer(ModelSerializer):
    id = CharField(read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'group', 'status', 'left_at', 'created_at')


class EnrollmentPostSerializer(ModelSerializer):
    student_id = PrimaryKeyRelatedField(
        queryset=StudentProfile.objects.all(),
        source='student',
    )
    group_id = PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='group',
    )

    class Meta:
        model = Enrollment
        fields = ('student_id', 'group_id', 'status', 'left_at')


class TransferSerializer(Serializer):
    """Input for PATCH enrollment/<id>/transfer."""
    to_group_id = PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        source='to_group',
    )
    reason = CharField(required=False, allow_blank=True, default="")


class DropoutSerializer(Serializer):
    """Input for PATCH enrollment/<id>/dropout."""
    reason = CharField(required=False, allow_blank=True, default="")


class FreezeSerializer(Serializer):
    """Input for PATCH student/<id>/freeze — student-level, not enrollment-level."""
    reason = CharField(required=False, allow_blank=True, default="")


class LeaveSerializer(Serializer):
    """
    Input for PATCH enrollment/<id>/leave — student voluntarily exits a group.

    `reason` is optional but strongly recommended for audit clarity.

    Contrast with DropoutSerializer (`/dropout`):
    - /leave  → enrollment closed, StudentProfile.status unchanged (STUDENT_LEFT in History)
    - /dropout → enrollment closed, StudentProfile.status = DROPPED  (STUDENT_DROPPED in History)
    """
    reason = CharField(required=False, allow_blank=True, default="")


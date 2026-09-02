"""
MeSerializer
============
Returns the authenticated user's base fields plus the role-specific
profile nested under a `profile` key.  Reuses the existing
{Student,Teacher,Staff}DetailSerializer so the shape is consistent
with the individual detail endpoints.
"""
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from api.users.serializers.student.student_detail import StudentDetailSerializer
from api.users.serializers.teacher.teacher_detail import TeacherDetailSerializer
from api.users.serializers.staff.staff_detail import StaffDetailSerializer
from apps.users.models import User


class MeSerializer(ModelSerializer):
    """
    Read-only serializer for `GET /me`.

    `profile` is dynamically populated based on the user's role:
      - student  → StudentDetailSerializer  (StudentProfile)
      - teacher  → TeacherDetailSerializer  (TeacherProfile)
      - admin / manager  → StaffDetailSerializer  (StaffProfile)
      - global_admin → None (no separate profile table)
    """

    profile = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'phone',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'organization',
            'profile',
        )
        read_only_fields = fields

    def get_profile(self, user: User):
        if user.role == User.Status.STUDENT:
            profile = getattr(user, 'student_profile', None)
            if profile:
                return StudentDetailSerializer(profile).data

        elif user.role == User.Status.TEACHER:
            profile = getattr(user, 'teacher_profile', None)
            if profile:
                return TeacherDetailSerializer(profile).data

        elif user.role in (User.Status.ADMIN, User.Status.MANAGER):
            profile = getattr(user, 'staff_profile', None)
            if profile:
                return StaffDetailSerializer(profile).data

        # GLOBAL_ADMIN has no separate profile table
        return None

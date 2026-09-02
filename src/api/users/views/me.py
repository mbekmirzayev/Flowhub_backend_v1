"""
MeAPIView
=========
GET /me — returns the authenticated user's own profile.
No body required. The response shape varies by role (profile key).
"""
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.users.serializers.me import MeSerializer


@extend_schema(
    tags=["auth"],
    summary="Get current user profile",
    description=(
        "Returns the authenticated user's base fields (`id`, `phone`, `role`, etc.) "
        "and a nested `profile` object that reflects their role:\n\n"
        "- **student** → `StudentDetailSerializer` fields\n"
        "- **teacher** → `TeacherDetailSerializer` fields\n"
        "- **admin / manager** → `StaffDetailSerializer` fields\n"
        "- **global_admin** → `profile` is `null` (no separate profile table)\n\n"
        "This endpoint is always scoped to the **currently authenticated user** "
        "and does not accept any input."
    ),
)
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Prefetch the relevant profile in a single query to avoid N+1
        user = request.user
        role = user.role

        if role == user.Status.STUDENT:
            user = (
                type(user).objects
                .select_related('student_profile', 'organization')
                .get(pk=user.pk)
            )
        elif role == user.Status.TEACHER:
            user = (
                type(user).objects
                .select_related('teacher_profile', 'organization')
                .get(pk=user.pk)
            )
        elif role in (user.Status.ADMIN, user.Status.MANAGER):
            user = (
                type(user).objects
                .select_related('staff_profile', 'organization')
                .get(pk=user.pk)
            )
        # GLOBAL_ADMIN: no extra select_related needed

        serializer = MeSerializer(user)
        return Response(serializer.data)

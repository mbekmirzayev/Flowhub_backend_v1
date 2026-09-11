"""
ChangePasswordAPI
==================
POST /api/v1/change-password  — changes the authenticated user's password.

Body:
    {
        "current_password": "...",
        "new_password": "...",
        "confirm_password": "..."
    }

Responses:
    200 — password changed successfully
    400 — validation error (wrong current password / mismatch)
    401 — not authenticated
"""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth.serializers.change_password import ChangePasswordSerializer


@extend_schema(tags=["auth"], summary="Change current user password")
class ChangePasswordAPI(APIView):
    """
    Authenticated endpoint to change the current user's password.

    POST /api/v1/change-password
    Body: { "current_password": "...", "new_password": "...", "confirm_password": "..." }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        # Validate the current password
        if not user.check_password(current_password):
            return Response(
                {"detail": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set and persist the new hashed password
        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

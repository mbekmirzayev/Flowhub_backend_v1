from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.auth.serializers.change_password import ChangePasswordSerializer


@extend_schema(tags=["auth"])
class ChangePasswordAPI(APIView):
    """
    Authenticated endpoint to change the current user's password.

    POST /api/v1/change_password
    Body: { "old_password": "...", "new_password": "..." }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Validate the current password
        if not user.check_password(old_password):
            return Response(
                {"old_password": "The current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set and persist the new hashed password
        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

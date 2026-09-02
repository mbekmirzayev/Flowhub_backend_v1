from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=1,
        help_text="The user's current password.",
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        help_text="The new password. Must be at least 6 characters.",
    )

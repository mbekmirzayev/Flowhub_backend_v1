from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=1,
        help_text="The user's current (old) password.",
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        help_text="The new password. Must be at least 6 characters.",
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=6,
        help_text="Must match new_password exactly.",
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "New passwords do not match."}
            )
        return attrs

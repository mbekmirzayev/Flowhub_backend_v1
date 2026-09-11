"""
UpdateMeSerializer
==================
Writable serializer used by PATCH /api/v1/me.
Only allows first_name, last_name, and phone to be updated.
Profile picture is intentionally excluded (locked in the UI).
"""
from rest_framework import serializers

from apps.users.models import User


class UpdateMeSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        required=True,
        min_length=1,
        max_length=150,
        trim_whitespace=True,
        help_text="User's first name.",
    )
    last_name = serializers.CharField(
        required=True,
        min_length=1,
        max_length=150,
        trim_whitespace=True,
        help_text="User's last name.",
    )
    phone = serializers.CharField(
        required=False,
        max_length=20,
        trim_whitespace=True,
        help_text="Phone number (unique). Cannot be changed to an existing user's phone.",
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone')

    def validate_phone(self, value):
        """Ensure the phone is not already taken by a different user."""
        request = self.context.get('request')
        qs = User.objects.filter(phone=value)
        if request and qs.exclude(pk=request.user.pk).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value

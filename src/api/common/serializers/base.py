from rest_framework import serializers


class BaseOrganizationSerializer(serializers.ModelSerializer):
    """
    Hamma tashkilotga tegishli serializerlar uchun asosiy klass.
    organization_id ni request jo'natayotgan userdan avtomatik oladi.
    """

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        if user and user.is_superuser:
            if 'organization' not in validated_data:
                raise serializers.ValidationError(
                    {"organization": "Global admin tashkilotni ko'rsatishi shart!"}
                )
        else:
            validated_data['organization'] = user.organization

        return super().create(validated_data)
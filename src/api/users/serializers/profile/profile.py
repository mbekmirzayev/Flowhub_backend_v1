from rest_framework.serializers import ModelSerializer

from apps.users.models import User


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'is_active')


class UserModelDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
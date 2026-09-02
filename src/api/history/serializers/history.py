from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.history.models import History


class HistorySerializer(ModelSerializer):
    id = CharField(read_only=True)
    performed_by_name = CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = History
        fields = (
            'id', 'performed_by', 'performed_by_name',
            'description', 'student', 'group',
            'action', 'organization', 'created_at',
        )

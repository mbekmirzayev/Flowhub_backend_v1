from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ChoiceField, ListField
from rest_framework.serializers import ModelSerializer, Serializer

from apps.attendance.models import Attendance


class AttendanceGetSerializer(ModelSerializer):
    id = CharField(read_only=True)
    date = CharField(source='lesson.date', read_only=True)
    group_id = CharField(source='lesson.group_id', read_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id',
            'lesson',
            'group_id',
            'date',
            'student',
            'status',
            'marked_by',
            'organization',
            'created_at',
        )


class AttendancePostSerializer(ModelSerializer):

    class Meta:
        model = Attendance
        fields = ('lesson', 'student', 'status')


class BulkAttendanceItemSerializer(Serializer):
    student_id = CharField()
    status = ChoiceField(choices=Attendance.Status.choices)


class BulkAttendanceSerializer(Serializer):

    lesson_id = CharField()
    records = ListField(child=BulkAttendanceItemSerializer(), allow_empty=False)

    def validate_records(self, value):
        student_ids = [r['student_id'] for r in value]
        if len(student_ids) != len(set(student_ids)):
            raise ValidationError("Duplicate student_ids in records — each student must appear once.")
        return value

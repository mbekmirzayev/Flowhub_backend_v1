from rest_framework.relations import PrimaryKeyRelatedField, StringRelatedField
from rest_framework.serializers import ModelSerializer

from apps.category.models import Category
from apps.course.models import Course
from apps.users.models import TeacherProfile


class CourseModelSerializer(ModelSerializer):
    teacher = StringRelatedField(many=True)

    class Meta:
        model = Course
        fields = '__all__'


class CoursePostSerializer(ModelSerializer):
    teachers = PrimaryKeyRelatedField(
        many=True,
        queryset=TeacherProfile.objects.all(),
        source='teacher'  # Agar modelda nomi 'teacher' bo'lsa
    )
    category_id = PrimaryKeyRelatedField(
        source='category',
        queryset=Category.objects.all()

    )

    class Meta:
        model = Course
        fields = ('title', 'teachers', 'duration', 'lesson_count', 'price', 'category_id')

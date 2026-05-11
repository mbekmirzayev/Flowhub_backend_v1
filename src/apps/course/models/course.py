from django.db.models import ForeignKey, CASCADE, SET_NULL, ManyToManyField
from django.db.models.fields import CharField, IntegerField, DecimalField
from django.utils.translation import gettext_lazy as _

from apps.category.models import Category
from apps.common.models import SlugBaseModel, CreateBaseModel
from apps.organization.models.organization import Organization
from apps.users.models import TeacherProfile


class Course(CreateBaseModel, SlugBaseModel):
    organization = ForeignKey(Organization, CASCADE, related_name='course')
    category = ForeignKey(Category, SET_NULL, null=True, blank=True, related_name='course')
    title = CharField(max_length=255, verbose_name=_("Course title"))
    teacher = ManyToManyField(TeacherProfile, related_name='course')
    duration = CharField(max_length=255, verbose_name='Duration')
    lesson_count = IntegerField(default=0)
    price = DecimalField(max_digits=10, decimal_places=2)

    @property
    def teacher_images(self):
        return [i.image.url for i in self.teacher.all() if i.image]

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")

    def __str__(self):
        return self.title

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.course.views.course import CourseModelViewSet
from api.course.views.group import GroupModelViewSet

router = DefaultRouter()
router.register(r'course', CourseModelViewSet, basename='course')
router.register(r'group', GroupModelViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
]
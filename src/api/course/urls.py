from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.course.views.course import CourseModelViewSet
from api.course.views.group import GroupModelViewSet
from api.course.views.group_schedule import GroupScheduleModelViewSet
from api.course.views.lesson import LessonModelViewSet

router = DefaultRouter()
router.register(r'course', CourseModelViewSet, basename='course')
router.register(r'group', GroupModelViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
    # Nested schedule endpoints under a specific group
    path('group/<uuid:group_id>/schedule', GroupScheduleModelViewSet.as_view({
        'get': 'list',
        'post': 'create',
    }), name='group-schedule-list'),
    path('group/<uuid:group_id>/schedule/<uuid:pk>', GroupScheduleModelViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='group-schedule-detail'),
    # Nested lesson endpoints under a specific group
    path('group/<uuid:group_id>/lesson', LessonModelViewSet.as_view({
        'get': 'list',
        'post': 'create',
    }), name='group-lesson-list'),
    path('group/<uuid:group_id>/lesson/<uuid:pk>', LessonModelViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='group-lesson-detail'),
]
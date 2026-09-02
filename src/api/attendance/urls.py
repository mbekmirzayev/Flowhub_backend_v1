from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.attendance.views.attendance import AttendanceModelViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceModelViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.enrollment.views.enrollment import EnrollmentModelViewSet

router = DefaultRouter()
router.register(r'enrollment', EnrollmentModelViewSet, basename='enrollment')

urlpatterns = [
    path('', include(router.urls)),
]

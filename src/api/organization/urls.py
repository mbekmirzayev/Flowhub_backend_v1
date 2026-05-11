from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from api.organization.views.organization import OrganizationModelViewSet

router = DefaultRouter()
router.register(r'organization', OrganizationModelViewSet, basename='organization')

urlpatterns = [
    path('/', include(router.urls)),
]
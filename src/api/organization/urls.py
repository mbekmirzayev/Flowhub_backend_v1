from django.urls import path, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter

from api.organization.views.organization import OrganizationModelViewSet, MyOrganizationView

router = DefaultRouter()
router.register(r'organization', OrganizationModelViewSet, basename='organization')

urlpatterns = [
    path('organization/my/', MyOrganizationView.as_view(), name='my-organization'),
    path('', include(router.urls)),
]
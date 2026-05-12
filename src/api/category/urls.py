from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.category.views import CategoryModelViewSet

router = DefaultRouter()
router.register(r'category', CategoryModelViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]

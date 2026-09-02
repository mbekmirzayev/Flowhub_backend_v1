from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.payment.views.payment import PaymentModelViewSet

router = DefaultRouter()
router.register(r'payment', PaymentModelViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.device.serializers.session import SessionSerializer
from apps.device.models import UserSession


@extend_schema(tags=["Sessions"])
class SessionListAPIView(ListAPIView):
    serializer_class = SessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user).select_related('device')


@extend_schema(tags=["Sessions"])
class SessionDestroyAPIView(DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {'detail': 'Sessiya muvaffaqiyatli yakunlandi.'},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Sessions"])
class SessionDestroyAllAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        UserSession.objects.filter(user=request.user).delete()
        return Response(
            {'detail': 'Barcha sessiyalar muvaffaqiyatli yakunlandi.'},
            status=status.HTTP_200_OK,
        )

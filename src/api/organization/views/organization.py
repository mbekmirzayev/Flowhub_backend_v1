from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.organization.serializers import OrganizationModelSerializer, OrganizationTenantSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsGlobalAdmin
from apps.organization.models import Organization
from apps.users.models import User


@extend_schema(tags=['Organization'])
class OrganizationModelViewSet(ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationModelSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsGlobalAdmin,)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs


@extend_schema(tags=['Organization'])
class MyOrganizationView(APIView):
    """
    GET  /organization/my/  — returns the current tenant's organization profile.
    PATCH /organization/my/ — updates only allowed contact fields (phone).
    Only for non-global-admin authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def _get_org(self, user):
        if user.role == User.Status.GLOBAL_ADMIN:
            return None
        return getattr(user, 'organization', None)

    def get(self, request):
        org = self._get_org(request.user)
        if org is None:
            return Response(
                {'detail': 'Global admins do not have a single organization profile. Use the organizations list.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(OrganizationTenantSerializer(org).data)

    def patch(self, request):
        org = self._get_org(request.user)
        if org is None:
            return Response(
                {'detail': 'Global admins cannot use this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = OrganizationTenantSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet

from api.organization.serializers import OrganizationModelSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsGlobalAdmin
from apps.organization.models import Organization


@extend_schema(tags=['Organization'])
class OrganizationModelViewSet(ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationModelSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsGlobalAdmin,)


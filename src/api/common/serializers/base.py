from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet


class TenantBaseModelViewSet(ModelViewSet):
    """
    Tashkilotga (Organization) bog'liq barcha ViewSet'lar
    uchun umumiy ota klass.
    """

    def perform_create(self, serializer):
        user = self.request.user
        save_kwargs = {}

        if user.is_global_admin:
            if 'organization' not in serializer.validated_data:
                raise ValidationError({"organization_id": "Global admin tashkilotni ko'rsatishi shart."})
        elif user.is_local_admin or user.is_manager:
            save_kwargs['organization'] = user.organization
        else:
            raise ValidationError("Sizda obyekt yaratish huquqi yo'q.")

        serializer.save(**save_kwargs)

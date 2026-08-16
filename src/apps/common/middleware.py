import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

from .context import set_current_tenant, clear_current_tenant

User = get_user_model()


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        org_id = None
        is_global = False

        if user and user.is_authenticated:
            is_global = getattr(user, 'is_global_admin', False) or user.is_superuser
            org_id = getattr(user, "organization_id", None) or (
                user.organization.id if getattr(user, 'organization', None) else None)

        else:
            auth_header = request.headers.get('Authorization', None)
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('user_id')

                    if user_id:
                        db_user = User.objects.filter(id=user_id).first()
                        if db_user:
                            request.user = db_user
                            is_global = getattr(db_user, 'is_global_admin', False) or db_user.is_superuser

                            if getattr(db_user, 'organization', None):
                                org_id = db_user.organization.id
                            else:
                                org_id = getattr(db_user, 'organization_id', None)
                except Exception:
                    pass

        if org_id or is_global:
            set_current_tenant(organization_id=org_id, is_global=is_global)
        else:
            clear_current_tenant()

        response = self.get_response(request)

        clear_current_tenant()
        return response

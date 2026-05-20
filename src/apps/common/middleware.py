from .context import set_current_tenant, clear_current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            is_global = request.user.is_superuser 

            org_id = getattr(request.user, "organization_id", None)

            set_current_tenant(organization_id=org_id, is_global=is_global)
        else:
            clear_current_tenant()

        response = self.get_response(request)

        clear_current_tenant()
        return response
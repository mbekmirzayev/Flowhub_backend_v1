from django.db.models import Manager

from apps.common.context import is_global_admin_user, get_current_organization_id


class LinkedTenantManager(Manager):
    def __init__(self, lookup_path, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.lookup_path = lookup_path

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_global_admin_user():
            return queryset

        org_id = get_current_organization_id()
        if org_id:
            return queryset.filter(**{self.lookup_path: org_id})
        return queryset

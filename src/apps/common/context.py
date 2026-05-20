from contextvars import ContextVar

# Faqat joriy so'rov uchun tashkilot ID-sini saqlash
_current_organization_id = ContextVar("current_organization_id", default=None)
_is_global_admin = ContextVar("is_global_admin", default=False)

def set_current_tenant(organization_id, is_global=False):
    _current_organization_id.set(organization_id)
    _is_global_admin.set(is_global)

def get_current_organization_id():
    return _current_organization_id.get()

def is_global_admin_user():
    return _is_global_admin.get()

def clear_current_tenant():
    _current_organization_id.set(None)
    _is_global_admin.set(False)
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.organization.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "slug",
        "status_badge",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_active", "is_deleted")
    search_fields = ("name", "phone", "slug")
    readonly_fields = ("slug", "created_at", "updated_at")
    ordering = ("name",)
    actions = ["activate_organizations", "deactivate_organizations"]

    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "phone", "slug"),
        }),
        (_("Status"), {
            "fields": ("is_active", "is_deleted"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Status"), ordering="is_active")
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#28a745;font-weight:bold;">● Active</span>'
            )
        return format_html(
            '<span style="color:#dc3545;font-weight:bold;">● Inactive</span>'
        )

    @admin.action(description=_("Activate selected organizations"))
    def activate_organizations(self, request, queryset):
        updated = queryset.update(is_active=True, is_deleted=False)
        self.message_user(request, _(f"{updated} organization(s) activated."))

    @admin.action(description=_("Deactivate selected organizations"))
    def deactivate_organizations(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f"{updated} organization(s) deactivated."))

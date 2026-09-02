from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.device.models import Device, UserSession


# ---------------------------------------------------------------------------
# Inline: UserSession inside DeviceAdmin
# ---------------------------------------------------------------------------

class UserSessionInline(admin.StackedInline):
    model = UserSession
    can_delete = True
    extra = 0
    fields = ("user", "ip_address", "created", "last_used")
    readonly_fields = ("created", "last_used", "refresh_token")
    verbose_name = _("Session")
    verbose_name_plural = _("Sessions")


# ---------------------------------------------------------------------------
# Device Admin
# ---------------------------------------------------------------------------

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "device_id_short",
        "type",
        "agent_short",
        "is_active_badge",
        "last_active",
        "created_at",
    )
    list_filter = ("type", "is_active")
    search_fields = ("user__phone", "user__first_name", "device_id", "agent")
    readonly_fields = ("last_active", "created_at", "updated_at")
    ordering = ("-last_active",)
    inlines = [UserSessionInline]
    actions = ["deactivate_devices"]

    fieldsets = (
        (_("Device Info"), {
            "fields": ("user", "device_id", "type", "agent"),
        }),
        (_("Status"), {
            "fields": ("is_active", "last_active"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Device ID"))
    def device_id_short(self, obj):
        return f"{obj.device_id[:12]}…" if len(obj.device_id) > 12 else obj.device_id

    @admin.display(description=_("Agent"))
    def agent_short(self, obj):
        if obj.agent:
            return obj.agent[:40] + ("…" if len(obj.agent) > 40 else "")
        return "—"

    @admin.display(description=_("Active"), boolean=False, ordering="is_active")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#28a745;font-weight:bold;">● Active</span>'
            )
        return format_html(
            '<span style="color:#dc3545;font-weight:bold;">● Inactive</span>'
        )

    @admin.action(description=_("Deactivate selected devices"))
    def deactivate_devices(self, request, queryset):
        count = 0
        for device in queryset.filter(is_active=True):
            device.deactivate()
            count += 1
        self.message_user(request, _(f"{count} device(s) deactivated."))

    def get_queryset(self, request):
        return Device.all_objects.select_related("user")


# ---------------------------------------------------------------------------
# UserSession Admin
# ---------------------------------------------------------------------------

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "device",
        "ip_address",
        "created",
        "last_used",
    )
    list_filter = ("user__organization",)
    search_fields = ("user__phone", "user__first_name", "ip_address", "device__device_id")
    readonly_fields = ("created", "last_used", "refresh_token")
    ordering = ("-created",)

    fieldsets = (
        (_("Session Info"), {
            "fields": ("user", "device", "ip_address"),
        }),
        (_("Token"), {
            "fields": ("refresh_token",),
            "classes": ("collapse",),
        }),
        (_("Timestamps"), {
            "fields": ("created", "last_used"),
        }),
    )

    def has_add_permission(self, request):
        """Sessions are created programmatically, not via admin."""
        return False

    def get_queryset(self, request):
        return UserSession.all_objects.select_related("user", "device")

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.notification.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "title",
        "type_badge",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read")
    search_fields = ("recipient__phone", "recipient__first_name", "title", "message")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["mark_as_read", "mark_as_unread"]

    fieldsets = (
        (_("Recipient"), {
            "fields": ("recipient",),
        }),
        (_("Content"), {
            "fields": ("title", "message", "notification_type", "link"),
        }),
        (_("Status"), {
            "fields": ("is_read", "created_at"),
        }),
    )

    @admin.display(description=_("Type"), ordering="notification_type")
    def type_badge(self, obj):
        colors = {
            "info": "#17a2b8",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
        }
        color = colors.get(obj.notification_type, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_notification_type_display(),
        )

    @admin.action(description=_("Mark selected notifications as read"))
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, _(f"{updated} notification(s) marked as read."))

    @admin.action(description=_("Mark selected notifications as unread"))
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, _(f"{updated} notification(s) marked as unread."))

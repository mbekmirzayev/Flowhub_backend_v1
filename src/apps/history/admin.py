from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.history.models import History


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    """
    History is an immutable audit log — all fields are read-only.
    Deletion and addition are disabled to preserve audit integrity.
    """
    list_display = (
        "action_badge",
        "performed_by",
        "student",
        "group",
        "short_description",
        "organization",
        "created_at",
    )
    list_filter = ("action", "organization")
    search_fields = (
        "performed_by__phone",
        "performed_by__first_name",
        "student__user__phone",
        "student__user__first_name",
        "group__name",
        "description",
    )
    readonly_fields = (
        "action",
        "performed_by",
        "student",
        "group",
        "description",
        "meta",
        "organization",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    fieldsets = (
        (_("Action"), {
            "fields": ("action", "organization", "created_at"),
        }),
        (_("Actors"), {
            "fields": ("performed_by", "student", "group"),
        }),
        (_("Details"), {
            "fields": ("description", "meta"),
        }),
    )

    # ── Disable all write operations — history is immutable ─────────────────
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Action"), ordering="action")
    def action_badge(self, obj):
        # Colour-code by action category
        action = obj.action
        if "STUDENT" in action:
            color = "#17a2b8"
        elif "PAYMENT" in action:
            color = "#28a745"
        elif "LESSON" in action:
            color = "#fd7e14"
        elif "GROUP" in action or "TEACHER" in action:
            color = "#6f42c1"
        else:
            color = "#6c757d"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:10px;font-weight:600;">{}</span>',
            color,
            obj.get_action_display(),
        )

    @admin.display(description=_("Description"))
    def short_description(self, obj):
        if obj.description:
            return obj.description[:60] + ("…" if len(obj.description) > 60 else "")
        return "—"

    def get_queryset(self, request):
        return History.all_objects.select_related(
            "performed_by", "student__user", "group__course", "organization"
        )

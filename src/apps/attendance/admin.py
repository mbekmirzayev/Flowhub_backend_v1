from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "lesson_date",
        "lesson_group",
        "status_badge",
        "marked_by",
        "organization",
        "created_at",
    )
    list_filter = ("status", "organization", "lesson__group__course")
    search_fields = (
        "student__user__phone",
        "student__user__first_name",
        "student__user__last_name",
        "lesson__group__name",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["mark_present", "mark_absent", "mark_excused"]

    fieldsets = (
        (_("Attendance Info"), {
            "fields": ("lesson", "student", "organization"),
        }),
        (_("Status"), {
            "fields": ("status", "marked_by"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Date"), ordering="lesson__date")
    def lesson_date(self, obj):
        return obj.lesson.date if obj.lesson else "—"

    @admin.display(description=_("Group"), ordering="lesson__group__name")
    def lesson_group(self, obj):
        return obj.lesson.group.name if obj.lesson else "—"

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        colors = {
            Attendance.Status.PRESENT: "#28a745",
            Attendance.Status.ABSENT: "#dc3545",
            Attendance.Status.EXCUSED: "#ffc107",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Mark selected as Present"))
    def mark_present(self, request, queryset):
        updated = queryset.update(status=Attendance.Status.PRESENT)
        self.message_user(request, _(f"{updated} record(s) marked as Present."))

    @admin.action(description=_("Mark selected as Absent"))
    def mark_absent(self, request, queryset):
        updated = queryset.update(status=Attendance.Status.ABSENT)
        self.message_user(request, _(f"{updated} record(s) marked as Absent."))

    @admin.action(description=_("Mark selected as Excused"))
    def mark_excused(self, request, queryset):
        updated = queryset.update(status=Attendance.Status.EXCUSED)
        self.message_user(request, _(f"{updated} record(s) marked as Excused."))

    def get_queryset(self, request):
        return Attendance.all_objects.select_related(
            "student__user",
            "lesson__group__course",
            "lesson__group__organization",
            "marked_by",
            "organization",
        )

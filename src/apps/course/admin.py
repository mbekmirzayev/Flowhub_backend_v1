from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.attendance.models import Attendance
from apps.course.models import Course, Group, GroupSchedule, Lesson


# ---------------------------------------------------------------------------
# Inline admins
# ---------------------------------------------------------------------------

class GroupScheduleInline(admin.TabularInline):
    model = GroupSchedule
    extra = 1
    fields = ("selected_days", "start_time", "end_time")
    verbose_name = _("Schedule")
    verbose_name_plural = _("Schedules")


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("date", "status", "teacher", "reason")
    readonly_fields = ()
    ordering = ("-date",)
    show_change_link = True
    verbose_name = _("Lesson")
    verbose_name_plural = _("Lessons")

    def get_queryset(self, request):
        return super().get_queryset(request).using("default").select_related("teacher__user", "group")


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ("student", "status", "marked_by")
    show_change_link = True
    verbose_name = _("Attendance")
    verbose_name_plural = _("Attendance Records")


# ---------------------------------------------------------------------------
# Course Admin
# ---------------------------------------------------------------------------

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "duration",
        "lesson_count",
        "price",
        "organization",
        "slug",
        "created_at",
    )
    list_filter = ("category", "organization")
    search_fields = ("title", "slug", "category__name")
    filter_horizontal = ("teacher",)
    readonly_fields = ("slug", "created_at", "updated_at")
    ordering = ("title",)

    fieldsets = (
        (_("Course Info"), {
            "fields": ("title", "slug", "category", "organization"),
        }),
        (_("Details"), {
            "fields": ("teacher", "duration", "lesson_count", "price"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ---------------------------------------------------------------------------
# Group Admin
# ---------------------------------------------------------------------------

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "course",
        "teacher",
        "status_badge",
        "start_date",
        "organization",
        "created_at",
    )
    list_filter = ("status", "organization", "course")
    search_fields = ("name", "course__title", "teacher__user__first_name", "teacher__user__last_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [GroupScheduleInline, LessonInline]
    actions = ["close_groups", "activate_groups"]

    fieldsets = (
        (_("Group Info"), {
            "fields": ("name", "course", "teacher", "organization"),
        }),
        (_("Status & Dates"), {
            "fields": ("status", "start_date"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        if obj.status == Group.Status.ACTIVE:
            return format_html(
                '<span style="background:#28a745;color:#fff;padding:2px 10px;'
                'border-radius:12px;font-size:11px;">● Active</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;">● Closed</span>'
        )

    @admin.action(description=_("Close selected groups"))
    def close_groups(self, request, queryset):
        updated = queryset.update(status=Group.Status.CLOSED)
        self.message_user(request, _(f"{updated} group(s) closed."))

    @admin.action(description=_("Activate selected groups"))
    def activate_groups(self, request, queryset):
        updated = queryset.update(status=Group.Status.ACTIVE)
        self.message_user(request, _(f"{updated} group(s) activated."))

    def get_queryset(self, request):
        return Group.all_objects.select_related(
            "course", "teacher__user", "organization"
        )


# ---------------------------------------------------------------------------
# GroupSchedule Admin
# ---------------------------------------------------------------------------

@admin.register(GroupSchedule)
class GroupScheduleAdmin(admin.ModelAdmin):
    list_display = ("group", "selected_days", "start_time", "end_time")
    list_filter = ("group__organization", "group__status")
    search_fields = ("group__name", "group__course__title")
    ordering = ("group__name",)

    def get_queryset(self, request):
        return GroupSchedule.all_objects.select_related("group__course", "group__organization")


# ---------------------------------------------------------------------------
# Lesson Admin
# ---------------------------------------------------------------------------

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "date",
        "status_badge",
        "teacher",
        "reason",
    )
    list_filter = ("status", "group__organization", "group__course")
    search_fields = ("group__name", "group__course__title", "teacher__user__first_name")
    readonly_fields = ("id",)
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [AttendanceInline]

    fieldsets = (
        (_("Lesson Info"), {
            "fields": ("group", "teacher", "date"),
        }),
        (_("Status"), {
            "fields": ("status", "reason"),
        }),
    )

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        colors = {
            Lesson.Status.PLANNED: "#17a2b8",
            Lesson.Status.COMPLETED: "#28a745",
            Lesson.Status.CANCELLED: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    def get_queryset(self, request):
        return Lesson.all_objects.select_related(
            "group__course", "group__organization", "teacher__user"
        )

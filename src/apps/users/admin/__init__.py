from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.users.models import User, StaffProfile, StudentProfile, TeacherProfile


# ---------------------------------------------------------------------------
# Inline admins for profiles inside UserAdmin
# ---------------------------------------------------------------------------

class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name = _("Staff Profile")
    verbose_name_plural = _("Staff Profile")
    extra = 0
    fields = ("salary", "is_active", "is_deleted")
    readonly_fields = ("is_deleted",)


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name = _("Student Profile")
    verbose_name_plural = _("Student Profile")
    extra = 0
    fields = ("parent_phone", "status", "is_active", "is_deleted")
    readonly_fields = ("is_deleted",)


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name = _("Teacher Profile")
    verbose_name_plural = _("Teacher Profile")
    extra = 0
    fields = ("subject", "work_type", "salary_type", "salary", "is_active", "is_deleted")
    readonly_fields = ("is_deleted",)


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "phone",
        "full_name",
        "email",
        "role_badge",
        "organization",
        "is_active",
        "is_deleted",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_deleted", "is_staff", "is_superuser", "organization")
    search_fields = ("phone", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "id")
    actions = ["soft_delete_users", "restore_users"]

    # Override BaseUserAdmin fieldsets to use 'phone' instead of 'username'
    fieldsets = (
        (_("Authentication"), {
            "fields": ("phone", "password"),
        }),
        (_("Personal Info"), {
            "fields": ("first_name", "last_name", "email"),
        }),
        (_("Role & Organization"), {
            "fields": ("role", "organization"),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        (_("Soft Delete"), {
            "fields": ("is_deleted",),
        }),
        (_("Important Dates"), {
            "fields": ("date_joined", "last_login"),
            "classes": ("collapse",),
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "password1", "password2", "role", "organization"),
        }),
    )

    def get_inlines(self, request, obj=None):
        """Dynamically show the relevant profile inline based on role."""
        if obj is None:
            return []
        role_to_inline = {
            User.Status.ADMIN: [StaffProfileInline],
            User.Status.MANAGER: [StaffProfileInline],
            User.Status.GLOBAL_ADMIN: [StaffProfileInline],
            User.Status.TEACHER: [TeacherProfileInline],
            User.Status.STUDENT: [StudentProfileInline],
        }
        return role_to_inline.get(obj.role, [])

    @admin.display(description=_("Full Name"), ordering="first_name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description=_("Role"), ordering="role")
    def role_badge(self, obj):
        colors = {
            User.Status.GLOBAL_ADMIN: "#6f42c1",
            User.Status.ADMIN: "#007bff",
            User.Status.MANAGER: "#17a2b8",
            User.Status.TEACHER: "#fd7e14",
            User.Status.STUDENT: "#28a745",
        }
        color = colors.get(obj.role, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:600;">{}</span>',
            color,
            obj.get_role_display(),
        )

    @admin.action(description=_("Soft-delete selected users"))
    def soft_delete_users(self, request, queryset):
        count = 0
        for user in queryset.filter(is_deleted=False):
            user.soft_delete()
            count += 1
        self.message_user(request, _(f"{count} user(s) soft-deleted."))

    @admin.action(description=_("Restore selected soft-deleted users"))
    def restore_users(self, request, queryset):
        updated = queryset.update(is_deleted=False, is_active=True)
        self.message_user(request, _(f"{updated} user(s) restored."))


# ---------------------------------------------------------------------------
# Standalone profile admins
# ---------------------------------------------------------------------------

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "user_phone", "user_role", "salary", "is_active", "is_deleted", "created_at")
    list_filter = ("is_active", "is_deleted", "user__role", "organization")
    search_fields = ("user__phone", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at", "is_deleted")
    ordering = ("-created_at",)

    fieldsets = (
        (_("User"), {"fields": ("user", "organization")}),
        (_("Employment"), {"fields": ("salary", "is_active", "is_deleted")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Phone"), ordering="user__phone")
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Role"), ordering="user__role")
    def user_role(self, obj):
        return obj.user.get_role_display()


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "user_phone", "parent_phone", "status_badge",
        "is_active", "is_deleted", "organization", "created_at"
    )
    list_filter = ("status", "is_active", "is_deleted", "organization")
    search_fields = ("user__phone", "user__first_name", "user__last_name", "parent_phone")
    readonly_fields = ("created_at", "updated_at", "is_deleted")
    ordering = ("-created_at",)

    fieldsets = (
        (_("User"), {"fields": ("user", "organization")}),
        (_("Student Info"), {"fields": ("parent_phone", "status")}),
        (_("Status"), {"fields": ("is_active", "is_deleted")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Phone"), ordering="user__phone")
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        colors = {
            StudentProfile.StudentStatus.ACTIVE: "#28a745",
            StudentProfile.StudentStatus.FROZEN: "#17a2b8",
            StudentProfile.StudentStatus.GRADUATED: "#6f42c1",
            StudentProfile.StudentStatus.DROPPED: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "user_phone", "subject", "work_type", "salary_type",
        "salary", "is_active", "is_deleted", "created_at"
    )
    list_filter = ("work_type", "salary_type", "is_active", "is_deleted", "organization")
    search_fields = ("user__phone", "user__first_name", "user__last_name", "subject")
    readonly_fields = ("created_at", "updated_at", "is_deleted")
    ordering = ("-created_at",)

    fieldsets = (
        (_("User"), {"fields": ("user", "organization")}),
        (_("Teaching Info"), {"fields": ("subject", "work_type")}),
        (_("Salary"), {"fields": ("salary_type", "salary")}),
        (_("Status"), {"fields": ("is_active", "is_deleted")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Phone"), ordering="user__phone")
    def user_phone(self, obj):
        return obj.user.phone

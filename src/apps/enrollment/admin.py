from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.enrollment.models import Enrollment
from apps.payment.models import Payment


# ---------------------------------------------------------------------------
# Payment inline inside Enrollment
# ---------------------------------------------------------------------------

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("amount", "payment_date", "payment_type", "status", "for_month", "received_by")
    readonly_fields = ("payment_date",)
    show_change_link = True
    verbose_name = _("Payment")
    verbose_name_plural = _("Payments")


# ---------------------------------------------------------------------------
# Enrollment Admin
# ---------------------------------------------------------------------------

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "group",
        "status_badge",
        "left_at",
        "created_at",
    )
    list_filter = ("status", "group__organization", "group__course")
    search_fields = (
        "student__user__phone",
        "student__user__first_name",
        "student__user__last_name",
        "group__name",
        "group__course__title",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [PaymentInline]
    actions = ["drop_enrollments", "finish_enrollments", "reactivate_enrollments"]

    fieldsets = (
        (_("Enrollment Info"), {
            "fields": ("student", "group"),
        }),
        (_("Status"), {
            "fields": ("status", "left_at"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        colors = {
            Enrollment.Status.ACTIVE: "#28a745",
            Enrollment.Status.DROPPED: "#dc3545",
            Enrollment.Status.FINISHED: "#6f42c1",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Drop selected enrollments"))
    def drop_enrollments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status=Enrollment.Status.DROPPED, left_at=timezone.now().date())
        self.message_user(request, _(f"{updated} enrollment(s) dropped."))

    @admin.action(description=_("Finish selected enrollments"))
    def finish_enrollments(self, request, queryset):
        updated = queryset.update(status=Enrollment.Status.FINISHED)
        self.message_user(request, _(f"{updated} enrollment(s) marked as finished."))

    @admin.action(description=_("Reactivate selected enrollments"))
    def reactivate_enrollments(self, request, queryset):
        updated = queryset.update(status=Enrollment.Status.ACTIVE, left_at=None)
        self.message_user(request, _(f"{updated} enrollment(s) reactivated."))

    def get_queryset(self, request):
        return Enrollment.all_objects.select_related(
            "student__user", "group__course", "group__organization"
        )

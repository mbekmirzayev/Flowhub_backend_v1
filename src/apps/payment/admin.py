from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.payment.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "amount_display",
        "payment_type_badge",
        "status_badge",
        "payment_date",
        "for_month",
        "due_date",
        "received_by",
        "organization",
    )
    list_filter = ("status", "payment_type", "organization", "for_month")
    search_fields = (
        "student__user__phone",
        "student__user__first_name",
        "student__user__last_name",
        "received_by__phone",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "payment_date"
    ordering = ("-payment_date",)
    actions = ["mark_as_paid", "mark_as_overdue", "export_total_summary"]

    fieldsets = (
        (_("Student & Enrollment"), {
            "fields": ("student", "enrollment", "organization"),
        }),
        (_("Payment Details"), {
            "fields": ("amount", "payment_type", "payment_date", "for_month", "due_date"),
        }),
        (_("Status & Receiver"), {
            "fields": ("status", "received_by"),
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Amount"), ordering="amount")
    def amount_display(self, obj):
        return format_html(
            '<strong style="color:#28a745;">{:,.0f} UZS</strong>',
            obj.amount,
        )

    @admin.display(description=_("Payment Type"), ordering="payment_type")
    def payment_type_badge(self, obj):
        colors = {
            Payment.PaymentType.CASH: "#6c757d",
            Payment.PaymentType.CARD: "#007bff",
            Payment.PaymentType.CLICK: "#17a2b8",
        }
        color = colors.get(obj.payment_type, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_payment_type_display(),
        )

    @admin.display(description=_("Status"), ordering="status")
    def status_badge(self, obj):
        colors = {
            Payment.Status.PAID: "#28a745",
            Payment.Status.PENDING: "#ffc107",
            Payment.Status.OVERDUE: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description=_("Mark selected payments as Paid"))
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status=Payment.Status.PAID)
        self.message_user(request, _(f"{updated} payment(s) marked as PAID."))

    @admin.action(description=_("Mark selected payments as Overdue"))
    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status=Payment.Status.OVERDUE)
        self.message_user(request, _(f"{updated} payment(s) marked as OVERDUE."))

    @admin.action(description=_("Show total for selected payments"))
    def export_total_summary(self, request, queryset):
        total = queryset.aggregate(total=Sum("amount"))["total"] or 0
        self.message_user(
            request,
            _(f"Total amount for selected {queryset.count()} payment(s): {total:,.0f} UZS"),
        )

    def get_queryset(self, request):
        return Payment.all_objects.select_related(
            "student__user", "enrollment__group", "received_by", "organization"
        )

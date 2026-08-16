from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantBaseModel, CreateBaseModel
from apps.enrollment.models import Enrollment
from apps.users.models import StudentProfile, User


class Payment(TenantBaseModel, CreateBaseModel):
    """
    Records a single payment transaction from a student.

    Key design decisions vs the original model:
    - `enrollment` FK anchors the payment to a specific group/course, allowing
      correct financial tracking when a student is in multiple groups.
    - `payment_date` is now a manual DateField (was auto_now_add DateTimeField),
      allowing staff to record past or back-dated payments.
    - `due_date` enables upcoming-payment tracking (requirement #3).
    - `for_month` identifies which calendar month this payment covers, supporting
      monthly-tuition workflows common in educational centres.
    - `received_by` records which staff member registered the payment — critical
      for audit trails in a CRM.
    """

    class PaymentType(models.TextChoices):
        CASH = 'cash', _('Cash')
        CARD = 'card', _('Card')
        CLICK = 'click', _('Click/Payme')

    class Status(models.TextChoices):
        PAID = 'paid', _('Paid')
        PENDING = 'pending', _('Pending')
        OVERDUE = 'overdue', _('Overdue')

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Student'),
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('Enrollment'),
        help_text=_('The specific group/course enrollment this payment is for.'),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Amount'),
    )
    payment_date = models.DateField(
        verbose_name=_('Payment date'),
        help_text=_('The actual date of payment. Can be manually set to a past date.'),
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Due date'),
        help_text=_('The deadline by which this payment is expected.'),
    )
    for_month = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('For month'),
        help_text=_('The first day of the month this payment covers (e.g. 2026-09-01).'),
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        verbose_name=_('Payment type'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_payments',
        verbose_name=_('Received by'),
        help_text=_('Staff member who recorded this payment.'),
    )

    class Meta:
        db_table = 'payments'
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['student'], name='payment_student_idx'),
            models.Index(fields=['status'], name='payment_status_idx'),
            models.Index(fields=['due_date'], name='payment_due_date_idx'),
            models.Index(fields=['for_month'], name='payment_for_month_idx'),
        ]

    def __str__(self):
        return f"{self.student} — {self.amount} — {self.payment_date}"

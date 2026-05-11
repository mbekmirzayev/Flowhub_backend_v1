from django.db.models import TextChoices, SET_NULL, ForeignKey
from django.db.models.fields import DecimalField, CharField, DateField, DateTimeField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import CreateBaseModel
from apps.course.models import Course, Group
from apps.users.models import StudentProfile


class Payment(CreateBaseModel):
    class Status(TextChoices):
        PAID = 'paid', _('Paid')
        UNPAID = 'unpaid', _('Unpaid')
        PARTIAL = 'partial', _('Partial')
        OVERDUE = 'overdue', _('Overdue')

    class PaymentMethod(TextChoices):
        CASH = 'cash', _('Naqd')
        CARD = 'card', _('Plastik karta')
        TRANSFER = 'transfer', _('Bank o‘tkazmasi')

    student = ForeignKey(StudentProfile, SET_NULL, null=True, related_name='payments')
    course = ForeignKey(Course, SET_NULL, null=True, related_name='payments')
    group = ForeignKey(Group, SET_NULL, null=True, related_name='payments')

    total_amount = DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Umumiy summa"))
    paid_amount = DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("To‘langan summa"))

    status = CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    payment_method = CharField(max_length=20, choices=PaymentMethod.choices, null=True, blank=True)

    due_date = DateField(null=True, blank=True, verbose_name=_("To‘lov muddati"))
    paid_at = DateTimeField(null=True, blank=True, verbose_name=_("To‘langan vaqti"))

    def __str__(self):
        return f"{self.student} - {self.total_amount} ({self.status})"

    def save(self, *args, **kwargs):
        paid = self.paid_amount or 0
        total = self.total_amount or 0

        if paid >= total:
            self.status = self.Status.PAID
            if not self.paid_at:
                self.paid_at = timezone.now()
            elif paid > 0:
                self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.UNPAID
        super().save(*args, **kwargs)

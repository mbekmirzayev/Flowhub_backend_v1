from rest_framework.fields import CharField
from rest_framework.serializers import ModelSerializer

from apps.payment.models import Payment


class PaymentGetSerializer(ModelSerializer):
    """
    Read serializer for Payment — exposes all financial context fields.
    """
    id = CharField(read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id',
            'student',
            'enrollment',
            'amount',
            'payment_date',
            'due_date',
            'for_month',
            'payment_type',
            'status',
            'received_by',
            'organization',
            'created_at',
        )


class PaymentPostSerializer(ModelSerializer):
    """
    Write serializer for Payment.

    Staff must now supply:
    - `student`       — who is paying
    - `enrollment`    — which group/course this payment is for (optional but recommended)
    - `amount`        — payment amount
    - `payment_date`  — actual date of payment (can be backdated)
    - `due_date`      — when was/is payment expected (optional)
    - `for_month`     — first day of the month this covers, e.g. 2026-09-01 (optional)
    - `payment_type`  — cash / card / click
    - `status`        — paid / pending / overdue

    `received_by` is set automatically in the view from request.user.
    """

    class Meta:
        model = Payment
        fields = (
            'student',
            'enrollment',
            'amount',
            'payment_date',
            'due_date',
            'for_month',
            'payment_type',
            'status',
        )

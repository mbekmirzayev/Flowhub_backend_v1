from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from api.payment.serializers.payment import PaymentGetSerializer, PaymentPostSerializer
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.history.services.writer import log_payment_done
from apps.payment.models import Payment


@extend_schema(tags=["Payment"])
class PaymentModelViewSet(ModelViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'enrollment', 'payment_type', 'status', 'for_month']
    ordering_fields = ['payment_date', 'due_date', 'amount', 'created_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return Payment.objects.all().select_related(
                'student', 'enrollment', 'organization', 'received_by'
            )

        if user.is_local_admin or user.is_manager:
            return Payment.objects.filter(
                organization=user.organization
            ).select_related('student', 'enrollment', 'received_by')

        return Payment.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PaymentGetSerializer
        return PaymentPostSerializer

    def perform_create(self, serializer):
        """
        Fix #3: Saves the payment and immediately writes PAYMENT_DONE to the
        immutable History log.  `log_payment_done` is defined in
        `apps/history/services/writer.py` and follows the same pattern as
        log_student_joined, log_lesson_completed, etc.
        """
        user = self.request.user
        if user.is_global_admin:
            # Global admin must supply organization via the serializer/body
            payment = serializer.save(received_by=user)
        else:
            payment = serializer.save(
                organization=user.organization,
                received_by=user,
            )

        # Write audit entry — only when a payment is actually PAID.
        # PENDING / OVERDUE records are not yet real payments, so we
        # log them only once they are confirmed.
        if payment.status == Payment.Status.PAID:
            log_payment_done(
                performed_by=user,
                student=payment.student,
                organization=payment.organization,
                payment=payment,
            )

    def perform_update(self, serializer):
        """
        Write PAYMENT_DONE to History when a pending payment is updated
        to PAID status (e.g. staff confirms a previously pending payment).
        Avoids duplicate history entries by checking whether the status
        is *changing* to PAID rather than simply already being PAID.
        """
        previous_status = self.get_object().status
        payment = serializer.save()

        status_changed_to_paid = (
            previous_status != Payment.Status.PAID
            and payment.status == Payment.Status.PAID
        )
        if status_changed_to_paid:
            log_payment_done(
                performed_by=self.request.user,
                student=payment.student,
                organization=payment.organization,
                payment=payment,
            )

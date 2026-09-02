from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.enrollment.serializers.enrollment import (
    EnrollmentGetSerializer,
    EnrollmentPostSerializer,
    TransferSerializer,
    DropoutSerializer,
    LeaveSerializer,
)
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager
from apps.enrollment.models import Enrollment
from apps.enrollment.services.lifecycle import (
    enroll_student,
    transfer_student,
    graduate_student,
    dropout_student,
    leave_student,
)


@extend_schema(tags=["Enrollment"])
class EnrollmentModelViewSet(ModelViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'group', 'status']
    ordering_fields = ['created_at', 'left_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_global_admin:
            return Enrollment.all_objects.all().select_related('student', 'group')
        if user.is_local_admin or user.is_manager:
            return Enrollment.objects.all().select_related('student', 'group')
        return Enrollment.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return EnrollmentGetSerializer
        if self.action == 'transfer':
            return TransferSerializer
        if self.action == 'dropout':
            return DropoutSerializer
        if self.action == 'leave':
            return LeaveSerializer
        return EnrollmentPostSerializer

    def perform_create(self, serializer):
        """Use the service layer so History is written on enrollment."""
        user = self.request.user
        org = user.organization if not user.is_global_admin else \
            serializer.validated_data['group'].organization
        try:
            enroll_student(
                student=serializer.validated_data['student'],
                group=serializer.validated_data['group'],
                performed_by=user,
                organization=org,
            )
        except ValueError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': str(e)})

    # ------------------------------------------------------------------
    # Lifecycle actions
    # ------------------------------------------------------------------

    @extend_schema(
        summary="Transfer student to another group",
        description=(
            "Closes the current enrollment (status=DROPPED, left_at=today) "
            "and creates a new ACTIVE enrollment in the target group. "
            "Writes STUDENT_TRANSFERRED to History."
        ),
        responses={
            200: OpenApiResponse(description="Transfer completed."),
            400: OpenApiResponse(description="Same group or student already enrolled."),
        },
    )
    @action(detail=True, methods=['patch'], url_path='transfer')
    def transfer(self, request, pk=None):
        enrollment = self.get_object()
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        to_group = serializer.validated_data['to_group']
        reason = serializer.validated_data.get('reason', '')
        org = request.user.organization if not request.user.is_global_admin \
            else enrollment.group.organization

        try:
            new_enrollment = transfer_student(
                enrollment=enrollment,
                to_group=to_group,
                performed_by=request.user,
                organization=org,
                reason=reason,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Student transferred.',
            'new_enrollment': EnrollmentGetSerializer(new_enrollment).data,
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Graduate student",
        description=(
            "Marks the enrollment as FINISHED, sets StudentProfile.status=GRADUATED, "
            "and writes STUDENT_GRADUATED to History."
        ),
        responses={200: OpenApiResponse(description="Student graduated.")},
    )
    @action(detail=True, methods=['patch'], url_path='graduate')
    def graduate(self, request, pk=None):
        enrollment = self.get_object()
        org = request.user.organization if not request.user.is_global_admin \
            else enrollment.group.organization

        graduate_student(
            enrollment=enrollment,
            performed_by=request.user,
            organization=org,
        )
        return Response(
            {'detail': 'Student graduated successfully.'},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Mark student as dropped out",
        description=(
            "Closes the enrollment (status=DROPPED), sets StudentProfile.status=DROPPED, "
            "and writes STUDENT_DROPPED to History."
        ),
        responses={200: OpenApiResponse(description="Dropout recorded.")},
    )
    @action(detail=True, methods=['patch'], url_path='dropout')
    def dropout(self, request, pk=None):
        enrollment = self.get_object()
        serializer = DropoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        org = request.user.organization if not request.user.is_global_admin \
            else enrollment.group.organization

        dropout_student(
            enrollment=enrollment,
            performed_by=request.user,
            organization=org,
            reason=reason,
        )
        return Response(
            {'detail': 'Student marked as dropped out.'},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Student voluntarily leaves a group",
        description=(
            "Closes the enrollment (status=DROPPED, left_at=today) but does **not** "
            "change `StudentProfile.status`. Use this when a student exits a single "
            "group while remaining active in the system (e.g. still enrolled elsewhere "
            "or likely to re-enroll).\n\n"
            "Use `/dropout` instead when the student is permanently leaving the programme."
        ),
        responses={
            200: OpenApiResponse(description="Student left the group."),
            400: OpenApiResponse(description="Enrollment is not ACTIVE."),
        },
    )
    @action(detail=True, methods=['patch'], url_path='leave')
    def leave(self, request, pk=None):
        """Fix #5: triggers STUDENT_LEFT History event."""
        enrollment = self.get_object()
        serializer = LeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        org = request.user.organization if not request.user.is_global_admin \
            else enrollment.group.organization

        try:
            leave_student(
                enrollment=enrollment,
                performed_by=request.user,
                organization=org,
                reason=reason,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'detail': 'Student has left the group.'},
            status=status.HTTP_200_OK,
        )

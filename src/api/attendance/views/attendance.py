from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.attendance.serializers.attendance import (
    AttendanceGetSerializer,
    AttendancePostSerializer,
    BulkAttendanceSerializer,
)
from apps.attendance.models import Attendance
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager, IsTeacher
from apps.course.models.lesson import Lesson


@extend_schema(tags=["Attendance"])
class AttendanceModelViewSet(ModelViewSet):
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lesson', 'student', 'status']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action == 'bulk_mark':
            # Fix #2: Python `or` on two truthy objects always returns the first.
            # DRF's bitwise `|` creates a real composite permission that grants
            # access when EITHER class returns True.
            return [IsAdminOrManager() or IsTeacher()]
        return [IsAdminOrManager()]

    def get_queryset(self):
        user = self.request.user

        if user.is_global_admin:
            return Attendance.all_objects.all().select_related(
                'lesson', 'lesson__group', 'student', 'marked_by'
            )

        if user.is_local_admin or user.is_manager:
            return Attendance.objects.filter(
                organization=user.organization
            ).select_related('lesson', 'lesson__group', 'student', 'marked_by')

        if user.is_teacher:
            # Teachers see attendance only for their groups
            return Attendance.objects.filter(
                lesson__group__teacher__user=user
            ).select_related('lesson', 'lesson__group', 'student')

        return Attendance.objects.none()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AttendanceGetSerializer
        if self.action == 'bulk_mark':
            return BulkAttendanceSerializer
        return AttendancePostSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_global_admin:
            serializer.save(marked_by=user)
        else:
            serializer.save(marked_by=user, organization=user.organization)

    @extend_schema(
        summary="Bulk mark attendance for a completed lesson",
        description=(
                "Updates attendance status for multiple students in a single request. "
                "Only records for the given lesson are affected. "
                "Records that already exist are updated; new ones are created if missing.\n\n"
                "**Typical workflow:**\n"
                "1. Teacher calls `PATCH /lesson/<id>/complete` → attendance auto-created (ABSENT)\n"
                "2. Teacher calls `POST /attendance/bulk-mark` → marks present/excused students\n"
                "3. Everyone NOT in the payload stays ABSENT"
        ),
        responses={
            200: OpenApiResponse(description="Attendance records updated."),
            400: OpenApiResponse(description="Validation error."),
            404: OpenApiResponse(description="Lesson not found."),
        },
    )
    @action(detail=False, methods=['post'], url_path='bulk-mark')
    def bulk_mark(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lesson_id = serializer.validated_data['lesson_id']
        records = serializer.validated_data['records']

        # Resolve and permission-check the lesson
        user = request.user
        if user.is_global_admin:
            lesson = get_object_or_404(Lesson.all_objects, pk=lesson_id)
        elif user.is_teacher:
            lesson = get_object_or_404(
                Lesson.objects,
                pk=lesson_id,
                group__teacher__user=user,
            )
        else:
            lesson = get_object_or_404(
                Lesson.objects,
                pk=lesson_id,
                group__organization=user.organization,
            )

        if lesson.status != Lesson.Status.COMPLETED:
            return Response(
                {'detail': 'Attendance can only be marked for COMPLETED lessons.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        org = lesson.group.organization

        # Bulk-update: update_or_create for each record
        updated, created = 0, 0
        for item in records:
            student_id = item['student_id']
            att_status = item['status']

            obj, was_created = Attendance.objects.update_or_create(
                lesson=lesson,
                student_id=student_id,
                defaults={
                    'status': att_status,
                    'marked_by': user,
                    'organization': org,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response({
            'detail': 'Attendance updated.',
            'lesson_id': lesson_id,
            'records_updated': updated,
            'records_created': created,
        }, status=status.HTTP_200_OK)

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.common.serializers import TenantBaseModelViewSet
from api.course.serializers.lesson import (
    LessonGetSerializer,
    LessonPostSerializer,
    LessonCompleteSerializer,
    LessonCancelSerializer,
)
from apps.common.paginations import CustomPageNumberPagination
from apps.common.permissions import IsAdminOrManager, IsTeacher
from apps.course.models.lesson import Lesson
from apps.course.services.lesson_lifecycle import complete_lesson, cancel_lesson


@extend_schema(tags=["Lesson"])
class LessonModelViewSet(TenantBaseModelViewSet):
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user
        group_id = self.kwargs.get('group_id')

        if user.is_global_admin:
            qs = Lesson.all_objects.all()
        elif user.is_local_admin or user.is_manager:
            qs = Lesson.objects.filter(group__organization=user.organization)
        elif user.is_teacher:
            # Teachers can see their own groups' lessons
            qs = Lesson.objects.filter(
                group__teacher__user=user
            )
        else:
            return Lesson.objects.none()

        if group_id:
            qs = qs.filter(group_id=group_id)

        return qs.select_related('group', 'teacher__user')

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonGetSerializer
        if self.action == 'complete':
            return LessonCompleteSerializer
        if self.action == 'cancel':
            return LessonCancelSerializer
        return LessonPostSerializer

    def get_permissions(self):
        if self.action in ['complete', 'cancel']:
            return [IsAdminOrManager() | IsTeacher()]
        return [IsAdminOrManager()]

    @extend_schema(
        summary="Mark a lesson as COMPLETED",
        description=(
                "Transitions a PLANNED lesson to COMPLETED and automatically creates "
                "Attendance records (status=ABSENT) for all active enrolled students. "
                "Staff/Teacher then calls the bulk-attendance endpoint to mark present/excused."
        ),
        responses={
            200: OpenApiResponse(description="Lesson completed, attendance records created."),
            400: OpenApiResponse(description="Lesson is not in PLANNED state."),
        },
    )
    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, **kwargs):
        lesson = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        teacher_profile = serializer.validated_data.get('teacher')
        org = request.user.organization if not request.user.is_global_admin else lesson.group.organization

        try:
            lesson, attendances = complete_lesson(
                lesson=lesson,
                performed_by=request.user,
                organization=org,
                teacher_profile=teacher_profile,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Lesson marked as completed.',
            'lesson': LessonGetSerializer(lesson).data,
            'attendance_records_created': len(attendances),
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancel a lesson",
        description=(
                "Transitions a PLANNED lesson to CANCELLED. A reason is required. "
                "No attendance records are created for cancelled lessons."
        ),
        responses={
            200: OpenApiResponse(description="Lesson cancelled."),
            400: OpenApiResponse(description="Lesson is not in PLANNED state or reason missing."),
        },
    )
    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, **kwargs):
        lesson = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data.get('reason', '')
        org = request.user.organization if not request.user.is_global_admin else lesson.group.organization

        try:
            lesson = cancel_lesson(
                lesson=lesson,
                reason=reason,
                performed_by=request.user,
                organization=org,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'detail': 'Lesson cancelled.',
            'lesson': LessonGetSerializer(lesson).data,
        }, status=status.HTTP_200_OK)

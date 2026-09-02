from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.enrollment.serializers.enrollment import FreezeSerializer
from apps.common.permissions import IsAdminOrManager
from apps.enrollment.services.lifecycle import freeze_student, unfreeze_student
from apps.users.models import StudentProfile


@extend_schema(tags=["Students"])
class StudentFreezeAPIView(APIView):
    """
    POST /student/<uuid>/freeze
    Freeze a student's account. They stay enrolled but won't receive attendance records.
    """
    permission_classes = (IsAdminOrManager,)

    @extend_schema(
        summary="Freeze a student",
        responses={
            200: OpenApiResponse(description="Student frozen."),
            400: OpenApiResponse(description="Student is already frozen."),
        },
    )
    def post(self, request, pk):
        student = _get_student(pk, request.user)
        serializer = FreezeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason', '')
        org = request.user.organization if not request.user.is_global_admin \
            else student.organization

        try:
            freeze_student(
                student=student,
                performed_by=request.user,
                organization=org,
                reason=reason,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Student frozen.'}, status=status.HTTP_200_OK)


@extend_schema(tags=["Students"])
class StudentUnfreezeAPIView(APIView):
    """
    POST /student/<uuid>/unfreeze
    Restore a frozen student to ACTIVE status.
    """
    permission_classes = (IsAdminOrManager,)

    @extend_schema(
        summary="Unfreeze a student",
        responses={
            200: OpenApiResponse(description="Student unfrozen."),
            400: OpenApiResponse(description="Student is not frozen."),
        },
    )
    def post(self, request, pk):
        student = _get_student(pk, request.user)
        org = request.user.organization if not request.user.is_global_admin \
            else student.organization

        try:
            unfreeze_student(
                student=student,
                performed_by=request.user,
                organization=org,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Student unfrozen.'}, status=status.HTTP_200_OK)


def _get_student(pk, user) -> StudentProfile:
    from django.shortcuts import get_object_or_404
    if user.is_global_admin:
        return get_object_or_404(StudentProfile.all_objects, pk=pk)
    return get_object_or_404(StudentProfile.objects, pk=pk, organization=user.organization)

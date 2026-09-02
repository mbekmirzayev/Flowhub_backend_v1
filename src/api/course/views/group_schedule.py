from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.viewsets import ModelViewSet

from api.course.serializers.group_schedule import GroupScheduleSerializer
from apps.common.permissions import IsAdminOrManager
from apps.course.models import Group
from apps.course.models.group_schedule import GroupSchedule


@extend_schema(tags=["Group Schedule"])
class GroupScheduleModelViewSet(ModelViewSet):
    serializer_class = GroupScheduleSerializer
    permission_classes = (IsAdminOrManager,)

    def get_queryset(self):
        user = self.request.user
        group_id = self.kwargs.get('group_id')

        if user.is_global_admin:
            qs = GroupSchedule.all_objects.all()
        elif user.is_local_admin or user.is_manager:
            qs = GroupSchedule.objects.filter(group__organization=user.organization)
        else:
            return GroupSchedule.objects.none()

        if group_id:
            qs = qs.filter(group_id=group_id)

        return qs.select_related('group')

    def perform_create(self, serializer):
        group_id = self.kwargs.get('group_id')
        user = self.request.user

        try:
            if user.is_global_admin:
                group = Group.all_objects.get(pk=group_id)
            else:
                group = Group.objects.filter(organization=user.organization).get(pk=group_id)
        except Group.DoesNotExist:
            raise NotFound('Guruh topilmadi yoki sizga tegishli emas.')

        serializer.save(group=group)

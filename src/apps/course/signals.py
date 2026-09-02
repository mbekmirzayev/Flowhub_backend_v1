import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.course.models.group_schedule import GroupSchedule

logger = logging.getLogger(__name__)


@receiver(post_save, sender=GroupSchedule)
def on_group_schedule_saved(sender, instance: GroupSchedule, created: bool, **kwargs):
    """
    When a GroupSchedule is created or updated, regenerate future lessons.

    - On CREATE: generate lessons from group.start_date for 6 months.
    - On UPDATE: delete future PLANNED lessons and regenerate from today.
    """
    from apps.course.services.lesson_generator import (
        generate_lessons_for_group,
        regenerate_lessons_after_schedule_change,
    )

    group = instance.group
    try:
        if created:
            count = len(generate_lessons_for_group(group=group))
            logger.info(
                "Auto-generated %d lessons for group '%s' after schedule creation.",
                count, group.name,
            )
        else:
            count = len(regenerate_lessons_after_schedule_change(group=group))
            logger.info(
                "Regenerated %d future lessons for group '%s' after schedule update.",
                count, group.name,
            )
    except Exception as exc:
        # Never crash the schedule save — log and continue.
        logger.error(
            "Failed to generate lessons for group '%s': %s", group.name, exc
        )

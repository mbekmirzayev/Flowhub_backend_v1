"""
Lesson Generation Service
=========================
Generates `Lesson` records from a Group's `GroupSchedule` blueprint.

This service is the bridge between the "what days does this group meet"
(GroupSchedule) and the "here is the actual class that happened on Monday"
(Lesson).

Usage:
    from apps.course.services.lesson_generator import generate_lessons_for_group
    generate_lessons_for_group(group, end_date=date(2026, 12, 31))

Called automatically by:
    - Django post_save signal on GroupSchedule (create / update)
    - Manually via management command: manage.py generate_lessons --group <uuid>
"""
import datetime
from typing import Optional

from django.db import transaction

from apps.course.models import Group
from apps.course.models.group_schedule import GroupSchedule
from apps.course.models.lesson import Lesson

# Maps GroupSchedule.DAYS values to Python weekday integers (Monday=0, Sunday=6)
_DAY_TO_WEEKDAY = {
    GroupSchedule.DAYS.MONDAY: 0,
    GroupSchedule.DAYS.TUESDAY: 1,
    GroupSchedule.DAYS.WEDNESDAY: 2,
    GroupSchedule.DAYS.THURSDAY: 3,
    GroupSchedule.DAYS.FRIDAY: 4,
    GroupSchedule.DAYS.SATURDAY: 5,
    GroupSchedule.DAYS.SUNDAY: 6,
}


def generate_lessons_for_group(
    group: Group,
    end_date: Optional[datetime.date] = None,
    overwrite: bool = False,
) -> list[Lesson]:
    """
    Generate PLANNED Lesson records for `group` from its GroupSchedule.

    Args:
        group:     The Group instance to generate lessons for.
        end_date:  Last date to generate lessons up to (inclusive).
                   Defaults to 6 months from group.start_date.
        overwrite: If True, existing PLANNED lessons in the range are deleted
                   and regenerated. COMPLETED/CANCELLED lessons are never touched.

    Returns:
        List of newly created Lesson instances.

    Raises:
        ValueError: If the group has no GroupSchedule defined.
    """
    schedules = list(
        GroupSchedule.all_objects.filter(group=group).prefetch_related()
    )
    if not schedules:
        raise ValueError(
            f"Group '{group.name}' (id={group.pk}) has no GroupSchedule defined. "
            "Create a schedule before generating lessons."
        )

    start_date = group.start_date
    if end_date is None:
        # Default: generate 6 months of lessons
        end_date = start_date + datetime.timedelta(days=182)

    if end_date < start_date:
        raise ValueError(f"end_date ({end_date}) must be >= start_date ({start_date})")

    # Collect all scheduled weekday integers across all schedule entries
    scheduled_weekdays: set[int] = set()
    for schedule in schedules:
        for day_code in schedule.selected_days:
            weekday = _DAY_TO_WEEKDAY.get(day_code)
            if weekday is not None:
                scheduled_weekdays.add(weekday)

    if not scheduled_weekdays:
        raise ValueError(
            f"Group '{group.name}' has a schedule but no days are selected."
        )

    with transaction.atomic():
        # Optionally clean out existing PLANNED lessons in the date range
        if overwrite:
            Lesson.all_objects.filter(
                group=group,
                date__range=(start_date, end_date),
                status=Lesson.Status.PLANNED,
            ).delete()

        # Find dates that already have any lesson (to skip duplicates)
        existing_dates = set(
            Lesson.all_objects.filter(
                group=group,
                date__range=(start_date, end_date),
            ).values_list('date', flat=True)
        )

        # Walk the date range and create lessons on matching weekdays
        lessons_to_create = []
        current_date = start_date
        while current_date <= end_date:
            if (
                current_date.weekday() in scheduled_weekdays
                and current_date not in existing_dates
            ):
                lessons_to_create.append(
                    Lesson(
                        group=group,
                        teacher=group.teacher,  # default to group's assigned teacher
                        date=current_date,
                        status=Lesson.Status.PLANNED,
                    )
                )
            current_date += datetime.timedelta(days=1)

        created = Lesson.all_objects.bulk_create(lessons_to_create)

    return created


def regenerate_lessons_after_schedule_change(group: Group) -> list[Lesson]:
    """
    Called when a GroupSchedule is updated to re-sync future lessons.

    - Only PLANNED lessons from today onwards are regenerated.
    - COMPLETED and CANCELLED lessons are preserved.
    - Uses overwrite=True to remove stale PLANNED lessons before re-creating.
    """
    today = datetime.date.today()
    # Rebuild PLANNED lessons from today forward (6 month window)
    end_date = today + datetime.timedelta(days=182)

    # Delete future PLANNED lessons (past ones stay untouched)
    Lesson.all_objects.filter(
        group=group,
        date__gte=today,
        status=Lesson.Status.PLANNED,
    ).delete()

    # Re-generate from today
    schedules = list(GroupSchedule.all_objects.filter(group=group))
    if not schedules:
        return []

    scheduled_weekdays: set[int] = set()
    for schedule in schedules:
        for day_code in schedule.selected_days:
            weekday = _DAY_TO_WEEKDAY.get(day_code)
            if weekday is not None:
                scheduled_weekdays.add(weekday)

    lessons_to_create = []
    current_date = today
    while current_date <= end_date:
        if current_date.weekday() in scheduled_weekdays:
            lessons_to_create.append(
                Lesson(
                    group=group,
                    teacher=group.teacher,
                    date=current_date,
                    status=Lesson.Status.PLANNED,
                )
            )
        current_date += datetime.timedelta(days=1)

    with transaction.atomic():
        created = Lesson.all_objects.bulk_create(lessons_to_create, ignore_conflicts=True)

    return created

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TenantBaseModel, CreateBaseModel
from apps.course.models.lesson import Lesson
from apps.users.models import StudentProfile, User


class Attendance(TenantBaseModel, CreateBaseModel):
    """
    Records a specific student's presence/absence for a single Lesson occurrence.

    The `date` and `group` fields are intentionally removed — they are derived
    from the linked Lesson (lesson.date, lesson.group) to keep a single source
    of truth and enforce referential integrity between attendance and actual
    scheduled class events.
    """

    class Status(models.TextChoices):
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        EXCUSED = 'excused', _('Excused')

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('Lesson'),
        # null=True here is intentional for the Phase 1 migration:
        # existing Attendance rows have no lesson FK. After running the
        # data migration (Phase 2) to backfill or remove stale records,
        # run a follow-up migration to set null=False.
        null=True,
        blank=True,
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('Student'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABSENT,
        verbose_name=_('Attendance status'),
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances',
        verbose_name=_('Marked by'),
    )

    class Meta:
        db_table = 'attendances'
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        # A student can only have one attendance record per lesson
        constraints = [
            models.UniqueConstraint(
                fields=['lesson', 'student'],
                name='unique_attendance_per_lesson_per_student',
            )
        ]
        indexes = [
            models.Index(fields=['lesson'], name='attendance_lesson_idx'),
            models.Index(fields=['student'], name='attendance_student_idx'),
            models.Index(fields=['status'], name='attendance_status_idx'),
        ]

    def __str__(self):
        return f"{self.student} — {self.lesson.date} — {self.status}"

    @property
    def date(self):
        """Convenience accessor: derive date from the linked Lesson."""
        return self.lesson.date

    @property
    def group(self):
        """Convenience accessor: derive group from the linked Lesson."""
        return self.lesson.group
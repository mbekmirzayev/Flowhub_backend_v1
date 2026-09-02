from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.course.models import Group, Lesson
from apps.history.models import History
from apps.payment.models import Payment
from apps.users.models import User, StudentProfile, TeacherProfile, StaffProfile


@login_required
def admin_dashboard(request):
    """Custom statistics dashboard for the Flowhub admin panel."""

    today = timezone.now().date()
    current_month_start = today.replace(day=1)

    # ── User Stats ──────────────────────────────────────────────────────────
    user_stats = User.all_objects.aggregate(
        total=Count("id"),
        students=Count("id", filter=Q(role=User.Status.STUDENT, is_deleted=False)),
        teachers=Count("id", filter=Q(role=User.Status.TEACHER, is_deleted=False)),
        staff=Count("id", filter=Q(
            role__in=[User.Status.ADMIN, User.Status.MANAGER],
            is_deleted=False,
        )),
        active=Count("id", filter=Q(is_active=True, is_deleted=False)),
    )

    # ── Course & Group Stats ─────────────────────────────────────────────────
    group_stats = Group.all_objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Group.Status.ACTIVE)),
        closed=Count("id", filter=Q(status=Group.Status.CLOSED)),
    )

    # ── Payment Stats (current month) ────────────────────────────────────────
    payment_stats = Payment.all_objects.filter(
        payment_date__gte=current_month_start
    ).aggregate(
        total_paid=Sum("amount", filter=Q(status=Payment.Status.PAID)),
        total_pending=Sum("amount", filter=Q(status=Payment.Status.PENDING)),
        total_overdue=Sum("amount", filter=Q(status=Payment.Status.OVERDUE)),
        count_paid=Count("id", filter=Q(status=Payment.Status.PAID)),
        count_pending=Count("id", filter=Q(status=Payment.Status.PENDING)),
        count_overdue=Count("id", filter=Q(status=Payment.Status.OVERDUE)),
    )

    # Ensure None values default to 0
    for key in ("total_paid", "total_pending", "total_overdue"):
        if payment_stats[key] is None:
            payment_stats[key] = 0

    # ── Lesson Stats (today) ─────────────────────────────────────────────────
    lesson_stats = Lesson.all_objects.filter(date=today).aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=Lesson.Status.COMPLETED)),
        planned=Count("id", filter=Q(status=Lesson.Status.PLANNED)),
        cancelled=Count("id", filter=Q(status=Lesson.Status.CANCELLED)),
    )

    # ── Attendance Stats (current month) ─────────────────────────────────────
    attendance_stats = Attendance.all_objects.filter(
        created_at__date__gte=current_month_start
    ).aggregate(
        present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        excused=Count("id", filter=Q(status=Attendance.Status.EXCUSED)),
    )
    total_att = (
        attendance_stats["present"]
        + attendance_stats["absent"]
        + attendance_stats["excused"]
    )
    attendance_stats["total"] = total_att
    attendance_stats["present_pct"] = (
        round(attendance_stats["present"] / total_att * 100) if total_att else 0
    )

    # ── Recent History (last 10 entries) ─────────────────────────────────────
    recent_history = (
        History.all_objects
        .select_related("performed_by", "student__user", "group")
        .order_by("-created_at")[:10]
    )

    context = {
        **admin.site.each_context(request),
        "title": "Dashboard",
        "today": today,
        "current_month": current_month_start.strftime("%B %Y"),
        "user_stats": user_stats,
        "group_stats": group_stats,
        "payment_stats": payment_stats,
        "lesson_stats": lesson_stats,
        "attendance_stats": attendance_stats,
        "recent_history": recent_history,
    }
    return render(request, "admin/dashboard.html", context)

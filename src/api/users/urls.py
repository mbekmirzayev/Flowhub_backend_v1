from django.urls import path

from api.users.views.me import MeAPIView
from api.users.views.staff import StaffList, CreateStaffAPIView, StaffDetailAPIView
from api.users.views.student import CreateStudentAPIVIew, StudentList, StudentDetailAPIView, \
    StudentFreezeAPIView, StudentUnfreezeAPIView
from api.users.views.teacher import CreateTeacherAPIVIew, TeacherList, TeacherDetailAPIView
from api.users.views.teacher.teacher_student import TeacherStudentList

urlpatterns = [
    # ── Current user ──────────────────────────────────────────────────────────
    # Fix #1: GET /me — returns the authenticated user's own profile by role
    path('me', MeAPIView.as_view(), name='me'),

    # ── Staff ─────────────────────────────────────────────────────────────────
    path('staff-create', CreateStaffAPIView.as_view(), name='staff-create'),
    path('staff-list', StaffList.as_view(), name='staff-list'),
    path('staff/<uuid:pk>', StaffDetailAPIView.as_view(), name='staff-detail'),

    # ── Teachers ──────────────────────────────────────────────────────────────
    path('teacher-create', CreateTeacherAPIVIew.as_view(), name='teacher-create'),
    path('teacher-list', TeacherList.as_view(), name='teacher-list'),
    path('teacher/<uuid:pk>', TeacherDetailAPIView.as_view(), name='teacher-detail'),
    # Fix #4: was dead code — view existed in teacher_student.py but was never routed
    path('teacher/<uuid:pk>/students', TeacherStudentList.as_view(), name='teacher-students'),

    # ── Students ──────────────────────────────────────────────────────────────
    path('student-create', CreateStudentAPIVIew.as_view(), name='student-create'),
    path('student-list', StudentList.as_view(), name='student-list'),
    path('student/<uuid:pk>', StudentDetailAPIView.as_view(), name='student-detail'),
    path('student/<uuid:pk>/freeze', StudentFreezeAPIView.as_view(), name='student-freeze'),
    path('student/<uuid:pk>/unfreeze', StudentUnfreezeAPIView.as_view(), name='student-unfreeze'),
]
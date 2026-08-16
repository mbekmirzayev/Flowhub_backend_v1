from django.urls import path

from api.users.views.staff import StaffList, CreateStaffAPIView, StaffDetailAPIView
from api.users.views.student import CreateStudentAPIVIew, StudentList, StudentDetailAPIView, \
    StudentFreezeAPIView, StudentUnfreezeAPIView
from api.users.views.teacher import CreateTeacherAPIVIew, TeacherList, TeacherDetailAPIView

urlpatterns = [
    # Staff
    path('staff-create', CreateStaffAPIView.as_view(), name='staff-create'),
    path('staff-list', StaffList.as_view(), name='staff-list'),
    path('staff/<uuid:pk>', StaffDetailAPIView.as_view(), name='staff-detail'),

    # Teacher
    path('teacher-create', CreateTeacherAPIVIew.as_view(), name='teacher-create'),
    path('teacher-list', TeacherList.as_view(), name='teacher-list'),
    path('teacher/<uuid:pk>', TeacherDetailAPIView.as_view(), name='teacher-detail'),

    # Student
    path('student-create', CreateStudentAPIVIew.as_view(), name='student-create'),
    path('student-list', StudentList.as_view(), name='student-list'),
    path('student/<uuid:pk>', StudentDetailAPIView.as_view(), name='student-detail'),
    path('student/<uuid:pk>/freeze', StudentFreezeAPIView.as_view(), name='student-freeze'),
    path('student/<uuid:pk>/unfreeze', StudentUnfreezeAPIView.as_view(), name='student-unfreeze'),
]
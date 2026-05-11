from django.urls import path

from api.users.views.staff import StaffList, CreateStaffAPIView
from api.users.views.student import CreateStudentAPIVIew
from api.users.views.teacher import CreateTeacherAPIVIew, TeacherList

urlpatterns = [
    path('staff-create', CreateStaffAPIView.as_view(), name='staff-create'),
    path('staff-list', StaffList.as_view(), name='staff-list'),
    path('teacher-create', CreateTeacherAPIVIew.as_view(), name='teacher-create'),
    path('teacher-list', TeacherList.as_view(), name='teacher-list'),
    path('student-create', CreateStudentAPIVIew.as_view(), name='student-create'),

]
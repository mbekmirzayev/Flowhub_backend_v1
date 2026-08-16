from django.urls import path, include

urlpatterns = [
    path('', include('api.auth.urls')),
    path('', include('api.organization.urls')),
    path('', include('api.users.urls')),
    path('', include('api.category.urls')),
    path('', include('api.course.urls')),
    path('', include('api.device.urls')),
    path('', include('api.enrollment.urls')),
    path('', include('api.attendance.urls')),
    path('', include('api.payment.urls')),
    path('', include('api.notification.urls')),
    path('', include('api.history.urls')),
]

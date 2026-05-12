from django.urls import path, include

urlpatterns = [
    path('', include('api.auth.urls')),
    path('', include('api.organization.urls')),
    path('', include('api.users.urls')),
    path('', include('api.category.urls')),
]

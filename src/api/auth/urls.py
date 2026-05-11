from django.urls import path

from api.auth.views import VerifyCodeAPI
from api.auth.views.login import LoginAPI, LogoutAPI, LogoutAllAPI

urlpatterns =[
    path('login', LoginAPI.as_view(), name='login'),
    path('logout', LogoutAPI.as_view(), name='logout'),
    path('verify_code', VerifyCodeAPI.as_view(), name='verify_code'),
    path('logout_all', LogoutAllAPI.as_view(), name='logout_all'),
    ]
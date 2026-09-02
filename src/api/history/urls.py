from django.urls import path

from api.history.views.history import HistoryListAPIView

urlpatterns = [
    path('history', HistoryListAPIView.as_view(), name='history-list'),
]

from django.urls import path
from .views import HomeView, UploadView, DashboardView, AnalysisView
from .views_receiver_history import ReceiverHistoryView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analysis/', AnalysisView.as_view(), name='analysis'),
    path('receiver-history/', ReceiverHistoryView.as_view(), name='receiver_history'),
]

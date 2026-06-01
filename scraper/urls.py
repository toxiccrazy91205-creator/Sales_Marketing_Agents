from django.urls import path
from .views import LeadDashboardView, LeadIngestionView

urlpatterns = [
    path('dashboard/', LeadDashboardView.as_view(), name='dashboard'),
    path('ingest/', LeadIngestionView.as_view(), name='ingest'),
]

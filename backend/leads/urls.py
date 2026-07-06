from django.urls import path

from .views import LeadCreateAPIView

urlpatterns = [
    path("leads/", LeadCreateAPIView.as_view(), name="lead-create"),
]
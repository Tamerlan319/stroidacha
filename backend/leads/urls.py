from django.urls import path

from .views import LeadAttachmentDownloadView, LeadCreateAPIView

urlpatterns = [
    path("leads/", LeadCreateAPIView.as_view(), name="lead-create"),
    path(
        "leads/attachments/<int:pk>/download/",
        LeadAttachmentDownloadView.as_view(),
        name="lead-attachment-download",
    ),
]

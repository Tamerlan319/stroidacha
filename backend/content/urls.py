from django.urls import path

from .views import HomepageContentAPIView

urlpatterns = [
    path("homepage/", HomepageContentAPIView.as_view(), name="homepage-content"),
]
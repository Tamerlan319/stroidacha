from django.urls import path

from .views import LandingPageDetailAPIView, LandingPageListAPIView

urlpatterns = [
    path("landing-pages/", LandingPageListAPIView.as_view(), name="landing-page-list"),
    path(
        "landing-pages/<slug:slug>/",
        LandingPageDetailAPIView.as_view(),
        name="landing-page-detail",
    ),
]
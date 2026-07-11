from django.urls import path

from .views import (
    ContactLocationListAPIView,
    HomepageContentAPIView,
    PortfolioProjectDetailAPIView,
    PortfolioProjectListAPIView,
)

urlpatterns = [
    path("homepage/", HomepageContentAPIView.as_view(), name="homepage-content"),
    path("contacts/", ContactLocationListAPIView.as_view(), name="contact-list"),
    path("portfolio/", PortfolioProjectListAPIView.as_view(), name="portfolio-list"),
    path(
        "portfolio/<slug:slug>/",
        PortfolioProjectDetailAPIView.as_view(),
        name="portfolio-detail",
    ),
]
from django.urls import path

from .views import (
    ContactLocationListAPIView,
    HomepageContentAPIView,
    PortfolioProjectDetailAPIView,
    PortfolioProjectListAPIView,
    ReviewListAPIView,
    SocialLinkListAPIView,
)

urlpatterns = [
    path("homepage/", HomepageContentAPIView.as_view(), name="homepage-content"),
    path("contacts/", ContactLocationListAPIView.as_view(), name="contact-list"),
    path("reviews/", ReviewListAPIView.as_view(), name="review-list"),
    path("social-links/", SocialLinkListAPIView.as_view(), name="social-link-list"),
    path("portfolio/", PortfolioProjectListAPIView.as_view(), name="portfolio-list"),
    path(
        "portfolio/<slug:slug>/",
        PortfolioProjectDetailAPIView.as_view(),
        name="portfolio-detail",
    ),
]

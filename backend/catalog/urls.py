from django.urls import path

from .feeds import RealtyFeedView
from .views import (
    ProjectCategoryListAPIView,
    ProjectDetailAPIView,
    ProjectFacetsAPIView,
    ProjectListAPIView,
)

urlpatterns = [
    path("categories/", ProjectCategoryListAPIView.as_view(), name="category-list"),
    path("projects/", ProjectListAPIView.as_view(), name="project-list"),
    # Раньше projects/<slug>/, иначе «facets» считался бы слагом проекта.
    path("projects/facets/", ProjectFacetsAPIView.as_view(), name="project-facets"),
    path("projects/<slug:slug>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("feeds/realty.yml", RealtyFeedView.as_view(), name="realty-feed"),
]
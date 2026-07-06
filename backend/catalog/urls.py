from django.urls import path

from .views import (
    ProjectCategoryListAPIView,
    ProjectDetailAPIView,
    ProjectListAPIView,
)

urlpatterns = [
    path("categories/", ProjectCategoryListAPIView.as_view(), name="category-list"),
    path("projects/", ProjectListAPIView.as_view(), name="project-list"),
    path("projects/<slug:slug>/", ProjectDetailAPIView.as_view(), name="project-detail"),
]
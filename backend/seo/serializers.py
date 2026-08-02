from rest_framework import serializers

from catalog.models import Project
from catalog.serializers import ProjectCategorySerializer, ProjectListSerializer

from .models import LandingPage, LandingPageFAQ, LandingPageImage


class LandingPageImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = LandingPageImage
        fields = ("id", "image", "alt_text", "caption", "sort_order")

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class LandingPageFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageFAQ
        fields = (
            "id",
            "question",
            "answer",
            "sort_order",
        )


class LandingPageListSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "page_type",
            "h1",
            "category",
            "seo_title",
            "seo_description",
            "sort_order",
        )


class LandingPageDetailSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)
    faqs = LandingPageFAQSerializer(many=True, read_only=True)
    related_projects = serializers.SerializerMethodField()
    images = LandingPageImageSerializer(many=True, read_only=True)

    class Meta:
        model = LandingPage
        fields = (
            "id",
            "title",
            "slug",
            "page_type",
            "h1",
            "intro_text",
            "main_text",
            "category",
            "related_projects",
            "faqs",
            "images",
            "seo_title",
            "seo_description",
            "sort_order",
        )

    def get_related_projects(self, obj):
        projects = obj.related_projects.filter(is_active=True).select_related("category")

        if not projects.exists() and obj.category:
            projects = Project.objects.filter(
                is_active=True,
                category=obj.category,
            ).select_related("category").order_by("sort_order", "-created_at")[:12]

        serializer = ProjectListSerializer(
            projects,
            many=True,
            context=self.context,
        )

        return serializer.data

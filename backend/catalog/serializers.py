from rest_framework import serializers

from .models import (
    Project,
    ProjectAddon,
    ProjectCategory,
    ProjectImage,
    ProjectPackage,
    ProjectPackageItem,
    ProjectPackageSection,
    ProjectPlan,
    ProjectPriceOption,
)


class AbsoluteImageUrlMixin:
    def get_absolute_image_url(self, obj, field_name):
        image = getattr(obj, field_name)

        if not image:
            return None

        request = self.context.get("request")
        url = image.url

        if request:
            return request.build_absolute_uri(url)

        return url


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = (
            "id",
            "title",
            "slug",
            "sort_order",
        )


class ProjectImageSerializer(AbsoluteImageUrlMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = (
            "id",
            "image",
            "image_type",
            "caption",
            "alt_text",
            "sort_order",
        )

    def get_image(self, obj):
        return self.get_absolute_image_url(obj, "image")


class ProjectPlanSerializer(AbsoluteImageUrlMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPlan
        fields = (
            "id",
            "title",
            "image",
            "floor",
            "alt_text",
            "sort_order",
        )

    def get_image(self, obj):
        return self.get_absolute_image_url(obj, "image")


class ProjectPriceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPriceOption
        fields = (
            "id",
            "group_title",
            "title",
            "price",
            "note",
            "sort_order",
        )


class ProjectAddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAddon
        fields = (
            "id",
            "group_title",
            "title",
            "price",
            "description",
            "sort_order",
        )


class ProjectPackageItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPackageItem
        fields = (
            "id",
            "title",
            "value",
            "sort_order",
        )


class ProjectPackageSectionSerializer(serializers.ModelSerializer):
    items = ProjectPackageItemSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectPackageSection
        fields = (
            "id",
            "title",
            "sort_order",
            "items",
        )


class ProjectPackageSerializer(serializers.ModelSerializer):
    sections = ProjectPackageSectionSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectPackage
        fields = (
            "id",
            "title",
            "price_from",
            "description",
            "sort_order",
            "sections",
        )


class ProjectListSerializer(AbsoluteImageUrlMixin, serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "external_id",
            "title",
            "slug",
            "category",
            "construction_type",
            "area",
            "floors",
            "floor_label",
            "bedrooms",
            "width",
            "length",
            "size_text",
            "price_from",
            "build_days_from",
            "build_days_to",
            "short_description",
            "main_image",
            "is_featured",
            "sort_order",
        )

    def get_main_image(self, obj):
        return self.get_absolute_image_url(obj, "main_image")


class ProjectDetailSerializer(ProjectListSerializer):
    images = ProjectImageSerializer(many=True, read_only=True)
    plans = ProjectPlanSerializer(many=True, read_only=True)
    price_options = ProjectPriceOptionSerializer(many=True, read_only=True)
    addons = ProjectAddonSerializer(many=True, read_only=True)
    packages = ProjectPackageSerializer(many=True, read_only=True)

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + (
            "description",
            "seo_title",
            "seo_description",
            "images",
            "plans",
            "price_options",
            "addons",
            "packages",
        )
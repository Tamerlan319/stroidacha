from rest_framework import serializers

from .models import (
    Advantage,
    FAQ,
    Review,
    SocialLink,
    WorkStep,
    ContactLocation,
    PortfolioProject,
    PortfolioImage,
)


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ("platform", "url")


class AdvantageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advantage
        fields = ("id", "title", "description", "icon", "sort_order")


class WorkStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStep
        fields = ("id", "title", "description", "sort_order")


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ("id", "question", "answer", "sort_order")


def public_author_name(full_name):
    """«Андрей Кузнецов» → «Андрей К.».

    Полное имя клиента хранится в админке, а на сайт и в API уходит имя с
    инициалом: так отзыв остаётся живым, но человека по нему не узнать
    (152-ФЗ, ст. 10.1).
    """
    words = full_name.split()
    if len(words) < 2:
        return full_name.strip()
    return f"{words[0]} {words[1][0].upper()}."


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    def get_author_name(self, review):
        return public_author_name(review.author_name)

    class Meta:
        model = Review
        fields = (
            "id",
            "author_name",
            "city",
            "text",
            "project_name",
            "rating",
            "sort_order",
            "created_at",
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


class ContactLocationSerializer(serializers.ModelSerializer):
    location_type_display = serializers.CharField(
        source="get_location_type_display",
        read_only=True,
    )

    class Meta:
        model = ContactLocation
        fields = (
            "id",
            "title",
            "location_type",
            "location_type_display",
            "address",
            "short_description",
            "phone",
            "email",
            "work_hours",
            "map_embed_url",
            "map_link_url",
            "sort_order",
        )


class PortfolioImageSerializer(
    AbsoluteImageUrlMixin,
    serializers.ModelSerializer,
):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioImage
        fields = (
            "id",
            "image",
            "caption",
            "alt_text",
            "is_cover",
            "sort_order",
        )

    def get_image(self, obj):
        return self.get_absolute_image_url(obj, "image")


class PortfolioProjectSerializer(
    AbsoluteImageUrlMixin,
    serializers.ModelSerializer,
):
    main_image = serializers.SerializerMethodField()
    images = PortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioProject
        fields = (
            "id",
            "title",
            "slug",
            "location",
            "area",
            "size_text",
            "material",
            "price",
            "short_description",
            "description",
            "main_image",
            "images",
            "sort_order",
            "created_at",
        )

    def get_main_image(self, obj):
        # obj.cover_image_file уже учитывает is_cover в галерее, main_image
        # и первое фото галереи как запасные варианты — см. модель.
        return self.get_absolute_image_url(obj, "cover_image_file")
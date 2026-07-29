from __future__ import annotations

from rest_framework import serializers

from .models import (
    BuildPackage,
    Project,
    ProjectCategory,
    ProjectContentSection,
    ProjectExtraOption,
    ProjectFoundation,
    ProjectImage,
    ProjectOffer,
    ProjectPlan,
    ProjectRoofCovering,
    ProjectTechnicalData,
)
from .pricing import PricingService


class AbsoluteImageUrlMixin:
    def absolute_file_url(self, file_field):
        if not file_field:
            return None
        try:
            url = file_field.url
        except (ValueError, AttributeError):
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class PricingSerializerMixin:
    def get_pricing_service(self):
        service = self.context.get("_pricing_service")
        if service is None:
            service = PricingService()
            self.context["_pricing_service"] = service
        return service


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ("id", "title", "slug", "sort_order")


class ProjectImageSerializer(AbsoluteImageUrlMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectImage
        fields = ("id", "image", "image_type", "caption", "alt_text", "sort_order")

    def get_image(self, obj):
        return self.absolute_file_url(obj.image)


class ProjectPlanSerializer(AbsoluteImageUrlMixin, serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPlan
        fields = ("id", "title", "image", "floor", "alt_text", "sort_order")

    def get_image(self, obj):
        return self.absolute_file_url(obj.image)


class ProjectOfferSerializer(PricingSerializerMixin, serializers.ModelSerializer):
    # Контракт frontend сохранён: group_title/title/price остаются прежними.
    group_title = serializers.CharField(source="material.group_title", read_only=True)
    title = serializers.CharField(source="material.title", read_only=True)
    material_code = serializers.CharField(source="material.code", read_only=True)
    package_title = serializers.SerializerMethodField()
    package_code = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    base_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProjectOffer
        fields = (
            "id",
            "material_code",
            "group_title",
            "title",
            "package_code",
            "package_title",
            "price",
            "base_price",
            "note",
            "sort_order",
        )

    @staticmethod
    def _package(obj):
        return obj.build_package or (obj.package if obj.package_id else None)

    def get_package_title(self, obj):
        package = self._package(obj)
        return package.title if package else None

    def get_package_code(self, obj):
        package = self._package(obj)
        return getattr(package, "code", None)

    def get_price(self, obj):
        return self.get_pricing_service().get_offer_price(obj)


class ProjectTechnicalDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTechnicalData
        fields = (
            "roof_area_m2",
            "roof_shape",
            "roof_pitch_deg",
            "roof_overhang_m",
            "roof_complexity_factor",
        )


class ProjectContentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContentSection
        fields = ("id", "title", "body", "sort_order")


class ProjectListSerializer(PricingSerializerMixin, AbsoluteImageUrlMixin, serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    price_from = serializers.SerializerMethodField()
    base_price_from = serializers.SerializerMethodField()
    floor_label = serializers.SerializerMethodField()
    size_text = serializers.SerializerMethodField()

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
            "bathrooms",
            "width",
            "length",
            "size_text",
            "terrace_area",
            "has_balcony",
            "has_porch",
            "price_from",
            "base_price_from",
            "build_days_from",
            "build_days_to",
            "short_description",
            "main_image",
            "is_featured",
            "sort_order",
        )

    def get_floor_label(self, obj):
        return obj.computed_floor_label

    def get_size_text(self, obj):
        return obj.computed_size_text

    def get_main_image(self, obj):
        images = list(obj.images.all())
        primary = next((image for image in images if image.is_primary), None)
        if primary:
            return self.absolute_file_url(primary.image)
        if images:
            return self.absolute_file_url(images[0].image)
        # Только безопасный fallback до cleanup legacy-поля.
        return self.absolute_file_url(obj.main_image)

    def get_price_from(self, obj):
        return self.get_pricing_service().get_project_price_from(obj)

    @staticmethod
    def get_base_price_from(obj):
        values = [offer.base_price for offer in obj.offers.all() if offer.base_price is not None]
        return min(values) if values else obj.price_from


class ProjectDetailSerializer(ProjectListSerializer):
    images = serializers.SerializerMethodField()
    plans = ProjectPlanSerializer(many=True, read_only=True)
    price_options = ProjectOfferSerializer(source="offers", many=True, read_only=True)
    addons = serializers.SerializerMethodField()
    packages = serializers.SerializerMethodField()
    content_sections = ProjectContentSectionSerializer(many=True, read_only=True)
    illustrated_options = serializers.SerializerMethodField()
    technical = serializers.SerializerMethodField()

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
            "content_sections",
            "illustrated_options",
            "technical",
        )

    def get_images(self, obj):
        # main_image уже выводится отдельно; в галерею не дублируем primary.
        items = [image for image in obj.images.all() if not image.is_primary]
        return ProjectImageSerializer(items, many=True, context=self.context).data

    def get_technical(self, obj):
        try:
            technical = obj.technical
        except ProjectTechnicalData.DoesNotExist:
            return None
        return ProjectTechnicalDataSerializer(technical).data

    def _foundation_payload(self, item: ProjectFoundation, *, illustrated=False):
        pricing = self.get_pricing_service()
        image = item.image_override or item.foundation.image
        payload = {
            "id": 1_000_000 + item.id,
            "option_code": item.foundation.code,
            "group_title": "Фундамент",
            "title": item.foundation.title,
            "price": pricing.get_foundation_price(item),
            "base_price": item.base_price_override,
            "description": item.description or item.foundation.description,
            "sort_order": item.sort_order,
        }
        if illustrated:
            payload["image"] = self.absolute_file_url(image)
        return payload

    def _roof_payload(self, item: ProjectRoofCovering, *, illustrated=False):
        pricing = self.get_pricing_service()
        image = item.image_override or item.covering.image
        payload = {
            "id": 2_000_000 + item.id,
            "option_code": item.covering.code,
            "group_title": "Чистовая кровля",
            "title": item.covering.title,
            "price": pricing.get_roof_covering_price(item),
            "base_price": item.base_price_override,
            "description": item.description or item.covering.description,
            "sort_order": item.sort_order,
        }
        if illustrated:
            payload["image"] = self.absolute_file_url(image)
        return payload

    def _extra_payload(self, item: ProjectExtraOption, *, illustrated=False):
        pricing = self.get_pricing_service()
        image = item.image_override or item.option.image
        payload = {
            "id": 3_000_000 + item.id,
            "option_code": item.option.code,
            "group_title": "Дополнительно",
            "title": item.option.title,
            "price": pricing.get_extra_price(item),
            "base_price": item.base_price_override,
            "description": item.description or item.option.description,
            "sort_order": item.sort_order,
        }
        if illustrated:
            payload["image"] = self.absolute_file_url(image)
        return payload

    def get_addons(self, obj):
        items = []
        items.extend(self._foundation_payload(item) for item in obj.foundations.all())
        items.extend(self._roof_payload(item) for item in obj.roof_coverings.all())
        items.extend(self._extra_payload(item) for item in obj.extra_options.all())
        return sorted(items, key=lambda item: (item["group_title"], item["sort_order"], item["id"]))

    def get_illustrated_options(self, obj):
        items = []
        for item in obj.foundations.all():
            payload = self._foundation_payload(item, illustrated=True)
            if payload["image"] or payload["description"]:
                items.append(payload)
        for item in obj.roof_coverings.all():
            payload = self._roof_payload(item, illustrated=True)
            if payload["image"] or payload["description"]:
                items.append(payload)
        for item in obj.extra_options.all():
            payload = self._extra_payload(item, illustrated=True)
            if payload["image"] or payload["description"]:
                items.append(payload)
        return sorted(items, key=lambda item: (item["group_title"], item["sort_order"], item["id"]))

    def get_packages(self, obj):
        pricing = self.get_pricing_service()
        package_ids = []
        packages: dict[int, BuildPackage] = {}
        offers_by_package = {}
        for offer in obj.offers.all():
            package = offer.build_package
            if not package:
                continue
            if package.id not in packages:
                package_ids.append(package.id)
                packages[package.id] = package
                offers_by_package[package.id] = []
            offers_by_package[package.id].append(offer)

        overrides = {override.package_id: override for override in obj.package_overrides.all()}
        result = []
        for package_id in package_ids:
            package = packages[package_id]
            override = overrides.get(package_id)
            offers = offers_by_package[package_id]
            effective_prices = [pricing.get_offer_price(offer) for offer in offers]
            effective_prices = [value for value in effective_prices if value is not None]
            base_prices = [offer.base_price for offer in offers if offer.base_price is not None]

            if override:
                sections = self._override_sections(override.sections)
                description = override.description or package.description
            else:
                sections = [
                    {
                        "id": section.id,
                        "title": section.title,
                        "sort_order": section.sort_order,
                        "items": [
                            {
                                "id": item.id,
                                "title": item.title,
                                "value": item.value,
                                "sort_order": item.sort_order,
                            }
                            for item in section.items.all()
                        ],
                    }
                    for section in package.sections.all()
                ]
                description = package.description

            result.append(
                {
                    "id": package.id,
                    "code": package.code,
                    "title": package.title,
                    "price_from": min(effective_prices) if effective_prices else None,
                    "base_price_from": min(base_prices) if base_prices else None,
                    "description": description,
                    "sort_order": package.sort_order,
                    "sections": sections,
                }
            )
        return result

    @staticmethod
    def _override_sections(raw_sections):
        result = []
        for section_index, section in enumerate(raw_sections or []):
            result.append(
                {
                    "id": -(section_index + 1),
                    "title": section.get("title", ""),
                    "sort_order": section.get("sort_order", section_index),
                    "items": [
                        {
                            "id": -((section_index + 1) * 1000 + item_index + 1),
                            "title": item.get("title", ""),
                            "value": item.get("value", ""),
                            "sort_order": item.get("sort_order", item_index),
                        }
                        for item_index, item in enumerate(section.get("items", []))
                    ],
                }
            )
        return result

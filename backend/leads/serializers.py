from rest_framework import serializers

from catalog.models import Project

from .models import Lead


class LeadCreateSerializer(serializers.ModelSerializer):
    project_slug = serializers.SlugField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Lead
        fields = (
            "name",
            "phone",
            "email",
            "message",
            "source",
            "project_slug",
            "page_url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
        )

    def validate_phone(self, value):
        value = value.strip()

        if len(value) < 5:
            raise serializers.ValidationError("Укажите корректный телефон.")

        return value

    def create(self, validated_data):
        project_slug = validated_data.pop("project_slug", "")

        if project_slug:
            try:
                validated_data["project"] = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise serializers.ValidationError(
                    {"project_slug": "Проект с таким slug не найден."}
                )

        request = self.context.get("request")

        if request:
            validated_data["ip_address"] = self.get_client_ip(request)
            validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

        return Lead.objects.create(**validated_data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")
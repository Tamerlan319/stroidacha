import re
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from catalog.models import Project

from .captcha import verify_smartcaptcha
from .models import Lead, LeadAttachment


MAX_ATTACHMENTS = 5
MAX_ATTACHMENT_SIZE = 8 * 1024 * 1024
MAX_ATTACHMENTS_TOTAL_SIZE = 20 * 1024 * 1024

ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
    ".pdf",
}

ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
    "application/octet-stream",
}


def normalize_russian_phone(value):
    digits = re.sub(r"\D", "", value)

    if digits.startswith("8"):
        digits = f"7{digits[1:]}"
    elif digits.startswith("9"):
        digits = f"7{digits}"
    elif digits and not digits.startswith("7"):
        digits = f"7{digits}"

    if len(digits) != 11 or not digits.startswith("7"):
        raise serializers.ValidationError(
            "Введите российский номер из 10 цифр после +7."
        )

    return (
        f"+7 ({digits[1:4]}) {digits[4:7]}"
        f"-{digits[7:9]}-{digits[9:11]}"
    )


class LeadMetadataField(serializers.CharField):
    """Служебное поле заявки, которого нет в форме: адрес страницы, UTM-метки.

    Слишком длинное значение обрезается до размера колонки, а не отклоняет
    заявку целиком. Иначе человек получает ошибку по полю, которое не видит
    и не может исправить: так терялись заявки с заходов из поиска Яндекса
    (длинный etext в адресе) и из Директа (utm_term на кириллице + yclid) —
    адрес страницы не влезал в 200 символов, сервер отвечал 400.
    """

    def __init__(self, model_field_name, **kwargs):
        self.limit = Lead._meta.get_field(model_field_name).max_length
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_blank", True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        return super().to_internal_value(data)[: self.limit]


class LeadCreateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(trim_whitespace=True, max_length=50)
    page_url = LeadMetadataField("page_url")
    utm_source = LeadMetadataField("utm_source")
    utm_medium = LeadMetadataField("utm_medium")
    utm_campaign = LeadMetadataField("utm_campaign")
    utm_content = LeadMetadataField("utm_content")
    utm_term = LeadMetadataField("utm_term")
    # Та же логика, что у LeadMetadataField: неизвестный источник (новая форма
    # на фронте раньше, чем бэкенд узнал о её source) не должен терять заявку.
    source = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=1500,
    )
    website = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=255,
    )
    smartcaptcha_token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=2000,
    )
    consent_accepted = serializers.BooleanField(write_only=True)
    consent_version = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=50,
    )
    project_slug = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    attachments = serializers.ListField(
        child=serializers.FileField(
            max_length=255,
            allow_empty_file=False,
            use_url=False,
        ),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Lead
        fields = (
            "phone",
            "message",
            "source",
            "project_slug",
            "page_url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "website",
            "smartcaptcha_token",
            "consent_accepted",
            "consent_version",
            "attachments",
        )

    def validate_phone(self, value):
        return normalize_russian_phone(value)

    def validate_page_url(self, value):
        # Не http(s) — не отклоняем заявку, просто не сохраняем адрес: в
        # админке он выводится ссылкой, javascript:/data: там не нужны.
        if value and not value.lower().startswith(("https://", "http://")):
            return ""
        return value

    def validate_source(self, value):
        if value in Lead.Source.values:
            return value
        return Lead.Source.CONTACT_FORM

    def validate_consent_accepted(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо согласие на обработку персональных данных."
            )
        return value

    def validate_attachments(self, files):
        if len(files) > MAX_ATTACHMENTS:
            raise serializers.ValidationError(
                f"Можно прикрепить не более {MAX_ATTACHMENTS} файлов."
            )

        total_size = 0

        for uploaded_file in files:
            extension = Path(uploaded_file.name).suffix.lower()
            content_type = getattr(uploaded_file, "content_type", "")

            if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
                raise serializers.ValidationError(
                    f"Файл «{uploaded_file.name}» имеет неподдерживаемый формат."
                )

            if content_type and content_type not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
                raise serializers.ValidationError(
                    f"Файл «{uploaded_file.name}» имеет неподдерживаемый тип."
                )

            if uploaded_file.size > MAX_ATTACHMENT_SIZE:
                raise serializers.ValidationError(
                    f"Файл «{uploaded_file.name}» больше 8 МБ."
                )

            total_size += uploaded_file.size

        if total_size > MAX_ATTACHMENTS_TOTAL_SIZE:
            raise serializers.ValidationError(
                "Общий размер файлов не должен превышать 20 МБ."
            )

        return files

    def validate(self, attrs):
        if attrs.pop("website", ""):
            raise serializers.ValidationError("Не удалось отправить заявку.")

        token = attrs.pop("smartcaptcha_token", "")
        request = self.context.get("request")
        ip_address = self.get_client_ip(request) if request else None

        if not verify_smartcaptcha(token, ip_address):
            raise serializers.ValidationError(
                {
                    "smartcaptcha_token": (
                        "Не пройдена проверка «Я не робот». Обновите страницу "
                        "и попробуйте ещё раз."
                    )
                }
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        project_slug = validated_data.pop("project_slug", "")
        attachments = validated_data.pop("attachments", [])
        validated_data.pop("consent_accepted", None)
        consent_version = (
            validated_data.pop("consent_version", "")
            or getattr(settings, "LEAD_CONSENT_VERSION", "")
            or "2026-08-03"
        )

        if project_slug:
            # Проект могли снять с публикации или переименовать, пока у
            # человека открыта страница, — заявка важнее ссылки на проект
            # (адрес страницы всё равно сохранится в page_url).
            validated_data["project"] = Project.objects.filter(
                slug=project_slug
            ).first()

        request = self.context.get("request")
        if request:
            validated_data["ip_address"] = self.get_client_ip(request)
            validated_data["user_agent"] = request.META.get(
                "HTTP_USER_AGENT",
                "",
            )

        lead = Lead.objects.create(
            consent_version=consent_version,
            consent_given_at=timezone.now(),
            **validated_data,
        )

        for uploaded_file in attachments:
            LeadAttachment.objects.create(
                lead=lead,
                file=uploaded_file,
                original_name=uploaded_file.name[:255],
                content_type=getattr(uploaded_file, "content_type", "")[:100],
                size=uploaded_file.size,
            )

        return lead

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

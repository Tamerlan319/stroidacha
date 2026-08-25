import logging

from django.http import FileResponse, Http404
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Lead, LeadAttachment
from .serializers import LeadCreateSerializer
from .services import notify_managers_about_lead


logger = logging.getLogger(__name__)


class LeadCreateAPIView(CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadCreateSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # Публичный AllowAny-эндпоинт без лимита раньше можно было заваливать
    # фейковыми заявками или файлами по 20 МБ без охлаждения. Лимит — по IP
    # (ScopedRateThrottle для анонимных запросов ключуется по адресу),
    # настраивается через LEAD_THROTTLE_RATE (см. settings.REST_FRAMEWORK).
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "leads"

    def perform_create(self, serializer):
        lead = serializer.save()

        try:
            notify_managers_about_lead(lead)
        except Exception:
            logger.exception(
                "Не удалось отправить email-уведомление о заявке"
            )


class LeadAttachmentDownloadView(APIView):
    """Отдаёт файл вложения заявки только сотрудникам с доступом в админку.

    Файлы хранятся в приватном хранилище (см. leads/storage.py), которое не
    примонтировано в Caddy и недоступно напрямую по URL — единственный
    легитимный способ их получить теперь этот view.
    """

    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            attachment = LeadAttachment.objects.select_related("lead").get(pk=pk)
        except LeadAttachment.DoesNotExist:
            raise Http404

        if not attachment.file:
            raise Http404

        return FileResponse(
            attachment.file.open("rb"),
            as_attachment=True,
            filename=attachment.original_name or attachment.file.name,
            content_type=attachment.content_type or None,
        )

import logging

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .models import Lead
from .serializers import LeadCreateSerializer
from .services import notify_managers_about_lead


logger = logging.getLogger(__name__)


class LeadCreateAPIView(CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        lead = serializer.save()

        try:
            notify_managers_about_lead(lead)
        except Exception:
            logger.exception("Не удалось отправить email-уведомление о заявке")
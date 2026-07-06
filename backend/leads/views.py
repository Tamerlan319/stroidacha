from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .models import Lead
from .serializers import LeadCreateSerializer


class LeadCreateAPIView(CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadCreateSerializer
    permission_classes = [AllowAny]
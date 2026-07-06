from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Advantage, FAQ, Review, WorkStep
from .serializers import (
    AdvantageSerializer,
    FAQSerializer,
    ReviewSerializer,
    WorkStepSerializer,
)


class HomepageContentAPIView(APIView):
    def get(self, request):
        advantages = Advantage.objects.filter(is_active=True)
        work_steps = WorkStep.objects.filter(is_active=True)
        faqs = FAQ.objects.filter(is_active=True)
        reviews = Review.objects.filter(is_active=True)

        return Response(
            {
                "advantages": AdvantageSerializer(advantages, many=True).data,
                "work_steps": WorkStepSerializer(work_steps, many=True).data,
                "faqs": FAQSerializer(faqs, many=True).data,
                "reviews": ReviewSerializer(reviews, many=True).data,
            }
        )
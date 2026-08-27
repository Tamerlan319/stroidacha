from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import (
    Advantage,
    FAQ,
    Review,
    SocialLink,
    WorkStep,
    ContactLocation,
    PortfolioProject,
)
from .serializers import (
    AdvantageSerializer,
    FAQSerializer,
    ReviewSerializer,
    SocialLinkSerializer,
    WorkStepSerializer,
    ContactLocationSerializer,
    PortfolioProjectSerializer,
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
    
class SocialLinkListAPIView(ListAPIView):
    serializer_class = SocialLinkSerializer

    def get_queryset(self):
        return SocialLink.objects.filter(is_active=True).order_by(
            "sort_order",
            "id",
        )


class ContactLocationListAPIView(ListAPIView):
    serializer_class = ContactLocationSerializer

    def get_queryset(self):
        return ContactLocation.objects.filter(is_active=True).order_by(
            "sort_order",
            "id",
        )


class ReviewListAPIView(ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(is_active=True).order_by(
            "sort_order",
            "-created_at",
        )


class PortfolioProjectListAPIView(ListAPIView):
    serializer_class = PortfolioProjectSerializer

    def get_queryset(self):
        return (
            PortfolioProject.objects.filter(is_active=True)
            .prefetch_related("images")
            .order_by("sort_order", "-created_at", "id")
        )


class PortfolioProjectDetailAPIView(RetrieveAPIView):
    serializer_class = PortfolioProjectSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            PortfolioProject.objects.filter(is_active=True)
            .prefetch_related("images")
        )

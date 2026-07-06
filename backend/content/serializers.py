from rest_framework import serializers

from .models import Advantage, FAQ, Review, WorkStep


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


class ReviewSerializer(serializers.ModelSerializer):
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
        )
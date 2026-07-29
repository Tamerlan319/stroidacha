from django.urls import path

from .views import CalculatorCalculateAPIView, CalculatorConfigAPIView

urlpatterns = [
    path("calculator/config/", CalculatorConfigAPIView.as_view(), name="calculator-config"),
    path("calculator/calculate/", CalculatorCalculateAPIView.as_view(), name="calculator-calculate"),
]

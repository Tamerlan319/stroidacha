from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CalculatorRequestSerializer
from .services import HouseCalculatorService


class CalculatorConfigAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(HouseCalculatorService().get_config())


class CalculatorCalculateAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = CalculatorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = HouseCalculatorService().calculate(serializer.validated_data, request=request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)

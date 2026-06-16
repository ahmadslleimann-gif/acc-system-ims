from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CompanyProfile, TaxRate, FiscalPeriod
from .serializers import (
    CompanyProfileSerializer, TaxRateSerializer, FiscalPeriodSerializer,
)


class CompanyProfileView(APIView):
    """Singleton company profile: GET (any auth user) / PUT (admin)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CompanyProfileSerializer(CompanyProfile.get_solo()).data)

    def put(self, request):
        if not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=403)
        obj = CompanyProfile.get_solo()
        s = CompanyProfileSerializer(obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save(updated_by=request.user)
        return Response(s.data)


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]


class FiscalPeriodViewSet(viewsets.ModelViewSet):
    queryset = FiscalPeriod.objects.all()
    serializer_class = FiscalPeriodSerializer
    permission_classes = [IsAdminUser]

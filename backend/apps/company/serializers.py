from rest_framework import serializers
from .models import CompanyProfile, TaxRate, FiscalPeriod


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = ["id", "name", "rate_percent", "is_active"]


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyProfile
        fields = [
            "id", "name_en", "name_ar", "legal_name", "tax_number",
            "base_currency", "fiscal_year_start_month", "address",
            "phone", "email", "logo", "default_tax_rate",
        ]


class FiscalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = ["id", "name", "start_date", "end_date", "status"]

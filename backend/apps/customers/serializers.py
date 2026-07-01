from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = [
            "id", "code", "name", "name_ar", "email", "phone",
            "tax_number", "address", "is_active", "notes", "balance",
        ]

    def get_balance(self, obj):
        from apps.reports.ledgers import partner_balance
        return partner_balance("customer", obj.id)

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        if not validated_data.get("code"):
            validated_data["code"] = next_document_no(Customer, "C", field="code")
        return super().create(validated_data)

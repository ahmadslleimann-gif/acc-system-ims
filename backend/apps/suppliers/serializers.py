from rest_framework import serializers
from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            "id", "code", "name", "name_ar", "email", "phone",
            "tax_number", "address", "is_active", "notes", "balance",
        ]

    def get_balance(self, obj):
        from apps.reports.ledgers import partner_balance
        return partner_balance("supplier", obj.id)

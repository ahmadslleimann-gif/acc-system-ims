from rest_framework import serializers
from apps.accounting_engine.numbering import next_document_no
from .models import Product, StockMovement


class ProductSerializer(serializers.ModelSerializer):
    stock_value = serializers.SerializerMethodField()
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "code", "name_en", "name_ar", "kind", "barcode", "unit",
            "sale_price", "tax_rate", "quantity_on_hand", "average_cost",
            "reorder_level", "inventory_account", "cogs_account", "sales_account",
            "is_active", "stock_value", "is_low_stock",
        ]
        # Valuation fields are maintained by stock movements, never set directly.
        read_only_fields = ["quantity_on_hand", "average_cost"]

    def get_stock_value(self, obj):
        return str(obj.stock_value)

    def create(self, validated_data):
        return Product.objects.create(created_by=self.context["request"].user, **validated_data)


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "doc_no", "product", "product_code", "product_name", "date",
            "direction", "reason", "quantity", "unit_cost", "total_cost",
            "contra_account", "qty_after", "avg_cost_after", "status",
            "reference", "journal_entry",
        ]
        read_only_fields = ["doc_no", "total_cost", "qty_after", "avg_cost_after", "status", "journal_entry"]

    def create(self, validated_data):
        return StockMovement.objects.create(
            doc_no=next_document_no(StockMovement, "STK"),
            created_by=self.context["request"].user,
            **validated_data,
        )

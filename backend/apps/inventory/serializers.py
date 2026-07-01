from rest_framework import serializers
from apps.accounting_engine.numbering import next_document_no
from apps.common.roles import in_group as _in_group
from .models import Product, StockMovement, ProductSupplier


class ProductSupplierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    supplier_code = serializers.CharField(source="supplier.code", read_only=True)
    product_name = serializers.CharField(source="product.name_en", read_only=True)

    class Meta:
        model = ProductSupplier
        fields = [
            "id", "product", "product_name", "supplier", "supplier_name", "supplier_code",
            "supplier_item_code", "cost", "last_purchase_price", "is_preferred", "notes",
        ]
        read_only_fields = ["last_purchase_price"]


class ProductSerializer(serializers.ModelSerializer):
    stock_value = serializers.SerializerMethodField()
    is_low_stock = serializers.BooleanField(read_only=True)
    code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            "id", "code", "name_en", "name_ar", "kind", "barcode", "unit",
            "sale_price", "price_retail", "price_wholesale", "price_bulk",
            "cost_price", "minimum_selling_price", "max_discount_percent",
            "tax_rate", "quantity_on_hand", "average_cost",
            "reorder_level", "inventory_account", "cogs_account", "sales_account",
            "is_active", "stock_value", "is_low_stock",
        ]
        # Valuation fields are maintained by stock movements, never set directly.
        read_only_fields = ["quantity_on_hand", "average_cost"]

    # Admins-only may write these. Cost-bearing ones are also HIDDEN from sales roles.
    PRICE_FIELDS = [
        "sale_price", "price_retail", "price_wholesale", "price_bulk",
        "cost_price", "minimum_selling_price", "max_discount_percent",
    ]
    COST_FIELDS = [
        "cost_price", "average_cost", "stock_value",
        "inventory_account", "cogs_account", "sales_account",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(self.context.get("request"), "user", None)
        is_admin = bool(user and (user.is_superuser or _in_group(user, "Super Admin")))
        can_view_cost = is_admin or _in_group(user, "Accountant")

        # Non-admins can never WRITE prices (read-only).
        if not is_admin:
            for f in self.PRICE_FIELDS:
                if f in self.fields:
                    self.fields[f].read_only = True
        # Sales/Viewer never even SEE cost / margin / account mappings.
        if not can_view_cost:
            for f in self.COST_FIELDS:
                self.fields.pop(f, None)

    def get_stock_value(self, obj):
        return str(obj.stock_value)

    def create(self, validated_data):
        if not validated_data.get("code"):
            validated_data["code"] = next_document_no(Product, "P", field="code")
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

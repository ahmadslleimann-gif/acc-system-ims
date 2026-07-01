from django.contrib import admin
from .models import Product, StockMovement, ProductSupplier


@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = ("product", "supplier", "cost", "last_purchase_price", "is_preferred")
    list_filter = ("is_preferred",)
    search_fields = ("product__code", "supplier__name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name_en", "kind", "quantity_on_hand", "average_cost", "sale_price", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("code", "name_en", "barcode")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("doc_no", "product", "direction", "reason", "quantity", "total_cost", "status", "date")
    list_filter = ("direction", "reason", "status")
    search_fields = ("doc_no", "product__code")

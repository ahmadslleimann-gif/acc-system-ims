from django.contrib import admin
from .models import Product, StockMovement


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

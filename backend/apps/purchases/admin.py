from django.contrib import admin
from .models import PurchaseInvoice, PurchaseInvoiceItem, SupplierPayment, DebitNote


class PurchaseInvoiceItemInline(admin.TabularInline):
    model = PurchaseInvoiceItem
    extra = 0


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("doc_no", "supplier", "date", "status", "total")
    list_filter = ("status",)
    inlines = [PurchaseInvoiceItemInline]


admin.site.register(SupplierPayment)
admin.site.register(DebitNote)

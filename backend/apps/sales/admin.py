from django.contrib import admin
from .models import (
    Quotation, QuotationItem, SalesInvoice, SalesInvoiceItem,
    CustomerPayment, CreditNote,
)


class SalesInvoiceItemInline(admin.TabularInline):
    model = SalesInvoiceItem
    extra = 0


@admin.register(SalesInvoice)
class SalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ("doc_no", "customer", "date", "status", "total")
    list_filter = ("status",)
    inlines = [SalesInvoiceItemInline]


admin.site.register(Quotation)
admin.site.register(CustomerPayment)
admin.site.register(CreditNote)

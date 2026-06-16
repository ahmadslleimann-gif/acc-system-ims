from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuotationViewSet, SalesInvoiceViewSet, CustomerPaymentViewSet, CreditNoteViewSet,
)

router = DefaultRouter()
router.register("quotations", QuotationViewSet, basename="quotation")
router.register("invoices", SalesInvoiceViewSet, basename="salesinvoice")
router.register("payments", CustomerPaymentViewSet, basename="customerpayment")
router.register("credit-notes", CreditNoteViewSet, basename="creditnote")

urlpatterns = [path("", include(router.urls))]

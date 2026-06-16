from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseInvoiceViewSet, SupplierPaymentViewSet, DebitNoteViewSet

router = DefaultRouter()
router.register("invoices", PurchaseInvoiceViewSet, basename="purchaseinvoice")
router.register("payments", SupplierPaymentViewSet, basename="supplierpayment")
router.register("debit-notes", DebitNoteViewSet, basename="debitnote")

urlpatterns = [path("", include(router.urls))]

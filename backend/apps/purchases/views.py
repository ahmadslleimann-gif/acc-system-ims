from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import PurchaseInvoice, SupplierPayment, DebitNote
from .serializers import (
    PurchaseInvoiceSerializer, SupplierPaymentSerializer, DebitNoteSerializer,
)
from . import services


class _DraftDeleteMixin:
    def destroy(self, request, *args, **kwargs):
        if getattr(self.get_object(), "status", "DRAFT") != "DRAFT":
            return Response({"detail": "Posted documents cannot be deleted. Use cancel."}, status=400)
        return super().destroy(request, *args, **kwargs)


class PurchaseInvoiceViewSet(_DraftDeleteMixin, viewsets.ModelViewSet):
    queryset = PurchaseInvoice.objects.prefetch_related("items").select_related("supplier").all()
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["supplier", "status", "date"]
    search_fields = ["doc_no", "supplier__name", "supplier_ref"]
    required_perms = {
        "POST": ["purchases.add_purchaseinvoice"],
        "PUT": ["purchases.change_purchaseinvoice"],
        "PATCH": ["purchases.change_purchaseinvoice"],
        "DELETE": ["purchases.delete_purchaseinvoice"],
    }

    @action(detail=True, methods=["post"])
    def post_invoice(self, request, pk=None):
        invoice = services.post_invoice(self.get_object(), user=request.user)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        from apps.accounting_engine.workflow import cancel_invoice_with_stock
        invoice = cancel_invoice_with_stock(self.get_object(), user=request.user, restore_direction="OUT")
        return Response(self.get_serializer(invoice).data)


class SupplierPaymentViewSet(_DraftDeleteMixin, viewsets.ModelViewSet):
    queryset = SupplierPayment.objects.select_related("supplier").all()
    serializer_class = SupplierPaymentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["supplier", "status"]
    search_fields = ["doc_no"]
    required_perms = {
        "POST": ["purchases.add_supplierpayment"],
        "PUT": ["purchases.change_supplierpayment"],
        "PATCH": ["purchases.change_supplierpayment"],
        "DELETE": ["purchases.delete_supplierpayment"],
    }

    @action(detail=True, methods=["post"])
    def post_payment(self, request, pk=None):
        payment = services.post_payment(self.get_object(), user=request.user)
        return Response(self.get_serializer(payment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        from apps.accounting_engine.workflow import reverse_only_cancel
        return Response(self.get_serializer(reverse_only_cancel(self.get_object(), user=request.user)).data)


class DebitNoteViewSet(_DraftDeleteMixin, viewsets.ModelViewSet):
    queryset = DebitNote.objects.select_related("supplier").all()
    serializer_class = DebitNoteSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["supplier", "status"]
    search_fields = ["doc_no"]
    required_perms = {
        "POST": ["purchases.add_debitnote"],
        "PUT": ["purchases.change_debitnote"],
        "PATCH": ["purchases.change_debitnote"],
        "DELETE": ["purchases.delete_debitnote"],
    }

    @action(detail=True, methods=["post"])
    def post_note(self, request, pk=None):
        note = services.post_debit_note(self.get_object(), user=request.user)
        return Response(self.get_serializer(note).data)

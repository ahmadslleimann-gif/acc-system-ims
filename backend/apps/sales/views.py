from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import HasModelPermission
from .models import Quotation, SalesInvoice, CustomerPayment, CreditNote
from .serializers import (
    QuotationSerializer, SalesInvoiceSerializer,
    CustomerPaymentSerializer, CreditNoteSerializer,
)
from . import services


class _DraftDeleteMixin:
    """Block deletion of non-DRAFT financial documents."""

    def destroy(self, request, *args, **kwargs):
        if getattr(self.get_object(), "status", "DRAFT") != "DRAFT":
            return Response({"detail": "Posted documents cannot be deleted. Use cancel."}, status=400)
        return super().destroy(request, *args, **kwargs)


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.prefetch_related("items").all()
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]
    required_perms = {
        "POST": ["sales.add_quotation"],
        "PUT": ["sales.change_quotation"],
        "PATCH": ["sales.change_quotation"],
        "DELETE": ["sales.delete_quotation"],
    }


class SalesInvoiceViewSet(viewsets.ModelViewSet):
    queryset = SalesInvoice.objects.prefetch_related("items").select_related("customer").all()
    serializer_class = SalesInvoiceSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["customer", "status", "date"]
    search_fields = ["doc_no", "customer__name"]
    required_perms = {
        "POST": ["sales.add_salesinvoice"],
        "PUT": ["sales.change_salesinvoice"],
        "PATCH": ["sales.change_salesinvoice"],
        "DELETE": ["sales.delete_salesinvoice"],
    }

    def destroy(self, request, *args, **kwargs):
        if self.get_object().status != "DRAFT":
            return Response({"detail": "Posted invoices cannot be deleted. Use cancel."}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def post_invoice(self, request, pk=None):
        invoice = services.post_invoice(self.get_object(), user=request.user)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        from apps.accounting_engine.workflow import cancel_invoice_with_stock
        invoice = cancel_invoice_with_stock(self.get_object(), user=request.user, restore_direction="IN")
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        from apps.reports.pdf import invoice_pdf_response
        return invoice_pdf_response(self.get_object())


class CustomerPaymentViewSet(_DraftDeleteMixin, viewsets.ModelViewSet):
    queryset = CustomerPayment.objects.select_related("customer").all()
    serializer_class = CustomerPaymentSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]
    required_perms = {
        "POST": ["sales.add_customerpayment"],
        "PUT": ["sales.change_customerpayment"],
        "PATCH": ["sales.change_customerpayment"],
        "DELETE": ["sales.delete_customerpayment"],
    }

    @action(detail=True, methods=["post"])
    def post_payment(self, request, pk=None):
        payment = services.post_payment(self.get_object(), user=request.user)
        return Response(self.get_serializer(payment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        from apps.accounting_engine.workflow import reverse_only_cancel
        return Response(self.get_serializer(reverse_only_cancel(self.get_object(), user=request.user)).data)


class CreditNoteViewSet(_DraftDeleteMixin, viewsets.ModelViewSet):
    queryset = CreditNote.objects.select_related("customer").all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated, HasModelPermission]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]
    required_perms = {
        "POST": ["sales.add_creditnote"],
        "PUT": ["sales.change_creditnote"],
        "PATCH": ["sales.change_creditnote"],
        "DELETE": ["sales.delete_creditnote"],
    }

    @action(detail=True, methods=["post"])
    def post_note(self, request, pk=None):
        note = services.post_credit_note(self.get_object(), user=request.user)
        return Response(self.get_serializer(note).data)

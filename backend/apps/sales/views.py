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


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.prefetch_related("items").all()
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]


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

    @action(detail=True, methods=["post"])
    def post_invoice(self, request, pk=None):
        invoice = services.post_invoice(self.get_object(), user=request.user)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        from apps.reports.pdf import invoice_pdf_response
        return invoice_pdf_response(self.get_object())


class CustomerPaymentViewSet(viewsets.ModelViewSet):
    queryset = CustomerPayment.objects.select_related("customer").all()
    serializer_class = CustomerPaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]

    @action(detail=True, methods=["post"])
    def post_payment(self, request, pk=None):
        payment = services.post_payment(self.get_object(), user=request.user)
        return Response(self.get_serializer(payment).data)


class CreditNoteViewSet(viewsets.ModelViewSet):
    queryset = CreditNote.objects.select_related("customer").all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["customer", "status"]
    search_fields = ["doc_no"]

    @action(detail=True, methods=["post"])
    def post_note(self, request, pk=None):
        note = services.post_credit_note(self.get_object(), user=request.user)
        return Response(self.get_serializer(note).data)

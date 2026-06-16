from rest_framework import serializers
from .models import (
    Quotation, QuotationItem, SalesInvoice, SalesInvoiceItem,
    CustomerPayment, CreditNote,
)


class SalesInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesInvoiceItem
        fields = [
            "id", "product", "description", "quantity", "unit_price", "tax_rate",
            "line_subtotal", "tax_amount", "line_total",
        ]
        read_only_fields = ["line_subtotal", "tax_amount", "line_total"]


class SalesInvoiceSerializer(serializers.ModelSerializer):
    items = SalesInvoiceItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = SalesInvoice
        fields = [
            "id", "doc_no", "customer", "customer_name", "date", "due_date",
            "status", "subtotal", "tax_amount", "total", "notes",
            "journal_entry", "items",
        ]
        read_only_fields = ["doc_no", "status", "subtotal", "tax_amount", "total", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        from .services import _recompute_invoice_totals
        items = validated_data.pop("items")
        invoice = SalesInvoice.objects.create(
            doc_no=next_document_no(SalesInvoice, "INV"),
            created_by=self.context["request"].user,
            **validated_data,
        )
        SalesInvoiceItem.objects.bulk_create([SalesInvoiceItem(invoice=invoice, **i) for i in items])
        _recompute_invoice_totals(invoice)
        return invoice

    def update(self, instance, validated_data):
        from .services import _recompute_invoice_totals
        if instance.status == "POSTED":
            raise serializers.ValidationError("Posted invoices cannot be edited.")
        items = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            SalesInvoiceItem.objects.bulk_create([SalesInvoiceItem(invoice=instance, **i) for i in items])
        _recompute_invoice_totals(instance)
        return instance


class CustomerPaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = CustomerPayment
        fields = [
            "id", "doc_no", "customer", "customer_name", "date", "amount",
            "deposit_account", "status", "notes", "journal_entry",
        ]
        read_only_fields = ["doc_no", "status", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        return CustomerPayment.objects.create(
            doc_no=next_document_no(CustomerPayment, "RCPT"),
            created_by=self.context["request"].user,
            **validated_data,
        )


class CreditNoteSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = CreditNote
        fields = [
            "id", "doc_no", "customer", "customer_name", "invoice", "date",
            "subtotal", "tax_amount", "total", "status", "reason", "journal_entry",
        ]
        read_only_fields = ["doc_no", "status", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        validated_data["total"] = validated_data.get("subtotal", 0) + validated_data.get("tax_amount", 0)
        return CreditNote.objects.create(
            doc_no=next_document_no(CreditNote, "CN"),
            created_by=self.context["request"].user,
            **validated_data,
        )


class QuotationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationItem
        fields = ["id", "description", "quantity", "unit_price", "tax_rate",
                  "line_subtotal", "tax_amount", "line_total"]
        read_only_fields = ["line_subtotal", "tax_amount", "line_total"]


class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Quotation
        fields = ["id", "doc_no", "customer", "customer_name", "date", "valid_until",
                  "status", "subtotal", "tax_amount", "total", "notes", "items"]
        read_only_fields = ["doc_no", "subtotal", "tax_amount", "total"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        from apps.common.models import ZERO
        items = validated_data.pop("items")
        quote = Quotation.objects.create(
            doc_no=next_document_no(Quotation, "QUO"),
            created_by=self.context["request"].user, **validated_data,
        )
        subtotal = ZERO
        tax = ZERO
        for i in items:
            sub = i["quantity"] * i["unit_price"]
            rate = i["tax_rate"].fraction() if i.get("tax_rate") else ZERO
            t = sub * rate
            QuotationItem.objects.create(
                quotation=quote, line_subtotal=sub, tax_amount=t, line_total=sub + t, **i
            )
            subtotal += sub
            tax += t
        quote.subtotal, quote.tax_amount, quote.total = subtotal, tax, subtotal + tax
        quote.save()
        return quote

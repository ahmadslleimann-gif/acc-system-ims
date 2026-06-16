from rest_framework import serializers
from .models import (
    PurchaseInvoice, PurchaseInvoiceItem, SupplierPayment, DebitNote,
)


class PurchaseInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseInvoiceItem
        fields = ["id", "product", "description", "quantity", "unit_price", "tax_rate",
                  "line_subtotal", "tax_amount", "line_total"]
        read_only_fields = ["line_subtotal", "tax_amount", "line_total"]


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items = PurchaseInvoiceItemSerializer(many=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = ["id", "doc_no", "supplier", "supplier_name", "supplier_ref", "date",
                  "due_date", "status", "subtotal", "tax_amount", "total",
                  "expense_account", "notes", "journal_entry", "items"]
        read_only_fields = ["doc_no", "status", "subtotal", "tax_amount", "total", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        from .services import _recompute_invoice_totals
        items = validated_data.pop("items")
        invoice = PurchaseInvoice.objects.create(
            doc_no=next_document_no(PurchaseInvoice, "PINV"),
            created_by=self.context["request"].user, **validated_data,
        )
        PurchaseInvoiceItem.objects.bulk_create([PurchaseInvoiceItem(invoice=invoice, **i) for i in items])
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
            PurchaseInvoiceItem.objects.bulk_create([PurchaseInvoiceItem(invoice=instance, **i) for i in items])
        _recompute_invoice_totals(instance)
        return instance


class SupplierPaymentSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = SupplierPayment
        fields = ["id", "doc_no", "supplier", "supplier_name", "date", "amount",
                  "paid_from_account", "status", "notes", "journal_entry"]
        read_only_fields = ["doc_no", "status", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        return SupplierPayment.objects.create(
            doc_no=next_document_no(SupplierPayment, "PAY"),
            created_by=self.context["request"].user, **validated_data,
        )


class DebitNoteSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = DebitNote
        fields = ["id", "doc_no", "supplier", "supplier_name", "invoice", "date",
                  "subtotal", "tax_amount", "total", "status", "reason", "journal_entry"]
        read_only_fields = ["doc_no", "status", "journal_entry"]

    def create(self, validated_data):
        from apps.accounting_engine.numbering import next_document_no
        validated_data["total"] = validated_data.get("subtotal", 0) + validated_data.get("tax_amount", 0)
        return DebitNote.objects.create(
            doc_no=next_document_no(DebitNote, "DN"),
            created_by=self.context["request"].user, **validated_data,
        )

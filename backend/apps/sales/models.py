from django.db import models
from apps.common.models import TimeStampedModel, money_field
from apps.customers.models import Customer
from apps.company.models import TaxRate
from apps.journal.models import JournalEntry


class DocStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    POSTED = "POSTED", "Posted"
    CANCELLED = "CANCELLED", "Cancelled"


class Quotation(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotations")
    date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, default="DRAFT")
    subtotal = money_field()
    tax_amount = money_field()
    total = money_field()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return self.doc_no


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit_price = money_field()
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    line_subtotal = money_field()
    tax_amount = money_field()
    line_total = money_field()


class SalesInvoice(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="invoices")
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=DocStatus.choices, default=DocStatus.DRAFT)
    subtotal = money_field()
    tax_amount = money_field()
    total = money_field()
    notes = models.TextField(blank=True)
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return self.doc_no


class SalesInvoiceItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "inventory.Product", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit_price = money_field()
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    line_subtotal = money_field()
    tax_amount = money_field()
    line_total = money_field()


class CustomerPayment(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="payments")
    date = models.DateField()
    amount = money_field()
    deposit_account = models.ForeignKey(
        "accounts_coa.Account", on_delete=models.PROTECT, related_name="+",
        help_text="Cash or bank account that receives the payment.",
    )
    status = models.CharField(max_length=12, choices=DocStatus.choices, default=DocStatus.DRAFT)
    notes = models.TextField(blank=True)
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return self.doc_no


class CreditNote(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="credit_notes")
    invoice = models.ForeignKey(SalesInvoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="credit_notes")
    date = models.DateField()
    subtotal = money_field()
    tax_amount = money_field()
    total = money_field()
    status = models.CharField(max_length=12, choices=DocStatus.choices, default=DocStatus.DRAFT)
    reason = models.TextField(blank=True)
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return self.doc_no

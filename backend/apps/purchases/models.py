from django.db import models
from apps.common.models import TimeStampedModel, money_field
from apps.suppliers.models import Supplier
from apps.company.models import TaxRate
from apps.journal.models import JournalEntry


class DocStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    POSTED = "POSTED", "Posted"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentType(models.TextChoices):
    CASH = "CASH", "Cash"
    CREDIT = "CREDIT", "Credit"


class PurchaseInvoice(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="invoices")
    supplier_ref = models.CharField(max_length=64, blank=True)  # supplier's own invoice no.
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    payment_type = models.CharField(max_length=6, choices=PaymentType.choices, default=PaymentType.CASH)
    amount_paid = money_field()
    status = models.CharField(max_length=12, choices=DocStatus.choices, default=DocStatus.DRAFT)
    subtotal = money_field()
    tax_amount = money_field()
    total = money_field()
    # The expense/inventory account the purchase is booked to.
    expense_account = models.ForeignKey(
        "accounts_coa.Account", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    notes = models.TextField(blank=True)
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-date", "-id"]

    @property
    def outstanding(self):
        return max(self.total - self.amount_paid, 0) if self.status == DocStatus.POSTED else 0

    @property
    def payment_status(self):
        if self.status != DocStatus.POSTED:
            return self.status
        if self.amount_paid >= self.total:
            return "PAID"
        return "PARTIAL" if self.amount_paid > 0 else "UNPAID"

    def __str__(self):
        return self.doc_no


class PurchaseInvoiceItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="items")
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


class SupplierPayment(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="payments")
    date = models.DateField()
    amount = money_field()
    paid_from_account = models.ForeignKey(
        "accounts_coa.Account", on_delete=models.PROTECT, related_name="+",
        help_text="Cash or bank account the payment is made from.",
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


class DebitNote(TimeStampedModel):
    doc_no = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="debit_notes")
    invoice = models.ForeignKey(PurchaseInvoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="debit_notes")
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

from django.db import models
from apps.common.models import TimeStampedModel, money_field
from apps.accounts_coa.models import Account
from apps.company.models import TaxRate
from apps.journal.models import JournalEntry


class ExpenseCategory(TimeStampedModel):
    name = models.CharField(max_length=160)
    name_ar = models.CharField(max_length=160, blank=True)
    expense_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Expense categories"

    def __str__(self):
        return self.name


class Expense(TimeStampedModel):
    """Expense with an approval workflow: DRAFT -> PENDING -> APPROVED -> POSTED."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending approval"
        APPROVED = "APPROVED", "Approved"
        POSTED = "POSTED", "Posted"
        REJECTED = "REJECTED", "Rejected"

    doc_no = models.CharField(max_length=30, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount = money_field()
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    tax_amount = money_field()
    total = money_field()
    # Credit side: cash/bank account paid from (immediate) or left blank to book to AP.
    paid_from_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)
    approved_by = models.ForeignKey("users_auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    journal_entry = models.OneToOneField(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.doc_no} · {self.description}"

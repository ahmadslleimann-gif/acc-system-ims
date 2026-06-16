from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel


class AccountType(models.TextChoices):
    ASSET = "ASSET", "Asset"
    LIABILITY = "LIABILITY", "Liability"
    EQUITY = "EQUITY", "Equity"
    REVENUE = "REVENUE", "Revenue"
    EXPENSE = "EXPENSE", "Expense"


class BalanceSide(models.TextChoices):
    DEBIT = "DEBIT", "Debit"
    CREDIT = "CREDIT", "Credit"


# Normal balance per account type (the accounting equation: A = L + E).
NORMAL_BALANCE = {
    AccountType.ASSET: BalanceSide.DEBIT,
    AccountType.EXPENSE: BalanceSide.DEBIT,
    AccountType.LIABILITY: BalanceSide.CREDIT,
    AccountType.EQUITY: BalanceSide.CREDIT,
    AccountType.REVENUE: BalanceSide.CREDIT,
}


class Account(TimeStampedModel):
    """
    A Chart of Accounts node. Tree via `parent`. Only LEAF accounts are postable.

    `is_system` accounts (AR control, AP control, Cash, Sales, VAT...) cannot be
    deleted and are referenced by the accounting engine via SystemAccount keys.
    """

    code = models.CharField(max_length=20, unique=True)
    name_en = models.CharField(max_length=160)
    name_ar = models.CharField(max_length=160, blank=True)
    type = models.CharField(max_length=10, choices=AccountType.choices)
    normal_balance = models.CharField(max_length=6, choices=BalanceSide.choices, editable=False)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    is_postable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def clean(self):
        if self.parent and self.parent_id == self.id:
            raise ValidationError("An account cannot be its own parent.")
        if self.parent and self.parent.type != self.type:
            raise ValidationError("Child account type must match its parent's type.")

    def save(self, *args, **kwargs):
        self.normal_balance = NORMAL_BALANCE[AccountType(self.type)]
        # A node with children is a header, not postable.
        super().save(*args, **kwargs)

    @property
    def is_leaf(self):
        return not self.children.exists()

    def __str__(self):
        return f"{self.code} · {self.name_en}"


class SystemAccount(models.Model):
    """
    Maps stable engine keys (e.g. 'AR', 'AP', 'SALES', 'VAT_PAYABLE') to actual
    Account rows, so posting templates never hard-code account codes.
    """

    KEY_CHOICES = [
        ("AR", "Accounts Receivable (control)"),
        ("AP", "Accounts Payable (control)"),
        ("SALES", "Sales Revenue"),
        ("SALES_RETURNS", "Sales Returns"),
        ("PURCHASES", "Purchases / Inventory"),
        ("PURCHASE_RETURNS", "Purchase Returns"),
        ("VAT_PAYABLE", "VAT Payable (output tax)"),
        ("VAT_RECEIVABLE", "VAT Receivable (input tax)"),
        ("CASH", "Default Cash"),
        ("RETAINED_EARNINGS", "Retained Earnings"),
        ("ROUNDING", "Rounding differences"),
    ]

    key = models.CharField(max_length=32, choices=KEY_CHOICES, unique=True)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")

    def __str__(self):
        return f"{self.key} -> {self.account.code}"

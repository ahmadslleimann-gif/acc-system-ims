from django.db import models
from apps.common.models import TimeStampedModel, money_field
from apps.accounts_coa.models import Account
from apps.journal.models import JournalEntry


class CashBankAccount(TimeStampedModel):
    """A wallet/till or bank account, each backed by a GL asset account."""

    class Kind(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK = "BANK", "Bank"

    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=4, choices=Kind.choices, default=Kind.CASH)
    gl_account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name="cash_bank")
    bank_name = models.CharField(max_length=160, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    iban = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.kind})"


class CashTransaction(TimeStampedModel):
    """Deposit / withdrawal / transfer. Posts to the ledger via the engine."""

    class Type(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        TRANSFER = "TRANSFER", "Transfer"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"

    doc_no = models.CharField(max_length=30, unique=True)
    type = models.CharField(max_length=12, choices=Type.choices)
    date = models.DateField()
    account = models.ForeignKey(CashBankAccount, on_delete=models.PROTECT, related_name="transactions")
    # For deposit/withdrawal: the contra GL account (income/expense/equity...).
    contra_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    # For transfers: the destination cash/bank account.
    destination_account = models.ForeignKey(
        CashBankAccount, null=True, blank=True, on_delete=models.PROTECT, related_name="incoming_transfers"
    )
    amount = money_field()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    memo = models.CharField(max_length=255, blank=True)
    journal_entry = models.OneToOneField(
        JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.doc_no} ({self.type})"

from decimal import Decimal
from django.db import models
from django.db.models import Q, F

from apps.common.models import TimeStampedModel, money_field, ZERO
from apps.accounts_coa.models import Account


class JournalEntry(TimeStampedModel):
    """
    Journal entry header. States: DRAFT -> POSTED -> REVERSED.
    A POSTED entry is immutable; corrections are made via a reversing entry.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"
        REVERSED = "REVERSED", "Reversed"

    entry_no = models.CharField(max_length=30, unique=True)
    entry_date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    memo = models.TextField(blank=True)

    # Bridge back to the source business document that generated this entry.
    source_type = models.CharField(max_length=40, blank=True)  # e.g. SALES_INVOICE
    source_id = models.CharField(max_length=64, blank=True)

    reversed_entry = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversals"
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(
        "users_auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-entry_date", "-id"]
        verbose_name_plural = "Journal entries"

    @property
    def total_debit(self) -> Decimal:
        return sum((l.debit for l in self.lines.all()), ZERO)

    @property
    def total_credit(self) -> Decimal:
        return sum((l.credit for l in self.lines.all()), ZERO)

    @property
    def is_balanced(self) -> bool:
        return self.total_debit == self.total_credit

    def __str__(self):
        return f"{self.entry_no} ({self.status})"


class JournalLine(models.Model):
    """A single debit-or-credit posting line. A line is one side only."""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="journal_lines")
    debit = money_field()
    credit = money_field()
    line_memo = models.CharField(max_length=255, blank=True)
    is_cleared = models.BooleanField(default=False)  # bank reconciliation flag

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(debit__gte=0), name="line_debit_nonneg"),
            models.CheckConstraint(check=Q(credit__gte=0), name="line_credit_nonneg"),
            # A line is one-sided: not both debit and credit > 0.
            models.CheckConstraint(
                check=~(Q(debit__gt=0) & Q(credit__gt=0)),
                name="line_one_sided",
            ),
        ]
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["entry"]),
        ]

    def __str__(self):
        return f"{self.account.code} D{self.debit} C{self.credit}"

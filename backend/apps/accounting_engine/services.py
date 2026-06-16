"""
Accounting Engine — the ONLY module permitted to write to the ledger.

Business modules (sales, purchases, expenses, cashbanks...) never create
JournalEntry / JournalLine rows directly. They build a `PostingEvent` and call
`PostingService.post(...)`. The engine:
  1. resolves accounts,
  2. validates balance (Σdebit == Σcredit) and that all lines are postable leaves,
  3. checks the fiscal period is open,
  4. writes a balanced, posted entry atomically.

This boundary is what guarantees accounting integrity.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Union

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import AccountingError
from apps.common.models import ZERO
from apps.accounts_coa.models import Account, SystemAccount
from apps.journal.models import JournalEntry, JournalLine
from .numbering import next_entry_no
from .period import assert_period_open

AccountRef = Union[Account, str, int]  # Account instance, system-key string, or pk


def _quantize(value) -> Decimal:
    return (Decimal(value) if not isinstance(value, Decimal) else value).quantize(Decimal("0.0001"))


@dataclass
class PostingLine:
    account: AccountRef
    debit: Decimal = ZERO
    credit: Decimal = ZERO
    memo: str = ""


@dataclass
class PostingEvent:
    """A balanced set of intended postings emitted by a business module."""

    date: object
    source_type: str
    source_id: str = ""
    memo: str = ""
    lines: list = field(default_factory=list)

    def debit(self, account: AccountRef, amount, memo=""):
        amount = _quantize(amount)
        if amount > 0:
            self.lines.append(PostingLine(account=account, debit=amount, memo=memo))
        return self

    def credit(self, account: AccountRef, amount, memo=""):
        amount = _quantize(amount)
        if amount > 0:
            self.lines.append(PostingLine(account=account, credit=amount, memo=memo))
        return self


class PostingService:
    @staticmethod
    def resolve_account(ref: AccountRef) -> Account:
        if isinstance(ref, Account):
            return ref
        if isinstance(ref, int):
            return Account.objects.get(pk=ref)
        # string -> first try a system-account key, then fall back to a GL code.
        try:
            return SystemAccount.objects.select_related("account").get(key=ref).account
        except SystemAccount.DoesNotExist:
            try:
                return Account.objects.get(code=ref)
            except Account.DoesNotExist:
                raise AccountingError(
                    f"Account reference '{ref}' is not a configured system key or GL code."
                )

    @classmethod
    @transaction.atomic
    def post(cls, event: PostingEvent, user=None, status=JournalEntry.Status.POSTED) -> JournalEntry:
        if not event.lines:
            raise AccountingError("Cannot post an entry with no lines.")

        assert_period_open(event.date)

        resolved = []
        total_debit = ZERO
        total_credit = ZERO
        for line in event.lines:
            account = cls.resolve_account(line.account)
            if not account.is_active:
                raise AccountingError(f"Account {account.code} is inactive.")
            if not account.is_postable or not account.is_leaf:
                raise AccountingError(f"Account {account.code} is a header account; not postable.")
            debit = _quantize(line.debit)
            credit = _quantize(line.credit)
            if debit > 0 and credit > 0:
                raise AccountingError("A line cannot be both debit and credit.")
            total_debit += debit
            total_credit += credit
            resolved.append((account, debit, credit, line.memo))

        if total_debit != total_credit:
            raise AccountingError(
                f"Unbalanced entry: debit {total_debit} != credit {total_credit}."
            )
        if total_debit == 0:
            raise AccountingError("Cannot post a zero-value entry.")

        entry = JournalEntry.objects.create(
            entry_no=next_entry_no(event.date),
            entry_date=event.date,
            status=status,
            memo=event.memo,
            source_type=event.source_type,
            source_id=str(event.source_id or ""),
            posted_at=timezone.now() if status == JournalEntry.Status.POSTED else None,
            posted_by=user if status == JournalEntry.Status.POSTED else None,
            created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(entry=entry, account=acc, debit=d, credit=c, line_memo=m)
            for acc, d, c, m in resolved
        ])
        return entry

    @classmethod
    @transaction.atomic
    def reverse(cls, entry: JournalEntry, user=None, date=None, memo=None) -> JournalEntry:
        """Create a mirror entry (debits<->credits) and mark the original REVERSED."""
        if entry.status != JournalEntry.Status.POSTED:
            raise AccountingError("Only POSTED entries can be reversed.")
        if entry.reversals.exists():
            raise AccountingError("Entry has already been reversed.")

        rev_date = date or entry.entry_date
        assert_period_open(rev_date)

        reversal = JournalEntry.objects.create(
            entry_no=next_entry_no(rev_date),
            entry_date=rev_date,
            status=JournalEntry.Status.POSTED,
            memo=memo or f"Reversal of {entry.entry_no}",
            source_type=entry.source_type,
            source_id=entry.source_id,
            reversed_entry=entry,
            posted_at=timezone.now(),
            posted_by=user,
            created_by=user,
        )
        JournalLine.objects.bulk_create([
            JournalLine(
                entry=reversal, account=line.account,
                debit=line.credit, credit=line.debit, line_memo=f"Reversal: {line.line_memo}",
            )
            for line in entry.lines.all()
        ])
        entry.status = JournalEntry.Status.REVERSED
        entry.save(update_fields=["status"])
        return reversal

    @classmethod
    def post_draft(cls, draft_entry: JournalEntry, user=None) -> JournalEntry:
        """Promote a manually-created DRAFT entry to POSTED after validation."""
        if draft_entry.status != JournalEntry.Status.DRAFT:
            raise AccountingError("Only DRAFT entries can be posted.")
        assert_period_open(draft_entry.entry_date)
        lines = list(draft_entry.lines.all())
        if not lines:
            raise AccountingError("Cannot post an entry with no lines.")
        total_debit = sum((l.debit for l in lines), ZERO)
        total_credit = sum((l.credit for l in lines), ZERO)
        if total_debit != total_credit:
            raise AccountingError(f"Unbalanced entry: {total_debit} != {total_credit}.")
        for l in lines:
            if not l.account.is_postable or not l.account.is_leaf:
                raise AccountingError(f"Account {l.account.code} is not postable.")
        draft_entry.status = JournalEntry.Status.POSTED
        draft_entry.posted_at = timezone.now()
        draft_entry.posted_by = user
        draft_entry.save(update_fields=["status", "posted_at", "posted_by"])
        return draft_entry

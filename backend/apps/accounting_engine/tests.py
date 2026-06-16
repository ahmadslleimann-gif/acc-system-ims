"""Core integrity tests for the accounting engine."""
import datetime
from decimal import Decimal

from django.test import TestCase

from apps.common.exceptions import AccountingError
from apps.accounts_coa.models import Account
from apps.journal.models import JournalEntry
from .services import PostingService, PostingEvent


class EngineTests(TestCase):
    def setUp(self):
        self.today = datetime.date.today()
        self.cash = Account.objects.create(code="1110", name_en="Cash", type="ASSET", is_postable=True)
        self.sales = Account.objects.create(code="4100", name_en="Sales", type="REVENUE", is_postable=True)
        self.header = Account.objects.create(code="1000", name_en="Assets", type="ASSET", is_postable=False)

    def test_balanced_entry_posts(self):
        e = PostingEvent(date=self.today, source_type="TEST")
        e.debit(self.cash, Decimal("100"))
        e.credit(self.sales, Decimal("100"))
        entry = PostingService.post(e)
        self.assertEqual(entry.status, JournalEntry.Status.POSTED)
        self.assertTrue(entry.is_balanced)

    def test_unbalanced_entry_rejected(self):
        e = PostingEvent(date=self.today, source_type="TEST")
        e.debit(self.cash, Decimal("100"))
        e.credit(self.sales, Decimal("90"))
        with self.assertRaises(AccountingError):
            PostingService.post(e)
        self.assertEqual(JournalEntry.objects.count(), 0)  # atomic rollback

    def test_header_account_not_postable(self):
        e = PostingEvent(date=self.today, source_type="TEST")
        e.debit(self.header, Decimal("50"))
        e.credit(self.sales, Decimal("50"))
        with self.assertRaises(AccountingError):
            PostingService.post(e)

    def test_reversal_mirrors_entry(self):
        e = PostingEvent(date=self.today, source_type="TEST")
        e.debit(self.cash, Decimal("100"))
        e.credit(self.sales, Decimal("100"))
        entry = PostingService.post(e)
        reversal = PostingService.reverse(entry)
        entry.refresh_from_db()
        self.assertEqual(entry.status, JournalEntry.Status.REVERSED)
        self.assertEqual(reversal.total_debit, Decimal("100.0000"))
        # The reversal's cash line should now be a credit.
        cash_line = reversal.lines.get(account=self.cash)
        self.assertEqual(cash_line.credit, Decimal("100.0000"))

    def test_double_reversal_rejected(self):
        e = PostingEvent(date=self.today, source_type="TEST")
        e.debit(self.cash, Decimal("10"))
        e.credit(self.sales, Decimal("10"))
        entry = PostingService.post(e)
        PostingService.reverse(entry)
        with self.assertRaises(AccountingError):
            PostingService.reverse(entry)

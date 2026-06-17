"""
Reset all transactional + master data back to zero, for a clean start.

DELETES: journal entries/lines, sales (invoices, payments, credit notes, quotations),
purchases (invoices, payments, debit notes), expenses, stock movements, products,
customers, suppliers, cash/bank accounts & transactions, audit logs.

KEEPS: users, roles/permissions, chart of accounts + system accounts,
company profile, tax rates, fiscal periods, expense categories.

Usage:  python manage.py reset_data --yes
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Wipe all transactions and records to start from zero (keeps users, CoA, settings)."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Confirm the wipe (required).")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["yes"]:
            self.stdout.write(self.style.ERROR(
                "Refusing to run without --yes. This deletes all transactions and records."
            ))
            return

        def wipe(label, qs):
            n = qs.count()
            qs.delete()
            self.stdout.write(f"  deleted {n:>5}  {label}")

        # Order matters: delete children / referencing rows before their targets.
        from apps.audit.models import AuditLog
        from apps.inventory.models import StockMovement, Product
        from apps.sales.models import (
            SalesInvoiceItem, SalesInvoice, CustomerPayment, CreditNote,
            QuotationItem, Quotation,
        )
        from apps.purchases.models import (
            PurchaseInvoiceItem, PurchaseInvoice, SupplierPayment, DebitNote,
        )
        from apps.expenses.models import Expense
        from apps.cashbanks.models import CashTransaction, CashBankAccount
        from apps.journal.models import JournalLine, JournalEntry
        from apps.customers.models import Customer
        from apps.suppliers.models import Supplier

        self.stdout.write("Resetting data…")
        wipe("audit logs", AuditLog.objects.all())
        wipe("stock movements", StockMovement.objects.all())

        wipe("sales invoice items", SalesInvoiceItem.objects.all())
        wipe("sales invoices", SalesInvoice.objects.all())
        wipe("customer payments", CustomerPayment.objects.all())
        wipe("credit notes", CreditNote.objects.all())
        wipe("quotation items", QuotationItem.objects.all())
        wipe("quotations", Quotation.objects.all())

        wipe("purchase invoice items", PurchaseInvoiceItem.objects.all())
        wipe("purchase invoices", PurchaseInvoice.objects.all())
        wipe("supplier payments", SupplierPayment.objects.all())
        wipe("debit notes", DebitNote.objects.all())

        wipe("expenses", Expense.objects.all())
        wipe("cash transactions", CashTransaction.objects.all())
        wipe("cash/bank accounts", CashBankAccount.objects.all())

        wipe("journal lines", JournalLine.objects.all())
        # Clear self-referential reversal links (PROTECT) before deleting entries.
        JournalEntry.objects.update(reversed_entry=None)
        wipe("journal entries", JournalEntry.objects.all())

        wipe("products", Product.objects.all())
        wipe("customers", Customer.objects.all())
        wipe("suppliers", Supplier.objects.all())

        self.stdout.write(self.style.SUCCESS("Done. All balances are now zero."))

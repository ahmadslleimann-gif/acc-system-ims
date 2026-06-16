"""Sales posting logic. Builds PostingEvents and hands them to the engine."""
from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.common.models import ZERO
from apps.accounting_engine.services import PostingService, PostingEvent
from apps.journal.models import JournalEntry
from .models import SalesInvoice, CustomerPayment, CreditNote, DocStatus


def _recompute_invoice_totals(invoice: SalesInvoice):
    subtotal = ZERO
    tax = ZERO
    for item in invoice.items.all():
        line_sub = (item.quantity * item.unit_price).quantize(ZERO)
        rate = item.tax_rate.fraction() if item.tax_rate else ZERO
        line_tax = (line_sub * rate).quantize(ZERO)
        item.line_subtotal = line_sub
        item.tax_amount = line_tax
        item.line_total = line_sub + line_tax
        item.save(update_fields=["line_subtotal", "tax_amount", "line_total"])
        subtotal += line_sub
        tax += line_tax
    invoice.subtotal = subtotal
    invoice.tax_amount = tax
    invoice.total = subtotal + tax
    invoice.save(update_fields=["subtotal", "tax_amount", "total"])


@transaction.atomic
def post_invoice(invoice: SalesInvoice, user=None) -> SalesInvoice:
    """
    Revenue:   Dr Accounts Receivable / Cr Sales Revenue (+ Cr VAT Payable)
    Inventory: for stock-product lines, Dr COGS / Cr Inventory at average cost,
               and the on-hand quantity is automatically reduced.
    Both legs go into ONE balanced journal entry.
    """
    from apps.inventory.models import Product
    from apps.inventory import services as inv

    if invoice.status == DocStatus.POSTED:
        raise AccountingError("Invoice is already posted.")
    _recompute_invoice_totals(invoice)
    if invoice.total <= 0:
        raise AccountingError("Invoice total must be positive.")

    # Pre-check stock and compute COGS for stock-tracked products.
    cogs_total = ZERO
    stock_lines = []  # (product, qty)
    for item in invoice.items.select_related("product"):
        product = item.product
        if product and product.kind == Product.Kind.STOCK:
            if item.quantity > product.quantity_on_hand:
                raise AccountingError(
                    f"Insufficient stock for {product.code}: on hand "
                    f"{product.quantity_on_hand}, sold {item.quantity}."
                )
            cogs_total += inv.cogs_preview(product, item.quantity)
            stock_lines.append((product, item.quantity))

    event = PostingEvent(
        date=invoice.date, source_type="SALES_INVOICE", source_id=invoice.id,
        memo=f"Sales invoice {invoice.doc_no} - {invoice.customer.name}",
    )
    event.debit("AR", invoice.total, memo=f"Invoice {invoice.doc_no}")
    event.credit("SALES", invoice.subtotal, memo="Sales revenue")
    if invoice.tax_amount > 0:
        event.credit("VAT_PAYABLE", invoice.tax_amount, memo="Output VAT")
    if cogs_total > 0:
        event.debit("5100", cogs_total, memo="Cost of goods sold")
        event.credit("1150", cogs_total, memo="Inventory reduction")

    entry = PostingService.post(event, user=user)

    # Auto-deduct inventory (records movements linked to this entry).
    for product, qty in stock_lines:
        inv.apply_issue(product, qty, date=invoice.date, reason="SALE",
                        reference=invoice.doc_no, journal_entry=entry, user=user)

    invoice.journal_entry = entry
    invoice.status = DocStatus.POSTED
    invoice.save(update_fields=["journal_entry", "status"])
    return invoice


@transaction.atomic
def post_payment(payment: CustomerPayment, user=None) -> CustomerPayment:
    """Dr Cash/Bank / Cr Accounts Receivable."""
    if payment.status == DocStatus.POSTED:
        raise AccountingError("Payment is already posted.")
    if payment.amount <= 0:
        raise AccountingError("Payment amount must be positive.")

    event = PostingEvent(
        date=payment.date, source_type="CUSTOMER_PAYMENT", source_id=payment.id,
        memo=f"Customer payment {payment.doc_no} - {payment.customer.name}",
    )
    event.debit(payment.deposit_account, payment.amount, memo="Payment received")
    event.credit("AR", payment.amount, memo=f"Settle {payment.customer.name}")

    entry = PostingService.post(event, user=user)
    payment.journal_entry = entry
    payment.status = DocStatus.POSTED
    payment.save(update_fields=["journal_entry", "status"])
    return payment


@transaction.atomic
def post_credit_note(note: CreditNote, user=None) -> CreditNote:
    """Dr Sales Returns (+ Dr VAT Payable) / Cr Accounts Receivable."""
    if note.status == DocStatus.POSTED:
        raise AccountingError("Credit note is already posted.")
    if note.total <= 0:
        raise AccountingError("Credit note total must be positive.")

    event = PostingEvent(
        date=note.date, source_type="CREDIT_NOTE", source_id=note.id,
        memo=f"Credit note {note.doc_no} - {note.customer.name}",
    )
    event.debit("SALES_RETURNS", note.subtotal, memo="Sales return")
    if note.tax_amount > 0:
        event.debit("VAT_PAYABLE", note.tax_amount, memo="Reverse output VAT")
    event.credit("AR", note.total, memo=f"Credit {note.customer.name}")

    entry = PostingService.post(event, user=user)
    note.journal_entry = entry
    note.status = DocStatus.POSTED
    note.save(update_fields=["journal_entry", "status"])
    return note

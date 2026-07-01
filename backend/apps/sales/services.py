"""Sales posting logic. Builds PostingEvents and hands them to the engine."""
from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.common.models import ZERO
from apps.accounting_engine.services import PostingService, PostingEvent
from apps.journal.models import JournalEntry
from .models import SalesInvoice, CustomerPayment, CreditNote, DocStatus


def _apply_official_pricing(invoice: SalesInvoice, user=None):
    """
    SECURITY: the server is the source of truth for price & tax.
    For stock products we OVERWRITE the client-sent unit_price with the official
    tier price from the product master, pull the product's tax rate, and reject
    anything below minimum_selling_price (Super Admin may override).
    Free-text lines (no product) keep their entered price.
    """
    from apps.common.roles import is_super_admin
    from apps.common.exceptions import AccountingError

    is_admin = is_super_admin(user)
    for item in invoice.items.select_related("product"):
        product = item.product
        if not product:
            # Free-text (custom-priced) lines are an admin-only capability — otherwise
            # a non-admin could define an arbitrary price outside the product master.
            if not is_admin and (item.unit_price or 0) > 0:
                raise AccountingError(
                    "Only an admin can add custom-priced lines. Select a product with an official price."
                )
            continue
        official = product.price_for_tier(invoice.price_tier)
        # Enforce the hard floor (admins may override an intentional low tier price).
        floor = product.minimum_selling_price or ZERO
        if floor > 0 and official < floor and not is_admin:
            raise AccountingError(
                f"{product.code}: price {official} is below the minimum selling price {floor}."
            )
        item.unit_price = official
        item.tax_rate = product.tax_rate
        item.save(update_fields=["unit_price", "tax_rate"])


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
    _apply_official_pricing(invoice, user=user)  # server-authoritative prices/tax
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

    from .models import PaymentType
    is_cash = invoice.payment_type == PaymentType.CASH

    items_desc = ", ".join(f"{it.description} x{it.quantity:g}" for it in invoice.items.all())
    event = PostingEvent(
        date=invoice.date, source_type="SALES_INVOICE", source_id=invoice.id,
        memo=f"Sales {invoice.doc_no} - {invoice.customer.name}" + (f" ({items_desc})" if items_desc else ""),
    )
    # Cash sale debits Cash (paid now); credit sale debits Accounts Receivable (owed).
    if is_cash:
        event.debit("CASH", invoice.total, memo=f"Cash sale {invoice.doc_no}")
    else:
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
    if is_cash:
        invoice.amount_paid = invoice.total  # cash sale is settled immediately
    invoice.save(update_fields=["journal_entry", "status", "amount_paid"])
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
    _allocate_customer_payment(payment)
    return payment


def _allocate_customer_payment(payment: CustomerPayment):
    """Apply a receipt to the customer's open CREDIT invoices, oldest first (FIFO),
    so each invoice shows Paid / Partially Paid correctly."""
    from .models import PaymentType
    remaining = payment.amount
    invoices = (
        SalesInvoice.objects
        .filter(customer=payment.customer, status=DocStatus.POSTED, payment_type=PaymentType.CREDIT)
        .order_by("date", "id")
    )
    for inv in invoices:
        if remaining <= 0:
            break
        due = inv.total - inv.amount_paid
        if due <= 0:
            continue
        applied = min(remaining, due)
        inv.amount_paid += applied
        inv.save(update_fields=["amount_paid"])
        remaining -= applied


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

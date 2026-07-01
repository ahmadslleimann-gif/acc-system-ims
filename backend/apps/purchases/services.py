"""Purchase posting logic."""
from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.common.models import ZERO
from apps.accounting_engine.services import PostingService, PostingEvent
from .models import PurchaseInvoice, SupplierPayment, DebitNote, DocStatus


def _recompute_invoice_totals(invoice: PurchaseInvoice):
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
def post_invoice(invoice: PurchaseInvoice, user=None) -> PurchaseInvoice:
    """
    Stock-product lines are capitalised to Inventory (Dr 1150) and the on-hand
    quantity / average cost is automatically increased. Non-stock lines book to
    the expense account. Then (+ Dr VAT Receivable) / Cr Accounts Payable.
    """
    from apps.inventory.models import Product
    from apps.inventory import services as inv

    if invoice.status == DocStatus.POSTED:
        raise AccountingError("Invoice is already posted.")
    _recompute_invoice_totals(invoice)
    if invoice.total <= 0:
        raise AccountingError("Invoice total must be positive.")

    inventory_total = ZERO
    expense_total = ZERO
    receipts = []  # (product, qty, unit_cost)
    for item in invoice.items.select_related("product"):
        product = item.product
        if product and product.kind == Product.Kind.STOCK:
            inventory_total += item.line_subtotal
            unit_cost = item.unit_price if item.quantity else ZERO
            receipts.append((product, item.quantity, unit_cost))
        else:
            expense_total += item.line_subtotal

    expense_acct = invoice.expense_account or "PURCHASES"
    items_desc = ", ".join(f"{it.description} x{it.quantity:g}" for it in invoice.items.all())
    event = PostingEvent(
        date=invoice.date, source_type="PURCHASE_INVOICE", source_id=invoice.id,
        memo=f"Purchase {invoice.doc_no} - {invoice.supplier.name}" + (f" ({items_desc})" if items_desc else ""),
    )
    if inventory_total > 0:
        event.debit("1150", inventory_total, memo="Inventory purchased")
    if expense_total > 0:
        event.debit(expense_acct, expense_total, memo="Purchase / expense")
    if invoice.tax_amount > 0:
        event.debit("VAT_RECEIVABLE", invoice.tax_amount, memo="Input VAT")
    # Cash purchase credits Cash (paid now); credit purchase credits Accounts Payable.
    from .models import PaymentType
    is_cash = invoice.payment_type == PaymentType.CASH
    if is_cash:
        event.credit("CASH", invoice.total, memo=f"Cash purchase {invoice.doc_no}")
    else:
        event.credit("AP", invoice.total, memo=f"Payable {invoice.supplier.name}")

    entry = PostingService.post(event, user=user)

    # Auto-increase inventory (records movements linked to this entry).
    from apps.inventory.models import ProductSupplier
    for product, qty, unit_cost in receipts:
        inv.apply_receipt(product, qty, unit_cost, date=invoice.date, reason="PURCHASE",
                          reference=invoice.doc_no, journal_entry=entry, user=user)
        # Track this supplier as a source for the product, with its latest price.
        ProductSupplier.objects.update_or_create(
            product=product, supplier=invoice.supplier,
            defaults={"last_purchase_price": unit_cost, "cost": unit_cost},
        )

    invoice.journal_entry = entry
    invoice.status = DocStatus.POSTED
    if is_cash:
        invoice.amount_paid = invoice.total
    invoice.save(update_fields=["journal_entry", "status", "amount_paid"])
    return invoice


@transaction.atomic
def post_payment(payment: SupplierPayment, user=None) -> SupplierPayment:
    """Dr Accounts Payable / Cr Cash/Bank."""
    if payment.status == DocStatus.POSTED:
        raise AccountingError("Payment is already posted.")
    if payment.amount <= 0:
        raise AccountingError("Payment amount must be positive.")

    event = PostingEvent(
        date=payment.date, source_type="SUPPLIER_PAYMENT", source_id=payment.id,
        memo=f"Supplier payment {payment.doc_no} - {payment.supplier.name}",
    )
    event.debit("AP", payment.amount, memo=f"Settle {payment.supplier.name}")
    event.credit(payment.paid_from_account, payment.amount, memo="Payment made")

    entry = PostingService.post(event, user=user)
    payment.journal_entry = entry
    payment.status = DocStatus.POSTED
    payment.save(update_fields=["journal_entry", "status"])
    _allocate_supplier_payment(payment)
    return payment


def _allocate_supplier_payment(payment: SupplierPayment):
    """Apply a supplier payment to open CREDIT purchase invoices, oldest first."""
    from .models import PaymentType
    remaining = payment.amount
    invoices = (
        PurchaseInvoice.objects
        .filter(supplier=payment.supplier, status=DocStatus.POSTED, payment_type=PaymentType.CREDIT)
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
def post_debit_note(note: DebitNote, user=None) -> DebitNote:
    """Dr Accounts Payable / Cr Purchase Returns (+ Cr VAT Receivable)."""
    if note.status == DocStatus.POSTED:
        raise AccountingError("Debit note is already posted.")
    if note.total <= 0:
        raise AccountingError("Debit note total must be positive.")

    event = PostingEvent(
        date=note.date, source_type="DEBIT_NOTE", source_id=note.id,
        memo=f"Debit note {note.doc_no} - {note.supplier.name}",
    )
    event.debit("AP", note.total, memo=f"Reduce payable {note.supplier.name}")
    event.credit("PURCHASE_RETURNS", note.subtotal, memo="Purchase return")
    if note.tax_amount > 0:
        event.credit("VAT_RECEIVABLE", note.tax_amount, memo="Reverse input VAT")

    entry = PostingService.post(event, user=user)
    note.journal_entry = entry
    note.status = DocStatus.POSTED
    note.save(update_fields=["journal_entry", "status"])
    return note

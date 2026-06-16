"""
Inventory valuation + posting (perpetual, weighted-average cost).

Stock movements are the ONLY place product.quantity_on_hand / average_cost change,
and every posted movement writes a balanced journal entry through the engine.
"""
from decimal import Decimal
from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.common.models import ZERO
from apps.accounting_engine.services import PostingService, PostingEvent
from apps.accounts_coa.models import Account
from .models import Product, StockMovement


def _account(ref_code):
    return Account.objects.get(code=ref_code)


def _inventory_account(product: Product) -> Account:
    return product.inventory_account or _account("1150")  # Inventory


def _cogs_account(product: Product) -> Account:
    return product.cogs_account or _account("5100")  # Purchases / COGS


def _next_stk_no():
    from apps.accounting_engine.numbering import next_document_no
    return next_document_no(StockMovement, "STK")


def apply_receipt(product: Product, qty, unit_cost, *, date, reason, reference, journal_entry, user=None):
    """
    Increase stock (weighted-average) WITHOUT posting a separate journal entry.
    Used by purchase-invoice posting, where the invoice's own entry already
    debits Inventory. Records a POSTED StockMovement linked to that entry for traceability.
    """
    qty = Decimal(str(qty))
    unit_cost = Decimal(str(unit_cost))
    total = (qty * unit_cost).quantize(ZERO)
    old_value = product.quantity_on_hand * product.average_cost
    new_qty = product.quantity_on_hand + qty
    new_avg = ((old_value + total) / new_qty).quantize(ZERO) if new_qty else ZERO
    product.quantity_on_hand = new_qty
    product.average_cost = new_avg
    product.save(update_fields=["quantity_on_hand", "average_cost"])
    return StockMovement.objects.create(
        doc_no=_next_stk_no(), product=product, date=date,
        direction=StockMovement.Direction.IN, reason=reason, quantity=qty,
        unit_cost=unit_cost, total_cost=total, qty_after=new_qty, avg_cost_after=new_avg,
        status=StockMovement.Status.POSTED, reference=reference,
        journal_entry=journal_entry, created_by=user,
    )


def apply_issue(product: Product, qty, *, date, reason, reference, journal_entry, user=None):
    """
    Decrease stock at average cost WITHOUT posting a separate journal entry.
    Used by sales-invoice posting (the invoice entry already credits Inventory / debits COGS).
    Returns the COGS value of the issue.
    """
    qty = Decimal(str(qty))
    if qty > product.quantity_on_hand:
        raise AccountingError(
            f"Insufficient stock for {product.code}: on hand {product.quantity_on_hand}, requested {qty}."
        )
    unit = product.average_cost
    total = (qty * unit).quantize(ZERO)
    new_qty = product.quantity_on_hand - qty
    product.quantity_on_hand = new_qty
    product.save(update_fields=["quantity_on_hand"])
    StockMovement.objects.create(
        doc_no=_next_stk_no(), product=product, date=date,
        direction=StockMovement.Direction.OUT, reason=reason, quantity=qty,
        unit_cost=unit, total_cost=total, qty_after=new_qty, avg_cost_after=product.average_cost,
        status=StockMovement.Status.POSTED, reference=reference,
        journal_entry=journal_entry, created_by=user,
    )
    return total


def cogs_preview(product: Product, qty) -> Decimal:
    """COGS value of issuing `qty` at the current average cost (no side effects)."""
    return (Decimal(str(qty)) * product.average_cost).quantize(ZERO)


@transaction.atomic
def post_movement(mv: StockMovement, user=None) -> StockMovement:
    if mv.status == StockMovement.Status.POSTED:
        raise AccountingError("Movement is already posted.")
    product = Product.objects.select_for_update().get(pk=mv.product_id)
    if product.kind != Product.Kind.STOCK:
        raise AccountingError("Only STOCK products can have stock movements.")
    if mv.quantity <= 0:
        raise AccountingError("Quantity must be positive.")

    inv_acct = _inventory_account(product)
    q = mv.quantity

    if mv.direction == StockMovement.Direction.IN:
        if mv.unit_cost <= 0:
            raise AccountingError("Stock-in requires a positive unit cost.")
        total = (q * mv.unit_cost).quantize(ZERO)
        # Weighted-average recalculation.
        old_value = product.quantity_on_hand * product.average_cost
        new_qty = product.quantity_on_hand + q
        new_avg = ((old_value + total) / new_qty).quantize(ZERO) if new_qty else ZERO
        contra = mv.contra_account or _account("3100")  # default: Owner's Capital (opening)

        event = PostingEvent(date=mv.date, source_type="STOCK_IN", source_id=mv.id,
                             memo=f"Stock IN {product.code} ({mv.reason})")
        event.debit(inv_acct, total, memo=f"{q} {product.unit} @ {mv.unit_cost}")
        event.credit(contra, total, memo="Inventory received")

    else:  # OUT
        if q > product.quantity_on_hand:
            raise AccountingError(
                f"Insufficient stock for {product.code}: on hand {product.quantity_on_hand}, requested {q}."
            )
        unit = product.average_cost
        total = (q * unit).quantize(ZERO)
        mv.unit_cost = unit
        new_qty = product.quantity_on_hand - q
        new_avg = product.average_cost  # average cost unchanged on issue
        contra = mv.contra_account or _cogs_account(product)  # default: COGS

        event = PostingEvent(date=mv.date, source_type="STOCK_OUT", source_id=mv.id,
                             memo=f"Stock OUT {product.code} ({mv.reason})")
        event.debit(contra, total, memo=f"COGS {q} {product.unit}")
        event.credit(inv_acct, total, memo=f"{q} {product.unit} @ {unit}")

    entry = PostingService.post(event, user=user)

    # Persist valuation + movement snapshot.
    product.quantity_on_hand = new_qty
    product.average_cost = new_avg
    product.save(update_fields=["quantity_on_hand", "average_cost"])

    mv.total_cost = total
    mv.qty_after = new_qty
    mv.avg_cost_after = new_avg
    mv.contra_account = contra
    mv.journal_entry = entry
    mv.status = StockMovement.Status.POSTED
    mv.save()
    return mv

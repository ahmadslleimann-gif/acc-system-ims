"""
Document cancellation workflow. Posted financial documents are NEVER deleted —
they are cancelled, which reverses their journal entry (and restores any stock),
leaving a fully auditable trail.
"""
from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.journal.models import JournalEntry
from .services import PostingService


def reverse_only_cancel(doc, user=None):
    """Cancel a payment / note: reverse its journal entry, mark CANCELLED."""
    _guard_cancellable(doc)
    with transaction.atomic():
        if doc.journal_entry and doc.journal_entry.status == JournalEntry.Status.POSTED:
            PostingService.reverse(doc.journal_entry, user=user, memo=f"Cancellation of {doc.doc_no}")
        doc.status = "CANCELLED"
        doc.save(update_fields=["status"])
    return doc


def cancel_invoice_with_stock(invoice, user=None, restore_direction="IN"):
    """
    Cancel a posted sales/purchase invoice: reverse the journal entry and undo the
    stock effect by mirroring each linked movement (sales restore IN, purchases OUT).
    """
    from apps.inventory.models import StockMovement
    from apps.inventory import services as inv

    _guard_cancellable(invoice)
    with transaction.atomic():
        reversal = None
        if invoice.journal_entry and invoice.journal_entry.status == JournalEntry.Status.POSTED:
            reversal = PostingService.reverse(invoice.journal_entry, user=user,
                                              memo=f"Cancellation of {invoice.doc_no}")
        # Mirror the stock movements that this invoice produced.
        moves = StockMovement.objects.filter(journal_entry=invoice.journal_entry)
        for mv in moves:
            if restore_direction == "IN" and mv.direction == StockMovement.Direction.OUT:
                inv.apply_receipt(mv.product, mv.quantity, mv.unit_cost, date=invoice.date,
                                  reason="RETURN", reference=f"Cancel {invoice.doc_no}",
                                  journal_entry=reversal, user=user)
            elif restore_direction == "OUT" and mv.direction == StockMovement.Direction.IN:
                inv.apply_issue(mv.product, mv.quantity, date=invoice.date,
                                reason="RETURN", reference=f"Cancel {invoice.doc_no}",
                                journal_entry=reversal, user=user)
        invoice.status = "CANCELLED"
        invoice.save(update_fields=["status"])
    return invoice


def _guard_cancellable(doc):
    status = getattr(doc, "status", None)
    if status == "CANCELLED":
        raise AccountingError("Document is already cancelled.")
    if status == "DRAFT":
        raise AccountingError("Draft documents are deleted, not cancelled.")
    if status != "POSTED":
        raise AccountingError(f"Cannot cancel a document in state '{status}'.")

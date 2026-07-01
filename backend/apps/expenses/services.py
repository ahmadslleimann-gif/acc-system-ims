from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.accounting_engine.services import PostingService, PostingEvent
from .models import Expense


@transaction.atomic
def post_expense(expense: Expense, user=None) -> Expense:
    """Dr Expense (+ Dr VAT Receivable) / Cr Cash-Bank (or AP). Requires APPROVED."""
    if expense.status == Expense.Status.POSTED:
        raise AccountingError("Expense is already posted.")
    if expense.total <= 0:
        raise AccountingError("Expense total must be positive.")

    event = PostingEvent(
        date=expense.date, source_type="EXPENSE", source_id=expense.id,
        memo=f"Expense {expense.doc_no} - {expense.description}",
    )
    event.debit(expense.category.expense_account, expense.amount, memo=expense.description)
    if expense.tax_amount > 0:
        event.debit("VAT_RECEIVABLE", expense.tax_amount, memo="Input VAT")
    credit_account = expense.paid_from_account or "AP"
    event.credit(credit_account, expense.total, memo="Expense paid")

    entry = PostingService.post(event, user=user)
    expense.journal_entry = entry
    expense.status = Expense.Status.POSTED
    expense.save(update_fields=["journal_entry", "status"])
    return expense

from django.db import transaction

from apps.common.exceptions import AccountingError
from apps.accounting_engine.services import PostingService, PostingEvent
from .models import CashTransaction


@transaction.atomic
def post_transaction(tx: CashTransaction, user=None) -> CashTransaction:
    if tx.status == CashTransaction.Status.POSTED:
        raise AccountingError("Transaction is already posted.")
    if tx.amount <= 0:
        raise AccountingError("Amount must be positive.")

    event = PostingEvent(
        date=tx.date, source_type=f"CASH_{tx.type}", source_id=tx.id,
        memo=tx.memo or f"{tx.type} {tx.doc_no}",
    )

    if tx.type == CashTransaction.Type.DEPOSIT:
        if not tx.contra_account:
            raise AccountingError("Deposit requires a contra account.")
        event.debit(tx.account.gl_account, tx.amount, memo="Deposit")
        event.credit(tx.contra_account, tx.amount, memo=tx.memo)

    elif tx.type == CashTransaction.Type.WITHDRAWAL:
        if not tx.contra_account:
            raise AccountingError("Withdrawal requires a contra account.")
        event.debit(tx.contra_account, tx.amount, memo=tx.memo)
        event.credit(tx.account.gl_account, tx.amount, memo="Withdrawal")

    elif tx.type == CashTransaction.Type.TRANSFER:
        if not tx.destination_account:
            raise AccountingError("Transfer requires a destination account.")
        if tx.destination_account_id == tx.account_id:
            raise AccountingError("Source and destination must differ.")
        event.debit(tx.destination_account.gl_account, tx.amount, memo="Transfer in")
        event.credit(tx.account.gl_account, tx.amount, memo="Transfer out")
    else:
        raise AccountingError(f"Unknown transaction type {tx.type}.")

    entry = PostingService.post(event, user=user)
    tx.journal_entry = entry
    tx.status = CashTransaction.Status.POSTED
    tx.save(update_fields=["journal_entry", "status"])
    return tx

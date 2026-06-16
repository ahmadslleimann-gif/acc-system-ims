from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.models import ZERO
from apps.accounts_coa.models import AccountType, Account
from apps.journal.models import JournalEntry, JournalLine


def _sum_doc(model, field, **flt):
    return model.objects.filter(**flt).aggregate(s=Sum(field))["s"] or ZERO


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    from apps.sales.models import SalesInvoice, DocStatus as SDoc
    from apps.purchases.models import PurchaseInvoice, DocStatus as PDoc
    from apps.expenses.models import Expense
    from apps.cashbanks.models import CashBankAccount
    from apps.reports.statements import account_totals

    total_sales = _sum_doc(SalesInvoice, "total", status=SDoc.POSTED)
    total_purchases = _sum_doc(PurchaseInvoice, "total", status=PDoc.POSTED)
    total_expenses = _sum_doc(Expense, "total", status=Expense.Status.POSTED)

    # Cash & bank balances from the GL.
    totals = account_totals()
    cash_balance = ZERO
    bank_balance = ZERO
    for cb in CashBankAccount.objects.select_related("gl_account"):
        t = totals.get(cb.gl_account_id)
        bal = (t["debit"] - t["credit"]) if t else ZERO
        if cb.kind == "BANK":
            bank_balance += bal
        else:
            cash_balance += bal

    # AR / AP from control accounts.
    def control_balance(key):
        from apps.accounts_coa.models import SystemAccount
        try:
            acc = SystemAccount.objects.get(key=key).account
        except SystemAccount.DoesNotExist:
            return ZERO
        t = totals.get(acc.id)
        if not t:
            return ZERO
        net = t["debit"] - t["credit"]
        return net if acc.normal_balance == "DEBIT" else -net

    receivables = control_balance("AR")
    payables = -control_balance("AP")  # AP is credit-normal; show positive payable

    recent = JournalEntry.objects.filter(status=JournalEntry.Status.POSTED).order_by("-entry_date", "-id")[:8]
    recent_data = [
        {"entry_no": e.entry_no, "date": str(e.entry_date), "memo": e.memo,
         "amount": str(e.total_debit), "source_type": e.source_type}
        for e in recent
    ]

    return Response({
        "total_sales": str(total_sales),
        "total_purchases": str(total_purchases),
        "total_expenses": str(total_expenses),
        "cash_balance": str(cash_balance),
        "bank_balance": str(bank_balance),
        "receivables": str(receivables),
        "payables": str(payables),
        "recent_transactions": recent_data,
    })

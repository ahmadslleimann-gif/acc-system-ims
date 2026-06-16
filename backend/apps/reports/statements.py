"""Financial statements computed from posted journal lines (the GL is source of truth)."""
from decimal import Decimal
from django.db.models import Sum, Q

from apps.common.models import ZERO
from apps.accounts_coa.models import Account, AccountType
from apps.journal.models import JournalEntry, JournalLine


def _posted_lines(date_from=None, date_to=None, account_ids=None):
    qs = JournalLine.objects.filter(entry__status=JournalEntry.Status.POSTED)
    if date_from:
        qs = qs.filter(entry__entry_date__gte=date_from)
    if date_to:
        qs = qs.filter(entry__entry_date__lte=date_to)
    if account_ids is not None:
        qs = qs.filter(account_id__in=account_ids)
    return qs


def account_totals(date_from=None, date_to=None):
    """Returns {account_id: {'debit':, 'credit':}} over the period."""
    rows = (
        _posted_lines(date_from, date_to)
        .values("account_id")
        .annotate(debit=Sum("debit"), credit=Sum("credit"))
    )
    return {r["account_id"]: {"debit": r["debit"] or ZERO, "credit": r["credit"] or ZERO} for r in rows}


def trial_balance(date_from=None, date_to=None):
    totals = account_totals(date_from, date_to)
    accounts = Account.objects.filter(id__in=totals.keys()).order_by("code")
    rows = []
    total_debit = ZERO
    total_credit = ZERO
    for acc in accounts:
        d = totals[acc.id]["debit"]
        c = totals[acc.id]["credit"]
        net = d - c
        debit_bal = net if net > 0 else ZERO
        credit_bal = -net if net < 0 else ZERO
        total_debit += debit_bal
        total_credit += credit_bal
        rows.append({
            "code": acc.code, "name": acc.name_en, "type": acc.type,
            "debit": str(debit_bal), "credit": str(credit_bal),
        })
    return {
        "rows": rows,
        "total_debit": str(total_debit),
        "total_credit": str(total_credit),
        "balanced": total_debit == total_credit,
    }


def _type_balance(acc_type, totals):
    """Net balance for all accounts of a type, signed to the type's normal side."""
    accounts = Account.objects.filter(type=acc_type)
    total = ZERO
    for acc in accounts:
        t = totals.get(acc.id)
        if not t:
            continue
        net = t["debit"] - t["credit"]
        # Revenue/Liability/Equity are credit-normal -> flip sign for presentation.
        if acc.normal_balance == "CREDIT":
            net = -net
        total += net
    return total


def income_statement(date_from=None, date_to=None):
    totals = account_totals(date_from, date_to)

    def lines(acc_type):
        out = []
        for acc in Account.objects.filter(type=acc_type).order_by("code"):
            t = totals.get(acc.id)
            if not t:
                continue
            net = t["credit"] - t["debit"] if acc.normal_balance == "CREDIT" else t["debit"] - t["credit"]
            if net != 0:
                out.append({"code": acc.code, "name": acc.name_en, "amount": str(net)})
        return out

    revenue = _type_balance(AccountType.REVENUE, totals)
    expense = _type_balance(AccountType.EXPENSE, totals)
    net_income = revenue - expense
    return {
        "revenue": lines(AccountType.REVENUE),
        "expenses": lines(AccountType.EXPENSE),
        "total_revenue": str(revenue),
        "total_expenses": str(expense),
        "net_income": str(net_income),
    }


def balance_sheet(date_to=None):
    """Cumulative balances up to date_to."""
    totals = account_totals(None, date_to)

    def lines(acc_type):
        out = []
        subtotal = ZERO
        for acc in Account.objects.filter(type=acc_type).order_by("code"):
            t = totals.get(acc.id)
            if not t:
                continue
            net = t["debit"] - t["credit"] if acc.normal_balance == "DEBIT" else t["credit"] - t["debit"]
            if net != 0:
                out.append({"code": acc.code, "name": acc.name_en, "amount": str(net)})
                subtotal += net
        return out, subtotal

    assets, total_assets = lines(AccountType.ASSET)
    liabilities, total_liabilities = lines(AccountType.LIABILITY)
    equity, total_equity = lines(AccountType.EQUITY)

    # Net income for the period flows into equity (retained earnings) for balancing.
    inc = income_statement(None, date_to)
    net_income = Decimal(inc["net_income"])
    total_equity_incl = total_equity + net_income

    return {
        "assets": assets, "total_assets": str(total_assets),
        "liabilities": liabilities, "total_liabilities": str(total_liabilities),
        "equity": equity, "current_earnings": str(net_income),
        "total_equity": str(total_equity_incl),
        "total_liabilities_equity": str(total_liabilities + total_equity_incl),
        "balanced": total_assets == (total_liabilities + total_equity_incl),
    }


def general_ledger(date_from=None, date_to=None, account_id=None):
    account_ids = [account_id] if account_id else None
    lines = (
        _posted_lines(date_from, date_to, account_ids)
        .select_related("account", "entry")
        .order_by("account__code", "entry__entry_date", "entry__id")
    )
    grouped = {}
    for ln in lines:
        key = ln.account.code
        grouped.setdefault(key, {"account": ln.account.name_en, "code": key, "rows": [], "balance": ZERO})
        running = grouped[key]["balance"] + (ln.debit - ln.credit)
        grouped[key]["balance"] = running
        grouped[key]["rows"].append({
            "date": str(ln.entry.entry_date), "entry_no": ln.entry.entry_no,
            "memo": ln.line_memo or ln.entry.memo,
            "debit": str(ln.debit), "credit": str(ln.credit), "balance": str(running),
        })
    for g in grouped.values():
        g["balance"] = str(g["balance"])
    return list(grouped.values())


def cash_flow(date_from=None, date_to=None):
    """Simplified cash flow: net movement of cash/bank GL accounts over the period."""
    from apps.cashbanks.models import CashBankAccount
    cash_account_ids = list(CashBankAccount.objects.values_list("gl_account_id", flat=True))
    totals = account_totals(date_from, date_to)
    inflow = ZERO
    outflow = ZERO
    rows = []
    for acc in Account.objects.filter(id__in=cash_account_ids).order_by("code"):
        t = totals.get(acc.id)
        if not t:
            continue
        net = t["debit"] - t["credit"]
        inflow += t["debit"]
        outflow += t["credit"]
        rows.append({"code": acc.code, "name": acc.name_en, "net_change": str(net)})
    return {
        "rows": rows, "total_inflow": str(inflow),
        "total_outflow": str(outflow), "net_cash_flow": str(inflow - outflow),
    }

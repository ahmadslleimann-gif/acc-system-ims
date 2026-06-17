from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import statements
from .excel import table_excel_response
from .pdf import table_pdf_response


def _range(request):
    return request.query_params.get("from"), request.query_params.get("to")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trial_balance(request):
    d_from, d_to = _range(request)
    return Response(statements.trial_balance(d_from, d_to))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def income_statement(request):
    d_from, d_to = _range(request)
    return Response(statements.income_statement(d_from, d_to))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def balance_sheet(request):
    _, d_to = _range(request)
    return Response(statements.balance_sheet(d_to))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def general_ledger(request):
    d_from, d_to = _range(request)
    account_id = request.query_params.get("account")
    return Response(statements.general_ledger(d_from, d_to, int(account_id) if account_id else None))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cash_flow(request):
    d_from, d_to = _range(request)
    return Response(statements.cash_flow(d_from, d_to))


def _build_export(report, d_from, d_to, request):
    """Return (title, headers, rows, base_filename) for any report, or None."""
    from decimal import Decimal
    from apps.common.models import ZERO

    if report == "trial-balance":
        data = statements.trial_balance(d_from, d_to)
        headers = ["Code", "Account", "Type", "Debit", "Credit"]
        rows = [[r["code"], r["name"], r["type"], r["debit"], r["credit"]] for r in data["rows"]]
        rows.append(["", "TOTAL", "", data["total_debit"], data["total_credit"]])
        return "Trial Balance", headers, rows, "trial_balance"

    if report == "income-statement":
        data = statements.income_statement(d_from, d_to)
        headers = ["Code", "Account", "Amount"]
        rows = [["", "REVENUE", ""]]
        rows += [[r["code"], r["name"], r["amount"]] for r in data["revenue"]]
        rows.append(["", "Total Revenue", data["total_revenue"]])
        rows.append(["", "EXPENSES", ""])
        rows += [[r["code"], r["name"], r["amount"]] for r in data["expenses"]]
        rows.append(["", "Total Expenses", data["total_expenses"]])
        rows.append(["", "NET INCOME", data["net_income"]])
        return "Income Statement", headers, rows, "income_statement"

    if report == "balance-sheet":
        data = statements.balance_sheet(d_to)
        headers = ["Code", "Account", "Amount"]
        rows = [["", "ASSETS", ""]]
        rows += [[r["code"], r["name"], r["amount"]] for r in data["assets"]]
        rows.append(["", "Total Assets", data["total_assets"]])
        rows.append(["", "LIABILITIES", ""])
        rows += [[r["code"], r["name"], r["amount"]] for r in data["liabilities"]]
        rows.append(["", "Total Liabilities", data["total_liabilities"]])
        rows.append(["", "EQUITY", ""])
        rows += [[r["code"], r["name"], r["amount"]] for r in data["equity"]]
        rows.append(["", "Current Earnings", data["current_earnings"]])
        rows.append(["", "Total Equity", data["total_equity"]])
        rows.append(["", "Total Liabilities + Equity", data["total_liabilities_equity"]])
        return "Balance Sheet", headers, rows, "balance_sheet"

    if report == "cash-flow":
        data = statements.cash_flow(d_from, d_to)
        headers = ["Code", "Account", "Net Change"]
        rows = [[r["code"], r["name"], r["net_change"]] for r in data["rows"]]
        rows.append(["", "NET CASH FLOW", data["net_cash_flow"]])
        return "Cash Flow", headers, rows, "cash_flow"

    if report == "general-ledger":
        account_id = request.query_params.get("account")
        data = statements.general_ledger(d_from, d_to, int(account_id) if account_id else None)
        headers = ["Date", "Entry", "Memo", "Debit", "Credit", "Balance"]
        rows = []
        for g in data:
            rows.append([f"{g['code']} - {g['account']}", "", "", "", "", ""])
            for r in g["rows"]:
                rows.append([r["date"], r["entry_no"], r["memo"], r["debit"], r["credit"], r["balance"]])
        return "General Ledger", headers, rows, "general_ledger"

    if report in ("customer-debts", "supplier-debts"):
        from apps.reports.ledgers import partner_balance
        if report == "customer-debts":
            from apps.customers.models import Customer
            partners, kind, who, title = Customer.objects.order_by("code"), "customer", "Customer", "Customer Debts"
        else:
            from apps.suppliers.models import Supplier
            partners, kind, who, title = Supplier.objects.order_by("code"), "supplier", "Supplier", "Supplier Debts"
        headers = ["Code", who, "Balance"]
        rows = []
        total = ZERO
        for p in partners:
            bal = partner_balance(kind, p.id)
            if bal:
                rows.append([p.code, p.name, str(bal)])
                total += Decimal(str(bal))
        rows.append(["", "TOTAL", str(total)])
        return title, headers, rows, report.replace("-", "_")

    if report == "inventory-valuation":
        from apps.inventory.models import Product
        headers = ["Code", "Product", "Qty", "Avg Cost", "Value"]
        rows = []
        total = ZERO
        for p in Product.objects.filter(kind=Product.Kind.STOCK).order_by("code"):
            rows.append([p.code, p.name_en, str(p.quantity_on_hand), str(p.average_cost), str(p.stock_value)])
            total += p.stock_value
        rows.append(["", "TOTAL", "", "", str(total)])
        return "Inventory Valuation", headers, rows, "inventory_valuation"

    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def report_export(request, report):
    d_from, d_to = _range(request)
    built = _build_export(report, d_from, d_to, request)
    if built is None:
        return Response({"detail": f"Unknown report '{report}'."}, status=404)
    title, headers, rows, base = built
    # NB: avoid the reserved DRF "format" query param (it drives content negotiation).
    fmt = request.query_params.get("fmt", "excel")
    if fmt == "pdf":
        return table_pdf_response(title, headers, rows, base + ".pdf")
    return table_excel_response(title, headers, rows, base + ".xlsx")

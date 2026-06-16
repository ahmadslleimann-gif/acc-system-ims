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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trial_balance_export(request):
    d_from, d_to = _range(request)
    data = statements.trial_balance(d_from, d_to)
    headers = ["Code", "Account", "Type", "Debit", "Credit"]
    rows = [[r["code"], r["name"], r["type"], r["debit"], r["credit"]] for r in data["rows"]]
    rows.append(["", "TOTAL", "", data["total_debit"], data["total_credit"]])
    fmt = request.query_params.get("format", "excel")
    if fmt == "pdf":
        return table_pdf_response("Trial Balance", headers, rows, "trial_balance.pdf")
    return table_excel_response("Trial Balance", headers, rows, "trial_balance.xlsx")

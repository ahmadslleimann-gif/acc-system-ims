from django.urls import path
from . import views

urlpatterns = [
    path("trial-balance/", views.trial_balance, name="trial_balance"),
    path("income-statement/", views.income_statement, name="income_statement"),
    path("balance-sheet/", views.balance_sheet, name="balance_sheet"),
    path("general-ledger/", views.general_ledger, name="general_ledger"),
    path("cash-flow/", views.cash_flow, name="cash_flow"),
    # Universal export (?format=pdf | excel) for any report.
    path("<str:report>/export/", views.report_export, name="report_export"),
]

"""
Seed a standard Chart of Accounts, the system-account mapping, and a default
VAT rate. Idempotent: safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts_coa.models import Account, SystemAccount, AccountType

# (code, name_en, name_ar, type, parent_code, is_postable, is_system)
COA = [
    # Assets
    ("1000", "Assets", "الأصول", "ASSET", None, False, False),
    ("1100", "Current Assets", "الأصول المتداولة", "ASSET", "1000", False, False),
    ("1110", "Cash on Hand", "النقدية", "ASSET", "1100", True, True),
    ("1120", "Bank Account", "الحساب البنكي", "ASSET", "1100", True, False),
    ("1130", "Accounts Receivable", "الذمم المدينة", "ASSET", "1100", True, True),
    ("1140", "VAT Receivable", "ضريبة القيمة المضافة - مدخلات", "ASSET", "1100", True, True),
    ("1150", "Inventory", "المخزون", "ASSET", "1100", True, False),
    ("1500", "Fixed Assets", "الأصول الثابتة", "ASSET", "1000", False, False),
    ("1510", "Equipment", "المعدات", "ASSET", "1500", True, False),
    # Liabilities
    ("2000", "Liabilities", "الخصوم", "LIABILITY", None, False, False),
    ("2100", "Current Liabilities", "الخصوم المتداولة", "LIABILITY", "2000", False, False),
    ("2110", "Accounts Payable", "الذمم الدائنة", "LIABILITY", "2100", True, True),
    ("2120", "VAT Payable", "ضريبة القيمة المضافة - مخرجات", "LIABILITY", "2100", True, True),
    # Equity
    ("3000", "Equity", "حقوق الملكية", "EQUITY", None, False, False),
    ("3100", "Owner's Capital", "رأس المال", "EQUITY", "3000", True, False),
    ("3200", "Retained Earnings", "الأرباح المحتجزة", "EQUITY", "3000", True, True),
    # Revenue
    ("4000", "Revenue", "الإيرادات", "REVENUE", None, False, False),
    ("4100", "Sales Revenue", "إيرادات المبيعات", "REVENUE", "4000", True, True),
    ("4200", "Sales Returns", "مردودات المبيعات", "REVENUE", "4000", True, True),
    # Expenses
    ("5000", "Expenses", "المصروفات", "EXPENSE", None, False, False),
    ("5100", "Cost of Goods Sold / Purchases", "تكلفة المبيعات / المشتريات", "EXPENSE", "5000", True, True),
    ("5150", "Purchase Returns", "مردودات المشتريات", "EXPENSE", "5000", True, True),
    ("5200", "Rent Expense", "مصروف الإيجار", "EXPENSE", "5000", True, False),
    ("5300", "Salaries Expense", "مصروف الرواتب", "EXPENSE", "5000", True, False),
    ("5400", "Utilities Expense", "مصروف المرافق", "EXPENSE", "5000", True, False),
    ("5500", "General & Admin Expense", "مصروفات عمومية وإدارية", "EXPENSE", "5000", True, False),
    ("5900", "Rounding Differences", "فروقات التقريب", "EXPENSE", "5000", True, True),
]

SYSTEM_MAP = {
    "CASH": "1110",
    "AR": "1130",
    "VAT_RECEIVABLE": "1140",
    "AP": "2110",
    "VAT_PAYABLE": "2120",
    "RETAINED_EARNINGS": "3200",
    "SALES": "4100",
    "SALES_RETURNS": "4200",
    "PURCHASES": "5100",
    "PURCHASE_RETURNS": "5150",
    "ROUNDING": "5900",
}


class Command(BaseCommand):
    help = "Seed chart of accounts, system accounts and a default VAT rate."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        by_code = {}
        for code, en, ar, typ, parent_code, postable, system in COA:
            parent = by_code.get(parent_code) if parent_code else None
            acc, was_created = Account.objects.get_or_create(
                code=code,
                defaults=dict(name_en=en, name_ar=ar, type=typ, parent=parent,
                              is_postable=postable, is_system=system),
            )
            by_code[code] = acc
            created += int(was_created)

        for key, code in SYSTEM_MAP.items():
            SystemAccount.objects.get_or_create(key=key, defaults={"account": by_code[code]})

        # Default VAT rate + company default.
        from apps.company.models import TaxRate, CompanyProfile
        vat, _ = TaxRate.objects.get_or_create(name="VAT 15%", defaults={"rate_percent": 15})
        company = CompanyProfile.get_solo()
        if not company.default_tax_rate:
            company.default_tax_rate = vat
            company.save(update_fields=["default_tax_rate"])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded CoA ({created} new accounts), {len(SYSTEM_MAP)} system accounts, default VAT."
        ))

"""Seed the four standard roles (Groups) with granular permissions. Idempotent."""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Role -> list of "app_label.codename" permissions. "*" means all on that app's models.
ROLES = {
    "Super Admin": ["*"],
    "Accountant": [
        # Books & ledger
        "accounts_coa.add_account", "accounts_coa.change_account", "accounts_coa.view_account",
        "journal.add_journalentry", "journal.change_journalentry", "journal.view_journalentry", "journal.delete_journalentry",
        # Receivables / payables documents
        "sales.add_salesinvoice", "sales.change_salesinvoice", "sales.view_salesinvoice",
        "sales.add_customerpayment", "sales.change_customerpayment", "sales.view_customerpayment",
        "sales.add_creditnote", "sales.change_creditnote", "sales.view_creditnote",
        "sales.view_quotation",
        "purchases.add_purchaseinvoice", "purchases.change_purchaseinvoice", "purchases.view_purchaseinvoice",
        "purchases.add_supplierpayment", "purchases.change_supplierpayment", "purchases.view_supplierpayment",
        "purchases.add_debitnote", "purchases.change_debitnote", "purchases.view_debitnote",
        # Expenses
        "expenses.add_expense", "expenses.change_expense", "expenses.view_expense",
        "expenses.add_expensecategory", "expenses.change_expensecategory", "expenses.view_expensecategory",
        # Inventory: may view cost + product-suppliers + stock ledger; manage stock movements/adjustments.
        # NB: cannot edit product *prices* (enforced at the serializer level).
        "inventory.add_product", "inventory.change_product", "inventory.view_product",
        "inventory.add_stockmovement", "inventory.change_stockmovement", "inventory.view_stockmovement",
        "inventory.add_productsupplier", "inventory.change_productsupplier",
        "inventory.delete_productsupplier", "inventory.view_productsupplier",
        # Master data (view)
        "customers.view_customer", "customers.change_customer",
        "suppliers.view_supplier", "suppliers.change_supplier",
    ],
    "Sales Employee": [
        # Sell + collect; quotations. NO cost, NO journal, NO accounts, NO purchases.
        "sales.add_salesinvoice", "sales.change_salesinvoice", "sales.view_salesinvoice",
        "sales.add_quotation", "sales.change_quotation", "sales.view_quotation",
        "sales.add_customerpayment", "sales.view_customerpayment",
        "customers.add_customer", "customers.change_customer", "customers.view_customer",
        # Product view only (cost fields stripped by the serializer for this role).
        "inventory.view_product",
    ],
    "Viewer": [
        # Read-only across operational data. No journal, no cost, no audit.
        "sales.view_salesinvoice", "sales.view_quotation",
        "purchases.view_purchaseinvoice",
        "inventory.view_product",
        "customers.view_customer", "suppliers.view_supplier",
    ],
}


class Command(BaseCommand):
    help = "Seed standard roles (Super Admin, Accountant, Sales Employee, Viewer)."

    def handle(self, *args, **options):
        for role_name, perms in ROLES.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            if perms == ["*"]:
                group.permissions.set(Permission.objects.all())
            else:
                resolved = []
                for p in perms:
                    app_label, codename = p.split(".")
                    qs = Permission.objects.filter(content_type__app_label=app_label, codename=codename)
                    resolved.extend(qs)
                group.permissions.set(resolved)
            self.stdout.write(self.style.SUCCESS(f"Role '{role_name}' -> {group.permissions.count()} perms"))

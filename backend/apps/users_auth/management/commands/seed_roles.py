"""Seed the four standard roles (Groups) with granular permissions. Idempotent."""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Role -> list of "app_label.codename" permissions. "*" means all on that app's models.
ROLES = {
    "Super Admin": ["*"],
    "Accountant": [
        "accounts_coa.add_account", "accounts_coa.change_account", "accounts_coa.view_account",
        "journal.add_journalentry", "journal.change_journalentry", "journal.view_journalentry", "journal.delete_journalentry",
        "sales.add_salesinvoice", "sales.change_salesinvoice", "sales.view_salesinvoice",
        "purchases.add_purchaseinvoice", "purchases.change_purchaseinvoice", "purchases.view_purchaseinvoice",
        "expenses.add_expense", "expenses.change_expense", "expenses.view_expense",
        "inventory.add_product", "inventory.change_product", "inventory.view_product",
        "customers.view_customer", "suppliers.view_supplier",
    ],
    "Sales Employee": [
        "sales.add_salesinvoice", "sales.change_salesinvoice", "sales.view_salesinvoice",
        "customers.add_customer", "customers.change_customer", "customers.view_customer",
    ],
    "Viewer": [
        "accounts_coa.view_account", "journal.view_journalentry",
        "sales.view_salesinvoice", "purchases.view_purchaseinvoice",
        "expenses.view_expense", "customers.view_customer", "suppliers.view_supplier",
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

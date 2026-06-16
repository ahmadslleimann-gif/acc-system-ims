from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .middleware import get_current_user, get_current_ip
from .models import AuditLog

# Models we track in the audit trail. Keep this list explicit to avoid noise.
TRACKED = {
    "journal.JournalEntry",
    "accounts_coa.Account",
    "sales.SalesInvoice",
    "sales.CustomerPayment",
    "sales.CreditNote",
    "purchases.PurchaseInvoice",
    "purchases.SupplierPayment",
    "purchases.DebitNote",
    "cashbanks.CashTransaction",
    "expenses.Expense",
    "inventory.Product",
    "inventory.StockMovement",
    "customers.Customer",
    "suppliers.Supplier",
    "company.FiscalPeriod",
}


def _label(instance):
    return f"{instance._meta.app_label}.{instance.__class__.__name__}"


@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    label = _label(instance) if hasattr(instance, "_meta") else ""
    if label not in TRACKED:
        return
    AuditLog.objects.create(
        user=get_current_user() if getattr(get_current_user(), "is_authenticated", False) else None,
        action=AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE,
        model=label,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=get_current_ip(),
    )


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    label = _label(instance) if hasattr(instance, "_meta") else ""
    if label not in TRACKED:
        return
    AuditLog.objects.create(
        user=get_current_user() if getattr(get_current_user(), "is_authenticated", False) else None,
        action=AuditLog.Action.DELETE,
        model=label,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=get_current_ip(),
    )

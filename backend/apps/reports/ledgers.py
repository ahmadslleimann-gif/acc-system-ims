"""
Sub-ledger queries (customer / supplier statements) derived from source documents.

In this single-company design the AR and AP control accounts are reconciled by
construction: every posted customer/supplier document hits AR/AP, and these
document-based sub-ledgers sum to the same control-account balance in the GL.
"""
from decimal import Decimal
from apps.common.models import ZERO


def _as_date(value):
    return value or None


def partner_balance(kind: str, partner_id: int) -> Decimal:
    """
    Outstanding balance for a customer (receivable) or supplier (payable).
    Only CREDIT invoices create debt — cash invoices are settled on the spot.
    Balance = credit invoices − payments − return notes.
    """
    if kind == "customer":
        from apps.sales.models import SalesInvoice, CustomerPayment, CreditNote, DocStatus, PaymentType
        invoices = SalesInvoice.objects.filter(customer_id=partner_id, status=DocStatus.POSTED, payment_type=PaymentType.CREDIT)
        payments = CustomerPayment.objects.filter(customer_id=partner_id, status=DocStatus.POSTED)
        notes = CreditNote.objects.filter(customer_id=partner_id, status=DocStatus.POSTED)
        charged = sum((i.total for i in invoices), ZERO)
        credited = sum((p.amount for p in payments), ZERO) + sum((n.total for n in notes), ZERO)
        return charged - credited

    from apps.purchases.models import PurchaseInvoice, SupplierPayment, DebitNote, DocStatus, PaymentType
    invoices = PurchaseInvoice.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED, payment_type=PaymentType.CREDIT)
    payments = SupplierPayment.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED)
    notes = DebitNote.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED)
    charged = sum((i.total for i in invoices), ZERO)
    settled = sum((p.amount for p in payments), ZERO) + sum((n.total for n in notes), ZERO)
    return charged - settled


def partner_debts(kind: str) -> dict:
    """Debts report rows: per partner -> invoices, payments, balance (credit only)."""
    if kind == "customer":
        from apps.customers.models import Customer
        from apps.sales.models import SalesInvoice, CustomerPayment, DocStatus, PaymentType
        partners = Customer.objects.order_by("code")
        inv_model, pay_model, fk = SalesInvoice, CustomerPayment, "customer_id"
    else:
        from apps.suppliers.models import Supplier
        from apps.purchases.models import PurchaseInvoice, SupplierPayment, DocStatus, PaymentType
        partners = Supplier.objects.order_by("code")
        inv_model, pay_model, fk = PurchaseInvoice, SupplierPayment, "supplier_id"

    rows = []
    t_inv = t_pay = t_bal = ZERO
    for p in partners:
        invoices = sum((i.total for i in inv_model.objects.filter(
            **{fk: p.id}, status=DocStatus.POSTED, payment_type=PaymentType.CREDIT)), ZERO)
        payments = sum((x.amount for x in pay_model.objects.filter(
            **{fk: p.id}, status=DocStatus.POSTED)), ZERO)
        balance = invoices - payments
        if invoices == 0 and balance == 0:
            continue
        rows.append({"code": p.code, "name": p.name,
                     "invoices": str(invoices), "payments": str(payments), "balance": str(balance)})
        t_inv += invoices; t_pay += payments; t_bal += balance
    return {"rows": rows, "total_invoices": str(t_inv), "total_payments": str(t_pay), "total_balance": str(t_bal)}


def partner_ledger(kind: str, partner_id: int, date_from=None, date_to=None) -> dict:
    """Chronological statement of documents with a running balance."""
    rows = []
    if kind == "customer":
        from apps.sales.models import SalesInvoice, CustomerPayment, CreditNote, DocStatus
        for i in SalesInvoice.objects.filter(customer_id=partner_id, status=DocStatus.POSTED):
            rows.append((i.date, i.doc_no, "Invoice", i.total, ZERO))
        for p in CustomerPayment.objects.filter(customer_id=partner_id, status=DocStatus.POSTED):
            rows.append((p.date, p.doc_no, "Payment", ZERO, p.amount))
        for n in CreditNote.objects.filter(customer_id=partner_id, status=DocStatus.POSTED):
            rows.append((n.date, n.doc_no, "Credit Note", ZERO, n.total))
    else:
        from apps.purchases.models import PurchaseInvoice, SupplierPayment, DebitNote, DocStatus
        for i in PurchaseInvoice.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED):
            rows.append((i.date, i.doc_no, "Invoice", i.total, ZERO))
        for p in SupplierPayment.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED):
            rows.append((p.date, p.doc_no, "Payment", ZERO, p.amount))
        for n in DebitNote.objects.filter(supplier_id=partner_id, status=DocStatus.POSTED):
            rows.append((n.date, n.doc_no, "Debit Note", ZERO, n.total))

    rows.sort(key=lambda r: (r[0], r[1]))
    if date_from:
        rows = [r for r in rows if str(r[0]) >= date_from]
    if date_to:
        rows = [r for r in rows if str(r[0]) <= date_to]

    running = ZERO
    out = []
    for date, doc_no, doc_type, debit, credit in rows:
        running += debit - credit
        out.append({
            "date": str(date), "doc_no": doc_no, "type": doc_type,
            "debit": str(debit), "credit": str(credit), "balance": str(running),
        })
    return {"rows": out, "closing_balance": str(running)}

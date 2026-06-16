from django.db import models
from apps.common.models import TimeStampedModel, money_field
from apps.accounts_coa.models import Account
from apps.company.models import TaxRate
from apps.journal.models import JournalEntry


class Product(TimeStampedModel):
    """
    A product or service in the catalog.

    STOCK products are tracked perpetually with weighted-average cost:
    `quantity_on_hand` and `average_cost` are maintained by stock movements.
    SERVICE products are not stock-tracked (no quantity / valuation).
    """

    class Kind(models.TextChoices):
        STOCK = "STOCK", "Stock item"
        SERVICE = "SERVICE", "Service"

    code = models.CharField(max_length=40, unique=True)
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.STOCK)
    barcode = models.CharField(max_length=64, blank=True)
    unit = models.CharField(max_length=24, default="pcs")  # pcs, kg, box...

    sale_price = money_field()
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    # Perpetual valuation (maintained by StockMovement; read-only from the UI).
    quantity_on_hand = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    average_cost = money_field()
    reorder_level = models.DecimalField(max_digits=16, decimal_places=3, default=0)

    # GL account links (default to system accounts when omitted).
    inventory_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    cogs_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    sales_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    @property
    def stock_value(self):
        return (self.quantity_on_hand * self.average_cost) if self.kind == self.Kind.STOCK else 0

    @property
    def is_low_stock(self):
        return self.kind == self.Kind.STOCK and self.quantity_on_hand <= self.reorder_level

    def __str__(self):
        return f"{self.code} · {self.name_en}"


class StockMovement(TimeStampedModel):
    """
    A single inventory movement. IN adds stock (purchase / opening / adjustment-up),
    OUT removes stock (sale / issue / adjustment-down). Each posted movement creates
    a balanced journal entry via the accounting engine.

    IN  : Dr Inventory            / Cr contra (AP, Cash, Capital...)
    OUT : Dr contra (usually COGS) / Cr Inventory   (valued at average cost)
    """

    class Direction(models.TextChoices):
        IN = "IN", "Stock In"
        OUT = "OUT", "Stock Out"

    class Reason(models.TextChoices):
        OPENING = "OPENING", "Opening balance"
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale / Issue"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        RETURN = "RETURN", "Return"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"

    doc_no = models.CharField(max_length=30, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    date = models.DateField()
    direction = models.CharField(max_length=3, choices=Direction.choices)
    reason = models.CharField(max_length=12, choices=Reason.choices, default=Reason.ADJUSTMENT)

    quantity = models.DecimalField(max_digits=16, decimal_places=3)
    unit_cost = money_field()       # required for IN; auto = average_cost for OUT
    total_cost = money_field()

    # Offsetting GL account. IN: source of value (AP/Cash/Capital). OUT: usually COGS.
    contra_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    # Snapshot of valuation after this movement (audit trail).
    qty_after = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    avg_cost_after = money_field()

    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    reference = models.CharField(max_length=120, blank=True)
    journal_entry = models.OneToOneField(JournalEntry, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.doc_no} {self.direction} {self.quantity} x {self.product.code}"

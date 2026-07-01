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

    sale_price = money_field()  # default/base price (kept for compatibility)
    # Three selling-price tiers. Only admins may change these (enforced in the serializer).
    price_retail = money_field()      # مفرّق
    price_wholesale = money_field()   # جملة
    price_bulk = money_field()        # جملة الجملة
    # Cost & guard-rails — admin-only to edit; cost is hidden from sales roles entirely.
    cost_price = money_field()                       # manually-set standard cost
    minimum_selling_price = money_field()            # hard floor; sales cannot go below
    max_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.ForeignKey(TaxRate, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    def price_for_tier(self, tier: str):
        """Official selling price for a tier ('RETAIL'|'WHOLESALE'|'BULK'); falls back to sale_price."""
        mapping = {
            "RETAIL": self.price_retail,
            "WHOLESALE": self.price_wholesale,
            "BULK": self.price_bulk,
        }
        v = mapping.get((tier or "RETAIL").upper(), self.price_retail)
        return v if v and v > 0 else self.sale_price

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
        constraints = [
            models.CheckConstraint(check=models.Q(minimum_selling_price__gte=0), name="prod_min_price_nonneg"),
            models.CheckConstraint(check=models.Q(cost_price__gte=0), name="prod_cost_nonneg"),
            models.CheckConstraint(
                check=models.Q(max_discount_percent__gte=0) & models.Q(max_discount_percent__lte=100),
                name="prod_discount_range",
            ),
        ]

    @property
    def stock_value(self):
        return (self.quantity_on_hand * self.average_cost) if self.kind == self.Kind.STOCK else 0

    @property
    def is_low_stock(self):
        return self.kind == self.Kind.STOCK and self.quantity_on_hand <= self.reorder_level

    def __str__(self):
        return f"{self.code} · {self.name_en}"


class ProductSupplier(TimeStampedModel):
    """
    Links a product to a supplier that sells it, with that supplier's cost.
    The same item can come from several suppliers, each with its own price.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="suppliers")
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.CASCADE, related_name="products")
    supplier_item_code = models.CharField(max_length=64, blank=True)  # supplier's own SKU
    cost = money_field()                # current/agreed purchase cost
    last_purchase_price = money_field()  # auto-updated from purchase invoices
    is_preferred = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-is_preferred", "cost"]
        constraints = [
            models.UniqueConstraint(fields=["product", "supplier"], name="uniq_product_supplier"),
        ]

    def __str__(self):
        return f"{self.product.code} @ {self.supplier.name}"


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

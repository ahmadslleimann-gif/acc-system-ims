from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel, money_field


class CompanyProfile(TimeStampedModel):
    """Singleton holding company-wide settings (single-company system)."""

    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    legal_name = models.CharField(max_length=200, blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    base_currency = models.CharField(max_length=3, default="USD")
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)  # 1=Jan
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="company/", blank=True, null=True)
    default_tax_rate = models.ForeignKey(
        "TaxRate", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "Company profile"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name_en": "My Company"})
        return obj

    def __str__(self):
        return self.name_en


class TaxRate(TimeStampedModel):
    """VAT / sales-tax rate, e.g. 'VAT 15%'."""

    name = models.CharField(max_length=64)
    rate_percent = models.DecimalField(max_digits=6, decimal_places=3)  # e.g. 15.000
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def fraction(self):
        return self.rate_percent / 100

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"


class FiscalPeriod(TimeStampedModel):
    """A locked-or-open accounting period. Posting into a CLOSED period is rejected."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=64)  # e.g. "2026-06"
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-start_date"]

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("end_date cannot be before start_date.")

    def __str__(self):
        return f"{self.name} [{self.status}]"

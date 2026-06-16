from decimal import Decimal
from django.conf import settings
from django.db import models

# Money: 19 digits, 4 decimal places. NEVER use FloatField for money.
MONEY_MAX_DIGITS = 19
MONEY_DECIMAL_PLACES = 4
ZERO = Decimal("0.0000")


def money_field(**kwargs):
    kwargs.setdefault("max_digits", MONEY_MAX_DIGITS)
    kwargs.setdefault("decimal_places", MONEY_DECIMAL_PLACES)
    kwargs.setdefault("default", ZERO)
    return models.DecimalField(**kwargs)


class TimeStampedModel(models.Model):
    """Base model: created/updated timestamps + created_by/updated_by audit columns."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

from apps.common.exceptions import AccountingError


def assert_period_open(entry_date):
    """Reject postings that fall inside a CLOSED fiscal period."""
    from apps.company.models import FiscalPeriod

    closed = FiscalPeriod.objects.filter(
        status=FiscalPeriod.Status.CLOSED,
        start_date__lte=entry_date,
        end_date__gte=entry_date,
    ).exists()
    if closed:
        raise AccountingError(
            f"The fiscal period covering {entry_date} is closed. Posting is not allowed."
        )

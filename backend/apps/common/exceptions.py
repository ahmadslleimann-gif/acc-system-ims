from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


class AccountingError(Exception):
    """Domain error raised by the accounting engine (e.g. unbalanced entry)."""


def custom_exception_handler(exc, context):
    """Render domain errors as clean 400 responses; defer the rest to DRF."""
    if isinstance(exc, AccountingError):
        return Response(
            {"detail": str(exc), "code": "accounting_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return exception_handler(exc, context)

from django.db import transaction
from django.db.models import Max


def next_entry_no(entry_date) -> str:
    """
    Gap-free-ish sequential journal number per fiscal year: JE-YYYY-NNNNNN.
    Uses a max+1 strategy inside the caller's transaction.
    """
    from apps.journal.models import JournalEntry

    year = entry_date.year
    prefix = f"JE-{year}-"
    last = (
        JournalEntry.objects.filter(entry_no__startswith=prefix)
        .aggregate(m=Max("entry_no"))
        .get("m")
    )
    seq = int(last.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{seq:06d}"


def next_document_no(model, prefix: str, field: str = "doc_no") -> str:
    """
    Generic document numbering (invoices, payments...): PREFIX-NNNNNN.
    Computes the max numeric suffix (robust against mixed zero-padding).
    """
    existing = model.objects.filter(**{f"{field}__startswith": f"{prefix}-"}).values_list(field, flat=True)
    max_seq = 0
    for value in existing:
        try:
            max_seq = max(max_seq, int(str(value).rsplit("-", 1)[-1]))
        except (ValueError, IndexError):
            continue
    return f"{prefix}-{max_seq + 1:06d}"

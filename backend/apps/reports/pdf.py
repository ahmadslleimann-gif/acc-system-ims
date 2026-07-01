"""Minimal PDF generation with reportlab (invoices + generic tabular reports)."""
import io
import os
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet


def _company_header():
    from apps.company.models import CompanyProfile
    c = CompanyProfile.get_solo()
    return c.name_en, c.tax_number, c.address


def _logo_path():
    """Find a logo image: company profile upload, else the frontend public logo."""
    from apps.company.models import CompanyProfile
    c = CompanyProfile.get_solo()
    if c.logo and getattr(c.logo, "path", None) and os.path.exists(c.logo.path):
        return c.logo.path
    fallback = os.path.join(settings.BASE_DIR.parent, "frontend", "public", "logo.png")
    return fallback if os.path.exists(fallback) else None


def _logo_flowable(max_h=22 * mm):
    path = _logo_path()
    if not path:
        return None
    try:
        img = Image(path)
        ratio = img.imageWidth / img.imageHeight if img.imageHeight else 1
        img.drawHeight = max_h
        img.drawWidth = max_h * ratio
        img.hAlign = "LEFT"
        return img
    except Exception:
        return None


def invoice_pdf_response(invoice):
    """A simple, clean A4 invoice: company, no/date/time, customer, cash/credit,
    then item · quantity · price · total, with a grand total."""
    from django.utils import timezone

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    name, _, _ = _company_header()

    created = timezone.localtime(invoice.created_at) if invoice.created_at else None
    pay = "Cash" if getattr(invoice, "payment_type", "CASH") == "CASH" else "Credit"

    elements = []
    logo = _logo_flowable(20 * mm)
    if logo:
        elements += [logo, Spacer(1, 4)]
    elements += [
        Paragraph(name, styles["Title"]),
        Spacer(1, 6),
        Paragraph(f"<b>Invoice:</b> {invoice.doc_no}", styles["Normal"]),
        Paragraph(f"<b>Customer:</b> {invoice.customer.name}", styles["Normal"]),
        Paragraph(f"<b>Date:</b> {invoice.date}" + (f" &nbsp; <b>Time:</b> {created:%H:%M}" if created else ""), styles["Normal"]),
        Paragraph(f"<b>Payment:</b> {pay}", styles["Normal"]),
        Spacer(1, 10),
    ]

    data = [["Item", "Qty", "Price", "Total"]]
    for it in invoice.items.all():
        qty = (f"{it.quantity:g}")
        data.append([it.description, qty, f"{it.unit_price:,.2f}", f"{it.line_total:,.2f}"])
    data.append(["", "", "Total", f"{invoice.total:,.2f}"])

    table = Table(data, colWidths=[95 * mm, 25 * mm, 30 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#cbd5e1")),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#0f766e")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements += [table, Spacer(1, 14), Paragraph(f"Thank you — {name}", styles["Italic"])]
    doc.build(elements)
    buf.seek(0)
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{invoice.doc_no}.pdf"'
    return resp


def table_pdf_response(title, headers, rows, filename="report.pdf"):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm)
    styles = getSampleStyleSheet()
    name, _, _ = _company_header()
    elements = []
    logo = _logo_flowable(18 * mm)
    if logo:
        elements += [logo, Spacer(1, 4)]
    elements += [Paragraph(name, styles["Title"]), Paragraph(title, styles["Heading2"]), Spacer(1, 8)]
    data = [headers] + rows
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp

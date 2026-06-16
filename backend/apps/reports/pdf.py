"""Minimal PDF generation with reportlab (invoices + generic tabular reports)."""
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def _company_header():
    from apps.company.models import CompanyProfile
    c = CompanyProfile.get_solo()
    return c.name_en, c.tax_number, c.address


def invoice_pdf_response(invoice):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm)
    styles = getSampleStyleSheet()
    name, tax_no, address = _company_header()

    elements = [
        Paragraph(name, styles["Title"]),
        Paragraph(f"Tax No: {tax_no}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"<b>Invoice {invoice.doc_no}</b>", styles["Heading2"]),
        Paragraph(f"Customer: {invoice.customer.name}", styles["Normal"]),
        Paragraph(f"Date: {invoice.date}", styles["Normal"]),
        Spacer(1, 8),
    ]

    data = [["Description", "Qty", "Unit Price", "Tax", "Total"]]
    for it in invoice.items.all():
        data.append([it.description, str(it.quantity), str(it.unit_price),
                     str(it.tax_amount), str(it.line_total)])
    data.append(["", "", "", "Subtotal", str(invoice.subtotal)])
    data.append(["", "", "", "Tax", str(invoice.tax_amount)])
    data.append(["", "", "", "Total", str(invoice.total)])

    table = Table(data, colWidths=[70 * mm, 20 * mm, 30 * mm, 25 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]))
    elements.append(table)
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
    elements = [Paragraph(name, styles["Title"]), Paragraph(title, styles["Heading2"]), Spacer(1, 8)]
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

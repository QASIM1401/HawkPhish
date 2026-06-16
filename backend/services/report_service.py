"""HawkPhish - Professional PDF Report Generator"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch, cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, HRFlowable, KeepTogether, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from datetime import datetime
from typing import Dict, List


# ── Brand Colors ──────────────────────────────────────────────
BRAND = {
    "primary": "#e94560",
    "dark": "#0f0f23",
    "darker": "#0a0a1a",
    "surface": "#1a1a2e",
    "text": "#2d2d2d",
    "text_light": "#6b7280",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    "border": "#e5e7eb",
    "bg_alt": "#f8fafc",
    "bg_card": "#ffffff",
}


def _hex(c):
    return colors.HexColor(c)


# ── Custom Styles ─────────────────────────────────────────────
def _styles():
    ss = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=ss["Title"],
            fontSize=32, leading=38, textColor=_hex(BRAND["primary"]),
            alignment=TA_CENTER, spaceAfter=8, fontName="Helvetica-Bold",
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=ss["Normal"],
            fontSize=14, leading=18, textColor=_hex(BRAND["text_light"]),
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "cover_version": ParagraphStyle(
            "cover_version", parent=ss["Normal"],
            fontSize=10, textColor=_hex(BRAND["text_light"]),
            alignment=TA_CENTER, spaceAfter=30,
        ),
        "section_title": ParagraphStyle(
            "section_title", parent=ss["Heading1"],
            fontSize=16, leading=22, textColor=_hex(BRAND["dark"]),
            fontName="Helvetica-Bold", spaceBefore=20, spaceAfter=10,
            borderPadding=(0, 0, 4, 0),
        ),
        "subsection": ParagraphStyle(
            "subsection", parent=ss["Heading2"],
            fontSize=12, leading=16, textColor=_hex(BRAND["surface"]),
            fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=ss["Normal"],
            fontSize=10, leading=14, textColor=_hex(BRAND["text"]),
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "body_bold": ParagraphStyle(
            "body_bold", parent=ss["Normal"],
            fontSize=10, leading=14, textColor=_hex(BRAND["text"]),
            fontName="Helvetica-Bold",
        ),
        "stat_big": ParagraphStyle(
            "stat_big", parent=ss["Normal"],
            fontSize=28, leading=32, textColor=_hex(BRAND["primary"]),
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        ),
        "stat_label": ParagraphStyle(
            "stat_label", parent=ss["Normal"],
            fontSize=9, leading=12, textColor=_hex(BRAND["text_light"]),
            alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer", parent=ss["Normal"],
            fontSize=8, textColor=_hex(BRAND["text_light"]),
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer", parent=ss["Normal"],
            fontSize=8, leading=11, textColor=_hex(BRAND["text_light"]),
            alignment=TA_CENTER, spaceAfter=4,
        ),
    }


# ── Header / Footer ──────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header line
    canvas.setStrokeColor(_hex(BRAND["primary"]))
    canvas.setLineWidth(2)
    canvas.line(20*mm, h - 18*mm, w - 20*mm, h - 18*mm)

    # Header text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_hex(BRAND["text_light"]))
    canvas.drawString(20*mm, h - 16*mm, "HawkPhish")
    canvas.drawRightString(w - 20*mm, h - 16*mm, "Confidential — Authorized Use Only")

    # Footer line
    canvas.setStrokeColor(_hex(BRAND["border"]))
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 18*mm, w - 20*mm, 18*mm)

    # Footer text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_hex(BRAND["text_light"]))
    canvas.drawString(20*mm, 13*mm, f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.drawRightString(w - 20*mm, 13*mm, f"Page {doc.page}")

    canvas.restoreState()


def _first_page(canvas, doc):
    """Cover page — no header/footer."""
    pass


# ── Helper: Colored Box ───────────────────────────────────────
def _make_stat_card(label, value, color=BRAND["primary"]):
    """Create a stat card as a table."""
    data = [
        [Paragraph(str(value), ParagraphStyle("sv", fontSize=24, leading=28,
                    textColor=_hex(color), alignment=TA_CENTER, fontName="Helvetica-Bold"))],
        [Paragraph(label, ParagraphStyle("sl", fontSize=9, leading=12,
                    textColor=_hex(BRAND["text_light"]), alignment=TA_CENTER))],
    ]
    t = Table(data, colWidths=[120], rowHeights=[36, 18])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hex(BRAND["bg_alt"])),
        ("BOX", (0, 0), (-1, -1), 1, _hex(BRAND["border"])),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("BOTTOMPADDING", (0, 0), (0, 0), 2),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 6),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return t


def _make_divider(color=None):
    return HRFlowable(width="100%", thickness=1, color=_hex(color or BRAND["border"]), spaceAfter=10, spaceBefore=10)


def _section(title, icon=""):
    prefix = f'<font color="{BRAND["primary"]}">{icon}</font>  ' if icon else ""
    return Paragraph(f'{prefix}{title}',
                     ParagraphStyle("sec", fontSize=14, leading=20,
                                    textColor=_hex(BRAND["dark"]),
                                    fontName="Helvetica-Bold",
                                    spaceBefore=18, spaceAfter=10))


# ── Campaign Report ───────────────────────────────────────────
def generate_campaign_report(campaign: Dict, emails: List[Dict], recipients: List[Dict]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=22*mm, bottomMargin=22*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    s = _styles()
    story = []

    # ── Cover Section ──
    story.append(Spacer(1, 40))
    story.append(Paragraph("HAWKPHISH", s["cover_title"]))
    story.append(Paragraph("Campaign Report", s["cover_subtitle"]))
    story.append(Spacer(1, 6))

    # Campaign name box
    name_data = [[Paragraph(campaign.get("name", "Untitled Campaign"),
                  ParagraphStyle("cn", fontSize=18, leading=24,
                                 textColor=_hex(BRAND["dark"]),
                                 alignment=TA_CENTER, fontName="Helvetica-Bold"))]]
    name_table = Table(name_data, colWidths=[450])
    name_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hex(BRAND["bg_alt"])),
        ("BOX", (0, 0), (-1, -1), 1.5, _hex(BRAND["primary"])),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(name_table)
    story.append(Spacer(1, 12))

    # Status + Date row
    status = campaign.get("status", "unknown").upper()
    status_color = BRAND["success"] if status == "COMPLETED" else BRAND["warning"] if status == "RUNNING" else BRAND["text_light"]
    meta_data = [[
        Paragraph(f'<font color="{BRAND["text_light"]}">Status:</font> <font color="{status_color}"><b>{status}</b></font>',
                  ParagraphStyle("m", fontSize=10, textColor=_hex(BRAND["text"]))),
        Paragraph(f'<font color="{BRAND["text_light"]}">Generated:</font> {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}',
                  ParagraphStyle("m", fontSize=10, textColor=_hex(BRAND["text"]), alignment=TA_RIGHT)),
    ]]
    meta_table = Table(meta_data, colWidths=[225, 225])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hex(BRAND["bg_card"])),
        ("BOX", (0, 0), (-1, -1), 0.5, _hex(BRAND["border"])),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(_make_divider(BRAND["primary"]))
    story.append(Spacer(1, 4))

    # ── Executive Summary ──
    story.append(_section("Executive Summary"))
    total = campaign.get("total_sent", 0) or 1
    opened = campaign.get("total_opened", 0)
    clicked = campaign.get("total_clicked", 0)
    submitted = campaign.get("total_submitted", 0)
    bounced = campaign.get("total_bounced", 0)
    failed = campaign.get("total_failed", 0)

    def _rate(numer, denom=total):
        return round((numer / denom * 100), 1) if denom > 0 else 0.0

    # Stats cards row
    cards = [
        _make_stat_card("Emails Sent", total, BRAND["info"]),
        _make_stat_card("Opened", f"{opened}", BRAND["success"]),
        _make_stat_card("Clicked", f"{clicked}", BRAND["warning"]),
        _make_stat_card("Captured", f"{submitted}", BRAND["danger"]),
    ]
    card_table = Table([cards], colWidths=[112, 112, 112, 112])
    card_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 12))

    # Rates table
    rates_data = [
        ["Metric", "Count", "Rate", "Status"],
        ["Emails Sent", str(campaign.get("total_sent", 0)), "100%", "---"],
        ["Opened", str(opened), f"{_rate(opened)}%",
         "CRITICAL" if _rate(opened) > 50 else "HIGH" if _rate(opened) > 30 else "MEDIUM"],
        ["Clicked", str(clicked), f"{_rate(clicked)}%",
         "CRITICAL" if _rate(clicked) > 30 else "HIGH" if _rate(clicked) > 15 else "MEDIUM"],
        ["Credentials Captured", str(submitted), f"{_rate(submitted)}%",
         "CRITICAL" if submitted > 0 else "NONE"],
        ["Bounced", str(bounced), f"{_rate(bounced)}%", "---"],
        ["Failed", str(failed), f"{_rate(failed)}%", "---"],
    ]

    status_colors = {"CRITICAL": BRAND["danger"], "HIGH": BRAND["warning"], "MEDIUM": BRAND["info"], "LOW": BRAND["success"], "NONE": BRAND["text_light"], "---": BRAND["text_light"]}

    t = Table(rates_data, colWidths=[130, 60, 70, 80])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _hex(BRAND["dark"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 1, _hex(BRAND["border"])),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, _hex(BRAND["primary"])),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hex(BRAND["bg_card"]), _hex(BRAND["bg_alt"])]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]

    for i, row in enumerate(rates_data[1:], 1):
        sc = row[3]
        if sc in status_colors:
            style_cmds.append(("TEXTCOLOR", (3, i), (3, i), _hex(status_colors[sc])))
            style_cmds.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Risk Assessment ──
    if submitted > 0 or clicked > 0:
        story.append(_section("Risk Assessment"))
        risk_level = "CRITICAL" if submitted > 0 else "HIGH" if clicked > 0 else "MEDIUM"
        risk_color = BRAND["danger"] if risk_level == "CRITICAL" else BRAND["warning"] if risk_level == "HIGH" else BRAND["info"]

        risk_text = []
        if submitted > 0:
            risk_text.append(f"<b>{submitted} credential(s) were captured</b> — this represents an immediate security risk requiring remediation.")
        if clicked > 0:
            risk_text.append(f"<b>{clicked} user(s) clicked the phishing link</b> — these users are susceptible to social engineering attacks.")

        risk_para = Paragraph(f'<font color="{risk_color}"><b>Risk Level: {risk_level}</b></font><br/><br/>' + "<br/>".join(risk_text),
                              ParagraphStyle("risk", fontSize=10, leading=14, textColor=_hex(BRAND["text"])))

        risk_box_data = [[risk_para]]
        risk_box = Table(risk_box_data, colWidths=[450])
        risk_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _hex(BRAND["bg_alt"])),
            ("BOX", (0, 0), (-1, -1), 1.5, _hex(risk_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ]))
        story.append(risk_box)
        story.append(Spacer(1, 12))

    # ── Recommendations ──
    story.append(_section("Recommendations"))
    recs = []
    if submitted > 0:
        recs.append("Immediately reset credentials for all compromised accounts")
        recs.append("Enable MFA on all affected accounts")
        recs.append("Conduct targeted security awareness training for captured users")
    if clicked > 0:
        recs.append("Provide phishing awareness training for all users who clicked")
        recs.append("Review and strengthen email filtering rules")
    if _rate(opened) > 40:
        recs.append("Implement stricter email security controls (DMARC, DKIM, SPF)")
    if not recs:
        recs.append("Continue regular phishing simulations to maintain security posture")
        recs.append("Recognize and reward employees who reported the phishing email")

    for i, rec in enumerate(recs, 1):
        story.append(Paragraph(f'<font color="{BRAND["primary"]}"><b>{i}.</b></font>  {rec}', s["body"]))
    story.append(Spacer(1, 10))

    # ── Email Activity Log ──
    if emails:
        story.append(PageBreak())
        story.append(_section("Email Activity Log"))

        email_header = ["#", "Recipient", "Status", "Opened", "Clicked", "Submitted", "IP"]
        email_rows = [email_header]
        for i, e in enumerate(emails[:150], 1):
            email_rows.append([
                str(i),
                Paragraph(e.get("email", "")[:35], ParagraphStyle("em", fontSize=8, leading=10)),
                e.get("status", "").capitalize(),
                e.get("opened_at", "")[:16] if e.get("opened_at") else "---",
                e.get("clicked_at", "")[:16] if e.get("clicked_at") else "---",
                e.get("submitted_at", "")[:16] if e.get("submitted_at") else "---",
                Paragraph(e.get("ip_address", "---")[:20], ParagraphStyle("ip", fontSize=7, leading=9, fontName="Courier")),
            ])

        t2 = Table(email_rows, colWidths=[22, 95, 52, 62, 62, 62, 75])
        t2_style = [
            ("BACKGROUND", (0, 0), (-1, 0), _hex(BRAND["dark"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, _hex(BRAND["border"])),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, _hex(BRAND["primary"])),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hex(BRAND["bg_card"]), _hex(BRAND["bg_alt"])]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        for i, row in enumerate(email_rows[1:], 1):
            status = row[2].lower()
            if status == "submitted":
                t2_style.append(("TEXTCOLOR", (2, i), (2, i), _hex(BRAND["danger"])))
                t2_style.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))
            elif status == "clicked":
                t2_style.append(("TEXTCOLOR", (2, i), (2, i), _hex(BRAND["warning"])))
            elif status == "opened":
                t2_style.append(("TEXTCOLOR", (2, i), (2, i), _hex(BRAND["success"])))

        t2.setStyle(TableStyle(t2_style))
        story.append(t2)

        if len(emails) > 150:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"... and {len(emails) - 150} more entries", s["disclaimer"]))

    # ── Footer Disclaimer ──
    story.append(Spacer(1, 30))
    story.append(_make_divider())
    story.append(Paragraph("CONFIDENTIAL — This report is for authorized security testing purposes only.", s["disclaimer"]))
    story.append(Paragraph("HawkPhish v1.2.0 — Advanced Phishing Simulation Platform", s["disclaimer"]))

    doc.build(story, onFirstPage=_first_page, onLaterPages=_header_footer)
    return buf.getvalue()


# ── Dashboard Summary Report ──────────────────────────────────
# ── JSON & CSV Reports ──────────────────────────────────────────

def generate_campaign_report_json(campaign: Dict, emails: List[Dict], recipients: List[Dict]) -> str:
    import json
    total = campaign.get("total_sent", 0) or 1
    opened = campaign.get("total_opened", 0)
    clicked = campaign.get("total_clicked", 0)
    submitted = campaign.get("total_submitted", 0)
    failed = campaign.get("total_failed", 0)
    bounced = campaign.get("total_bounced", 0)

    rate = round((opened / total * 100), 2) if total > 0 else 0.0
    risk = "CRITICAL" if submitted > 0 else "HIGH" if clicked > 0 else "MEDIUM" if opened > 0 else "LOW"
    recs = []
    if submitted > 0:
        recs = ["Immediately reset credentials for all compromised accounts", "Enable MFA", "Conduct targeted security awareness training"]
    elif clicked > 0:
        recs = ["Provide phishing awareness training", "Review email filtering rules"]
    elif rate > 40:
        recs = ["Implement stricter email security controls (DMARC, DKIM, SPF)", "Continue regular phishing simulations"]
    else:
        recs = ["Continue regular phishing simulations", "Recognize employees who reported the phishing email"]

    report = {
        "meta": {"tool": "HawkPhish", "version": "1.2.0", "generated_at": datetime.utcnow().isoformat()},
        "campaign": campaign,
        "summary": {
            "total_sent": total, "opened": opened, "clicked": clicked,
            "submitted": submitted, "failed": failed, "bounced": bounced,
            "open_rate": f"{rate}%", "risk_level": risk,
        },
        "recommendations": recs,
        "emails": emails,
    }
    return json.dumps(report, indent=2)


def generate_campaign_report_csv(campaign: Dict, emails: List[Dict]) -> str:
    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "test_type", "scenario", "target", "from_email", "status", "opened_at", "clicked_at", "submitted_at", "error"])
    for e in emails:
        writer.writerow([
            e.get("timestamp", ""), "campaign", campaign.get("name", ""),
            e.get("email", ""), campaign.get("from_email", ""),
            e.get("status", ""), e.get("opened_at", ""),
            e.get("clicked_at", ""), e.get("submitted_at", ""),
            e.get("error", ""),
        ])
    return buf.getvalue()


def generate_dashboard_summary(campaigns: List[Dict]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=22*mm, bottomMargin=22*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    s = _styles()
    story = []

    # ── Cover ──
    story.append(Spacer(1, 40))
    story.append(Paragraph("HAWKPHISH", s["cover_title"]))
    story.append(Paragraph("Dashboard Summary Report", s["cover_subtitle"]))
    story.append(Paragraph(f"Generated {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}", s["cover_version"]))
    story.append(_make_divider(BRAND["primary"]))
    story.append(Spacer(1, 8))

    # ── Aggregate Stats ──
    total_sent = sum(c.get("total_sent", 0) for c in campaigns)
    total_opened = sum(c.get("total_opened", 0) for c in campaigns)
    total_clicked = sum(c.get("total_clicked", 0) for c in campaigns)
    total_submitted = sum(c.get("total_submitted", 0) for c in campaigns)
    total_bounced = sum(c.get("total_bounced", 0) for c in campaigns)
    total_failed = sum(c.get("total_failed", 0) for c in campaigns)

    story.append(_section("Overview"))

    cards = [
        _make_stat_card("Campaigns", len(campaigns), BRAND["info"]),
        _make_stat_card("Total Sent", total_sent, BRAND["info"]),
        _make_stat_card("Total Opened", total_opened, BRAND["success"]),
        _make_stat_card("Credentials", total_submitted, BRAND["danger"]),
    ]
    card_table = Table([cards], colWidths=[112, 112, 112, 112])
    card_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 14))

    # Summary table
    open_rate = f"{(total_opened/total_sent*100) if total_sent else 0:.1f}%"
    click_rate = f"{(total_clicked/total_sent*100) if total_sent else 0:.1f}%"
    submit_rate = f"{(total_submitted/total_sent*100) if total_sent else 0:.1f}%"

    summary_data = [
        ["Metric", "Count", "Rate"],
        ["Total Campaigns", str(len(campaigns)), "---"],
        ["Total Emails Sent", str(total_sent), "100%"],
        ["Total Opened", str(total_opened), open_rate],
        ["Total Clicked", str(total_clicked), click_rate],
        ["Total Credentials Captured", str(total_submitted), submit_rate],
        ["Total Bounced", str(total_bounced), f"{(total_bounced/total_sent*100) if total_sent else 0:.1f}%"],
        ["Total Failed", str(total_failed), f"{(total_failed/total_sent*100) if total_sent else 0:.1f}%"],
    ]
    t = Table(summary_data, colWidths=[180, 80, 80])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _hex(BRAND["dark"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 1, _hex(BRAND["border"])),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, _hex(BRAND["primary"])),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hex(BRAND["bg_card"]), _hex(BRAND["bg_alt"])]),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Campaign Breakdown ──
    if campaigns:
        story.append(_section("Campaign Breakdown"))
        cdata = [["Campaign", "Status", "Sent", "Opened", "Clicked", "Submitted"]]
        for c in campaigns:
            cdata.append([
                Paragraph(c.get("name", "")[:30], ParagraphStyle("cn", fontSize=8, leading=10)),
                c.get("status", "").capitalize(),
                str(c.get("total_sent", 0)),
                str(c.get("total_opened", 0)),
                str(c.get("total_clicked", 0)),
                str(c.get("total_submitted", 0)),
            ])

        t2 = Table(cdata, colWidths=[120, 55, 40, 45, 50, 60])
        t2_style = [
            ("BACKGROUND", (0, 0), (-1, 0), _hex(BRAND["primary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, _hex(BRAND["border"])),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, _hex(BRAND["dark"])),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hex(BRAND["bg_card"]), _hex(BRAND["bg_alt"])]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        for i, row in enumerate(cdata[1:], 1):
            status = row[1].lower()
            if status == "completed":
                t2_style.append(("TEXTCOLOR", (1, i), (1, i), _hex(BRAND["success"])))
            elif status == "running":
                t2_style.append(("TEXTCOLOR", (1, i), (1, i), _hex(BRAND["warning"])))
            elif status == "paused":
                t2_style.append(("TEXTCOLOR", (1, i), (1, i), _hex(BRAND["info"])))

        t2.setStyle(TableStyle(t2_style))
        story.append(t2)

    # ── Footer ──
    story.append(Spacer(1, 30))
    story.append(_make_divider())
    story.append(Paragraph("CONFIDENTIAL — This report is for authorized security testing purposes only.", s["disclaimer"]))
    story.append(Paragraph("HawkPhish v1.2.0 — Advanced Phishing Simulation Platform", s["disclaimer"]))

    doc.build(story, onFirstPage=_first_page, onLaterPages=_header_footer)
    return buf.getvalue()

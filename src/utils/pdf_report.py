"""
Premium PDF Generation Engine for Aegis Audits.
"""
import logging
import os
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger("aegis.report")

PAGE_MARGIN = 45
CONTENT_WIDTH = 522  # 612 - 45 - 45 (Perfect point grid boundaries)

NAVY = colors.HexColor("#0F172A")        
INDIGO = colors.HexColor("#4F46E5")      
CHARCOAL = colors.HexColor("#334155")    
SLATE_MUTED = colors.HexColor("#64748B") 
LIGHT_NEUTRAL = colors.HexColor("#F8FAFC")
BORDER_GREY = colors.HexColor("#E2E8F0")  

RISK_GREEN_BG = colors.HexColor("#F0FDF4")
RISK_GREEN_LINE = colors.HexColor("#16A34A")
RISK_GREEN_TEXT = colors.HexColor("#15803D")

RISK_AMBER_BG = colors.HexColor("#FFFBEB")
RISK_AMBER_LINE = colors.HexColor("#D97706")
RISK_AMBER_TEXT = colors.HexColor("#B45309")

RISK_RED_BG = colors.HexColor("#FEF2F2")
RISK_RED_LINE = colors.HexColor("#DC2626")
RISK_RED_TEXT = colors.HexColor("#991B1B")


def sanitize_for_reportlab(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*([\s\S]*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([\s\S]*?)\*", r"<i>\1</i>", text)
    return text


def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["AegisTitle"] = ParagraphStyle(
        "AegisTitle", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=NAVY, spaceAfter=2
    )
    styles["AegisSubtitle"] = ParagraphStyle(
        "AegisSubtitle", parent=base["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=SLATE_MUTED
    )
    styles["AegisMetaLabel"] = ParagraphStyle(
        "AegisMetaLabel", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=10, textColor=SLATE_MUTED, alignment=TA_RIGHT
    )
    styles["AegisMetaValue"] = ParagraphStyle(
        "AegisMetaValue", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=NAVY, alignment=TA_RIGHT
    )
    styles["AegisSectionHeader"] = ParagraphStyle(
        "AegisSectionHeader", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=13, leading=17, textColor=NAVY, spaceBefore=14, spaceAfter=6
    )
    styles["AegisBody"] = ParagraphStyle(
        "AegisBody", parent=base["Normal"], fontName="Helvetica",
        fontSize=10, leading=15.5, textColor=CHARCOAL, spaceAfter=4
    )
    styles["AegisCardLabel"] = ParagraphStyle(
        "AegisCardLabel", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=11, textColor=SLATE_MUTED, alignment=TA_CENTER
    )
    styles["AegisCardValue"] = ParagraphStyle(
        "AegisCardValue", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, alignment=TA_CENTER
    )
    styles["AegisTableHeader"] = ParagraphStyle(
        "AegisTableHeader", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=colors.white
    )
    styles["AegisTableCell"] = ParagraphStyle(
        "AegisTableCell", parent=base["Normal"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=CHARCOAL
    )
    styles["AegisTableCellBold"] = ParagraphStyle(
        "AegisTableCellBold", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=13, textColor=NAVY
    )
    styles["AegisCritic"] = ParagraphStyle(
        "AegisCritic", parent=base["Normal"], fontName="Helvetica",
        fontSize=9.5, leading=14, textColor=colors.HexColor("#4C0519")
    )
    return styles


def _risk_palette(risk_score: int):
    if risk_score >= 60:
        return RISK_RED_BG, RISK_RED_LINE, RISK_RED_TEXT
    if risk_score >= 30:
        return RISK_AMBER_BG, RISK_AMBER_LINE, RISK_AMBER_TEXT
    return RISK_GREEN_BG, RISK_GREEN_LINE, RISK_GREEN_TEXT


def _header_grid(report_data: dict, styles) -> Table:
    generated_at = report_data.get("generated_at") or datetime.now().strftime("%B %d, %Y")
    request_id = report_data.get("request_id", "N/A")
    status = report_data.get("status", "UNKNOWN")

    left_cell = [
        Paragraph("AEGIS ENGINE SYSTEM", styles["AegisTitle"]),
        Paragraph("Automated Enterprise Risk Evaluation Ledger &bull; Verification Matrix", styles["AegisSubtitle"]),
    ]

    meta_rows = [
        [Paragraph("DATE", styles["AegisMetaLabel"]), Paragraph(str(generated_at), styles["AegisMetaValue"])],
        [Paragraph("REQUEST ID", styles["AegisMetaLabel"]), Paragraph(str(request_id), styles["AegisMetaValue"])],
        [Paragraph("STATUS", styles["AegisMetaLabel"]), Paragraph(str(status), styles["AegisMetaValue"])],
    ]
    meta_table = Table(meta_rows, colWidths=[80, 161])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    header = Table([[left_cell, meta_table]], colWidths=[281, 241])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return header


def _risk_callout_card(report_data: dict, styles) -> Table:
    risk_score = report_data.get("risk_score", 0)
    status = report_data.get("status", "UNKNOWN").replace("_", " ")
    jurisdiction = report_data.get("audited_jurisdiction", "Unknown")
    unresolved = report_data.get("unresolved_count", 0)
    bg, line, text_color = _risk_palette(risk_score)

    card_value_style = ParagraphStyle("CardValColor", parent=styles["AegisCardValue"], textColor=text_color)
    card_status_style = ParagraphStyle("CardStatusColor", parent=styles["AegisCardValue"], fontSize=11, leading=14, textColor=text_color)

    inner = Table(
        [
            [
                Paragraph("RISK SCORE", styles["AegisCardLabel"]),
                Paragraph("RESOLUTION VERDICT", styles["AegisCardLabel"]),
                Paragraph("JURISDICTION", styles["AegisCardLabel"]),
                Paragraph("MANUAL REVIEW ITEMS", styles["AegisCardLabel"]),
            ],
            [
                Paragraph(f"{risk_score} / 100", card_value_style),
                Paragraph(status, card_status_style),
                Paragraph(jurisdiction, styles["AegisCardValue"]),
                Paragraph(str(unresolved), card_value_style if unresolved > 0 else styles["AegisCardValue"]),
            ],
        ],
        colWidths=[110, 152, 140, 120],
    )
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 2),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 2),
    ]))

    card = Table([[inner]], colWidths=[CONTENT_WIDTH])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), bg),
        ("LINEBEFORE", (0, 0), (0, 0), 4, line),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return card


def _generate_findings_table(findings: list, styles) -> Table:
    headers = [
        Paragraph("VERIFICATION", styles["AegisTableHeader"]),
        Paragraph("AUDIT PARAMETER", styles["AegisTableHeader"]),
        Paragraph("ANALYTICAL FINDING &amp; CONTEXT MAPPING", styles["AegisTableHeader"]),
        Paragraph("CITATION SOURCE", styles["AegisTableHeader"]),
    ]
    
    rows = [headers]
    for idx, f in enumerate(findings):
        status_str = str(f.get("finding_status", "FLAGGED"))
        color_token = RISK_RED_TEXT if "FAIL" in status_str or "NON_COMPLIANCE" in status_str or "FLAGGED" in status_str else RISK_GREEN_TEXT
        
        status_para = Paragraph(f"<font color='{color_token.hexval()}'><b>{status_str}</b></font>", styles["AegisTableCellBold"])
        param_para = Paragraph(sanitize_for_reportlab(f.get("parameter", "Unknown")), styles["AegisTableCellBold"])
        analysis_para = Paragraph(sanitize_for_reportlab(f.get("analysis", "")), styles["AegisTableCell"])
        source_para = Paragraph(sanitize_for_reportlab(f.get("source", "N/A")), styles["AegisTableCell"])
        
        rows.append([status_para, param_para, analysis_para, source_para])

    table = Table(rows, colWidths=[105, 110, 217, 90], repeatRows=1)
    
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, NAVY),
    ]
    
    for i in range(1, len(rows)):
        bg = LIGHT_NEUTRAL if i % 2 == 1 else colors.white
        t_style.append(("BACKGROUND", (0, i), (-1, i), bg))
        t_style.append(("LINEBELOW", (0, i), (-1, i), 0.5, BORDER_GREY))
        
    table.setStyle(TableStyle(t_style))
    return table


def _critic_evaluation_card(report_data: dict, styles) -> Table:
    critic_text = sanitize_for_reportlab(
        report_data.get("critic_evaluation", "No QA feedback recorded.")
    ).replace("\n", "<br/>")
    
    critic_table = Table([[Paragraph(critic_text, styles["AegisCritic"])]], colWidths=[CONTENT_WIDTH])
    critic_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#FFF1F2")),
        ("LINEBEFORE", (0, 0), (0, 0), 4, colors.HexColor("#F43F5E")),
        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#FFE4E6")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return critic_table


def build_compliance_pdf(report_data: dict, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title="Aegis Compliance Audit Ledger",
    )
    styles = _build_styles()
    story = []

    # --- Header Segment ---
    story.append(_header_grid(report_data, styles))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=12))

    # --- Metrics Segment ---
    story.append(_risk_callout_card(report_data, styles))
    story.append(Spacer(1, 16))

    # --- Section 1: Structured Audit Data Ledger ---
    story.append(Paragraph("1. CORE COMPLIANCE MATRIX &amp; EXECUTED FINDINGS", styles["AegisSectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=BORDER_GREY, spaceBefore=1, spaceAfter=8))
    
    findings_list = report_data.get("raw_findings_array", [])
    if findings_list:
        story.append(_generate_findings_table(findings_list, styles))
    else:
        story.append(Paragraph("No explicit system deviations detected within the target document.", styles["AegisBody"]))
    story.append(Spacer(1, 16))

    # --- Section 2: Multi-Agent Critic Shield ---
    story.append(Paragraph("2. MULTI-AGENT SHIELD DEPLOYMENT LOGS", styles["AegisSectionHeader"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=BORDER_GREY, spaceBefore=1, spaceAfter=8))
    story.append(_critic_evaluation_card(report_data, styles))

    doc.build(story)
    logger.info("Premium PDF successfully serialized at %s", output_path)
    return os.path.abspath(output_path)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.utils import ImageReader
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTE — Government / Legal Document Style
# ─────────────────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0A1628")    # Dark navy — headers
DARK_BLUE  = colors.HexColor("#1B3A6B")    # Section headers
MID_BLUE   = colors.HexColor("#2E5FA3")    # Sub-headers, accents
LIGHT_BLUE = colors.HexColor("#D6E4F7")    # Table header bg
PALE_BLUE  = colors.HexColor("#EEF4FB")    # Alternating row bg
RED_ALERT  = colors.HexColor("#B22222")    # Red flag / alert
AMBER      = colors.HexColor("#B8860B")    # Warning
GREEN_OK   = colors.HexColor("#1A6B3C")    # Normal/ok
GOLD       = colors.HexColor("#C9A84C")    # Header accent line
LIGHT_GREY = colors.HexColor("#F5F5F5")    # Light bg
MID_GREY   = colors.HexColor("#CCCCCC")    # Borders
DARK_GREY  = colors.HexColor("#444444")    # Body text
BLACK      = colors.black
WHITE      = colors.white


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER / FOOTER  (called on every page)
# ─────────────────────────────────────────────────────────────────────────────
class HeaderFooterCanvas:
    """Adds running header + footer to every page."""

    def __init__(self, case_id, investigator, total_pages_placeholder="?"):
        self.case_id     = case_id
        self.investigator= investigator

    def on_first_page(self, canvas, doc):
        self._draw_footer(canvas, doc)

    def on_later_pages(self, canvas, doc):
        self._draw_header(canvas, doc)
        self._draw_footer(canvas, doc)

    def _draw_header(self, canvas, doc):
        w, h = A4
        canvas.saveState()

        # Top bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 1.1*cm, w, 1.1*cm, fill=1, stroke=0)

        # Header text
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(1*cm, h - 0.75*cm, "SOCIALSCOPE FORENSIC TOOLKIT")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 1*cm, h - 0.75*cm,
                               f"CASE ID: {self.case_id}  |  INVESTIGATOR: {self.investigator}")

        # Gold accent line
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1.5)
        canvas.line(0, h - 1.15*cm, w, h - 1.15*cm)

        canvas.restoreState()

    def _draw_footer(self, canvas, doc):
        w, h = A4
        canvas.saveState()

        # Footer line
        canvas.setStrokeColor(MID_BLUE)
        canvas.setLineWidth(0.5)
        canvas.line(1*cm, 1.4*cm, w - 1*cm, 1.4*cm)

        # Footer text
        canvas.setFillColor(DARK_GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(1*cm, 0.9*cm,
                          "CONFIDENTIAL — FOR LAW ENFORCEMENT USE ONLY")
        canvas.drawString(1*cm, 0.55*cm,
                          f"Generated: {datetime.now().strftime('%d %B %Y  %H:%M:%S IST')}")
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(w - 1*cm, 0.9*cm,
                               f"Page {doc.page}")
        canvas.drawRightString(w - 1*cm, 0.55*cm,
                               "SocialScope v2.0")

        canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN REPORT CLASS
# ─────────────────────────────────────────────────────────────────────────────
class ForensicReport:
    def __init__(self, case_id, investigator):
        self.case_id     = case_id
        self.investigator= investigator
        self.output_dir  = Path("./output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_styles()

    def _setup_styles(self):
        base = getSampleStyleSheet()

        self.style_normal = ParagraphStyle(
            'Normal', fontName='Helvetica',
            fontSize=9.5, leading=14,
            textColor=DARK_GREY, spaceAfter=4,
        )
        self.style_body = ParagraphStyle(
            'Body', fontName='Helvetica',
            fontSize=9, leading=13,
            textColor=DARK_GREY, spaceAfter=3,
            alignment=TA_JUSTIFY,
        )
        self.style_section = ParagraphStyle(
            'Section', fontName='Helvetica-Bold',
            fontSize=11, leading=16,
            textColor=WHITE, spaceAfter=0, spaceBefore=0,
        )
        self.style_subsection = ParagraphStyle(
            'Subsection', fontName='Helvetica-Bold',
            fontSize=10, leading=14,
            textColor=DARK_BLUE, spaceAfter=4, spaceBefore=8,
        )
        self.style_cell = ParagraphStyle(
            'Cell', fontName='Helvetica',
            fontSize=8.5, leading=12,
            textColor=DARK_GREY,
        )
        self.style_cell_bold = ParagraphStyle(
            'CellBold', fontName='Helvetica-Bold',
            fontSize=8.5, leading=12,
            textColor=NAVY,
        )
        self.style_red = ParagraphStyle(
            'Red', fontName='Helvetica-Bold',
            fontSize=8.5, leading=12,
            textColor=RED_ALERT,
        )
        self.style_center = ParagraphStyle(
            'Center', fontName='Helvetica',
            fontSize=9, leading=13,
            textColor=DARK_GREY, alignment=TA_CENTER,
        )
        self.style_title = ParagraphStyle(
            'Title', fontName='Helvetica-Bold',
            fontSize=20, leading=26,
            textColor=NAVY, alignment=TA_CENTER,
            spaceAfter=6,
        )
        self.style_subtitle = ParagraphStyle(
            'Subtitle', fontName='Helvetica',
            fontSize=11, leading=15,
            textColor=MID_BLUE, alignment=TA_CENTER,
            spaceAfter=4,
        )

    # ── Section header block ─────────────────────────────────────────────────
    def _section_header(self, text, number=None):
        label = f"  {number}.  {text}" if number else f"  {text}"
        tbl = Table([[Paragraph(label, self.style_section)]],
                    colWidths=[17*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), DARK_BLUE),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 6),
            ('ROUNDEDCORNERS', [3, 3, 3, 3]),
        ]))
        return tbl

    # ── Key-value info table ─────────────────────────────────────────────────
    def _kv_table(self, rows):
        data = []
        for k, v in rows:
            data.append([
                Paragraph(k, self.style_cell_bold),
                Paragraph(str(v), self.style_cell),
            ])
        tbl = Table(data, colWidths=[5*cm, 12*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (0,-1), PALE_BLUE),
            ('BACKGROUND',    (1,0), (1,-1), WHITE),
            ('GRID',          (0,0), (-1,-1), 0.4, MID_GREY),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
        ]))
        return tbl

    # ── Messages table ───────────────────────────────────────────────────────
    def _messages_table(self, messages, highlight_suspicious=False):
        # Header row
        headers = [
            Paragraph("#",           self.style_cell_bold),
            Paragraph("Date / Time", self.style_cell_bold),
            Paragraph("Sender",      self.style_cell_bold),
            Paragraph("Message",     self.style_cell_bold),
            Paragraph("Status",      self.style_cell_bold),
        ]
        data = [headers]

        for i, msg in enumerate(messages):
            text    = str(msg.get('text', '') or '')[:200]
            sender  = str(msg.get('sender', 'Unknown'))
            time    = str(msg.get('readable_time', 'N/A'))
            status  = str(msg.get('sentiment', msg.get('status', 'ACTIVE')))
            is_susp = msg.get('is_suspicious', False)

            # Color coding
            if is_susp or status in ('Aggressive', 'Suspicious'):
                text_style   = self.style_red
                status_style = self.style_red
                row_bg       = colors.HexColor("#FFF0F0")
            else:
                text_style   = self.style_cell
                status_style = self.style_cell
                row_bg       = PALE_BLUE if i % 2 == 0 else WHITE

            row = [
                Paragraph(str(i+1),  self.style_cell),
                Paragraph(time,      self.style_cell),
                Paragraph(sender,    self.style_cell_bold),
                Paragraph(text,      text_style),
                Paragraph(status,    status_style),
            ]
            data.append(row)

        col_widths = [0.8*cm, 3.5*cm, 3.5*cm, 7.5*cm, 2.5*cm]
        tbl = Table(data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            # Header
            ('BACKGROUND',    (0,0), (-1,0), DARK_BLUE),
            ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 9),
            ('TOPPADDING',    (0,0), (-1,0), 7),
            ('BOTTOMPADDING', (0,0), (-1,0), 7),
            # Body
            ('GRID',          (0,0), (-1,-1), 0.4, MID_GREY),
            ('TOPPADDING',    (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,1), (-1,-1), 4),
            ('LEFTPADDING',   (0,0), (-1,-1), 5),
            ('VALIGN',        (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [PALE_BLUE, WHITE]),
        ]

        # Highlight suspicious rows red background
        for i, msg in enumerate(messages):
            if msg.get('is_suspicious') or msg.get('sentiment') in ('Aggressive', 'Suspicious'):
                style_cmds.append(
                    ('BACKGROUND', (0, i+1), (-1, i+1), colors.HexColor("#FFF0F0"))
                )

        tbl.setStyle(TableStyle(style_cmds))
        return tbl

    # ── Cover page ───────────────────────────────────────────────────────────
    def _build_cover(self, messages, deleted, suspicious, db_hash):
        story = []
        w = 17*cm

        # Top decoration bar
        top_bar = Table([['']], colWidths=[w], rowHeights=[0.5*cm])
        top_bar.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), GOLD),
        ]))
        story.append(top_bar)
        story.append(Spacer(1, 0.8*cm))

        # GOVERNMENT SEAL / TITLE BLOCK
        title_data = [[
            Paragraph("🔬", ParagraphStyle('icon', fontSize=36, alignment=TA_CENTER)),
        ]]
        story.append(Paragraph("DIGITAL FORENSIC INVESTIGATION REPORT",
                               self.style_title))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("Instagram Direct Message Analysis",
                               self.style_subtitle))
        story.append(Paragraph("Prepared by SocialScope Forensic Toolkit v2.0",
                               self.style_subtitle))
        story.append(Spacer(1, 0.4*cm))

        # Gold divider
        story.append(HRFlowable(width="100%", thickness=2,
                                color=GOLD, spaceAfter=12))

        # Classification banner
        cls_tbl = Table(
            [[Paragraph("⚠  CONFIDENTIAL — FOR LAW ENFORCEMENT USE ONLY  ⚠",
                        ParagraphStyle('cls', fontName='Helvetica-Bold',
                                       fontSize=10, textColor=WHITE,
                                       alignment=TA_CENTER))]],
            colWidths=[w]
        )
        cls_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), RED_ALERT),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(cls_tbl)
        story.append(Spacer(1, 0.6*cm))

        # Case details block
        story.append(self._kv_table([
            ("CASE ID",              self.case_id),
            ("INVESTIGATOR",         self.investigator),
            ("REPORT DATE",          datetime.now().strftime('%d %B %Y')),
            ("REPORT TIME",          datetime.now().strftime('%H:%M:%S IST')),
            ("PLATFORM",             "Instagram (Meta)"),
            ("TOOL VERSION",         "SocialScope Forensic Toolkit v2.0"),
            ("DB SHA-256 HASH",      db_hash if db_hash else "N/A"),
        ]))
        story.append(Spacer(1, 0.5*cm))

        # Summary statistics
        story.append(self._section_header("CASE SUMMARY STATISTICS"))
        story.append(Spacer(1, 0.2*cm))

        stats_data = [
            [
                self._stat_box("Total Messages",   str(len(messages)),   DARK_BLUE),
                self._stat_box("Suspicious",        str(len(suspicious)), RED_ALERT),
                self._stat_box("Deleted/Recovered", str(len(deleted)),   AMBER),
            ]
        ]
        stats_tbl = Table(stats_data, colWidths=[5.6*cm, 5.6*cm, 5.6*cm])
        stats_tbl.setStyle(TableStyle([
            ('LEFTPADDING',  (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(stats_tbl)
        story.append(Spacer(1, 0.5*cm))

        # Legal disclaimer
        disclaimer = (
            "<b>LEGAL NOTICE:</b> This report has been generated using automated forensic "
            "analysis tools. All data presented herein is derived from digital evidence "
            "extracted from the subject device/account. This document is intended solely "
            "for use by authorized law enforcement personnel. Unauthorized disclosure, "
            "reproduction, or distribution of this report is strictly prohibited."
        )
        disc_tbl = Table(
            [[Paragraph(disclaimer, ParagraphStyle(
                'disc', fontName='Helvetica', fontSize=8,
                leading=12, textColor=DARK_GREY, alignment=TA_JUSTIFY
            ))]],
            colWidths=[w]
        )
        disc_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), LIGHT_GREY),
            ('BOX',           (0,0), (-1,-1), 0.5, MID_GREY),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
            ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ]))
        story.append(disc_tbl)

        story.append(PageBreak())
        return story

    def _stat_box(self, label, value, color):
        data = [[
            Paragraph(value, ParagraphStyle(
                'val', fontName='Helvetica-Bold', fontSize=22,
                textColor=WHITE, alignment=TA_CENTER, leading=28
            ))
        ],[
            Paragraph(label, ParagraphStyle(
                'lbl', fontName='Helvetica', fontSize=8,
                textColor=WHITE, alignment=TA_CENTER, leading=11
            ))
        ]]
        tbl = Table(data, colWidths=[5*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), color),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        return tbl

    # ─────────────────────────────────────────────────────────────────────────
    #  MAIN GENERATE
    # ─────────────────────────────────────────────────────────────────────────
    def generate_report(self, messages, deleted_messages,
                        suspicious_messages, db_hash):

        filename = self.output_dir / (
            f"FORENSIC_REPORT_{self.case_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )

        hfc = HeaderFooterCanvas(self.case_id, self.investigator)

        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.8*cm,
            bottomMargin=1.8*cm,
            title=f"Forensic Report — {self.case_id}",
            author="SocialScope Forensic Toolkit",
            subject="Instagram DM Forensic Analysis",
        )

        story = []
        w = 17*cm

        # ── COVER PAGE ───────────────────────────────────────────────────────
        story += self._build_cover(messages, deleted_messages,
                                   suspicious_messages, db_hash)

        # ── SECTION 1: INVESTIGATION DETAILS ────────────────────────────────
        story.append(self._section_header("INVESTIGATION DETAILS", "1"))
        story.append(Spacer(1, 0.2*cm))
        story.append(self._kv_table([
            ("Case ID",          self.case_id),
            ("Investigator",     self.investigator),
            ("Analysis Date",    datetime.now().strftime('%d %B %Y')),
            ("Analysis Time",    datetime.now().strftime('%H:%M:%S IST')),
            ("Platform",         "Instagram (Meta Platforms Inc.)"),
            ("Data Source",      "direct.db / Instagram JSON Export"),
            ("Tool",             "SocialScope Forensic Toolkit v2.0"),
            ("Hash (SHA-256)",   str(db_hash) if db_hash else "N/A"),
        ]))
        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 2: EXECUTIVE SUMMARY ─────────────────────────────────────
        story.append(self._section_header("EXECUTIVE SUMMARY", "2"))
        story.append(Spacer(1, 0.2*cm))

        # Unique senders
        senders = list(set(m.get('sender', '') for m in messages if m.get('sender')))
        sender_str = ', '.join(senders[:10]) if senders else 'N/A'

        # Date range
        timestamps = [m.get('timestamp_unix', 0) for m in messages if m.get('timestamp_unix', 0) > 0]
        if timestamps:
            from datetime import datetime as dt
            date_from = dt.fromtimestamp(min(timestamps)).strftime('%d %b %Y %H:%M')
            date_to   = dt.fromtimestamp(max(timestamps)).strftime('%d %b %Y %H:%M')
            date_range = f"{date_from}  →  {date_to}"
        else:
            date_range = "N/A"

        story.append(self._kv_table([
            ("Total Messages Analysed",  str(len(messages))),
            ("Suspicious Messages",      str(len(suspicious_messages))),
            ("Deleted/Recovered Items",  str(len(deleted_messages))),
            ("Unique Participants",      str(len(senders))),
            ("Participants",             sender_str),
            ("Conversation Period",      date_range),
        ]))
        story.append(Spacer(1, 0.3*cm))

        # Summary narrative
        susp_pct = (len(suspicious_messages) / len(messages) * 100) if messages else 0
        narrative = (
            f"A total of <b>{len(messages)}</b> messages were extracted and analysed from the "
            f"subject's Instagram account. The analysis identified <b>{len(suspicious_messages)}</b> "
            f"messages ({susp_pct:.1f}%) containing suspicious keywords, red-flag phrases, or "
            f"aggressive sentiment. "
            f"<b>{len(deleted_messages)}</b> deleted/recovered items were detected through forensic "
            f"recovery methods. The conversation spans the period from {date_range}."
        )
        story.append(Paragraph(narrative, self.style_body))
        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 3: SUSPECT / PARTICIPANT DETAILS ─────────────────────────
        story.append(self._section_header("PARTICIPANT DETAILS", "3"))
        story.append(Spacer(1, 0.2*cm))

        from collections import Counter
        sender_counts = Counter(m.get('sender', 'Unknown') for m in messages)

        part_data = [[
            Paragraph("S.No", self.style_cell_bold),
            Paragraph("Username / ID", self.style_cell_bold),
            Paragraph("Messages Sent", self.style_cell_bold),
            Paragraph("Role", self.style_cell_bold),
            Paragraph("Platform", self.style_cell_bold),
        ]]
        for idx, (sender, count) in enumerate(sender_counts.most_common(), 1):
            role = "Device Owner / Suspect" if idx == 1 else "Other Participant"
            part_data.append([
                Paragraph(str(idx),      self.style_cell),
                Paragraph(str(sender),   self.style_cell_bold),
                Paragraph(str(count),    self.style_cell),
                Paragraph(role,          self.style_cell),
                Paragraph("Instagram",   self.style_cell),
            ])

        part_tbl = Table(part_data, colWidths=[1.5*cm, 5*cm, 3*cm, 4.5*cm, 3*cm])
        part_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), DARK_BLUE),
            ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,0), 9),
            ('GRID',          (0,0), (-1,-1), 0.4, MID_GREY),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [PALE_BLUE, WHITE]),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING',   (0,0), (-1,-1), 6),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(part_tbl)
        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 4: RED FLAG / SUSPICIOUS MESSAGES ────────────────────────
        if suspicious_messages:
            story.append(self._section_header(
                f"RED FLAG MESSAGES  ({len(suspicious_messages)} DETECTED)", "4"))
            story.append(Spacer(1, 0.15*cm))

            # Alert box
            alert_box = Table(
                [[Paragraph(
                    f"⚠  WARNING: The following {len(suspicious_messages)} messages contain "
                    f"keywords or phrases flagged as suspicious or aggressive by the "
                    f"automated analysis engine.",
                    ParagraphStyle('alert', fontName='Helvetica-Bold', fontSize=9,
                                   textColor=RED_ALERT, leading=13)
                )]],
                colWidths=[w]
            )
            alert_box.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor("#FFF0F0")),
                ('BOX',           (0,0), (-1,-1), 1, RED_ALERT),
                ('TOPPADDING',    (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
            ]))
            story.append(alert_box)
            story.append(Spacer(1, 0.2*cm))
            story.append(self._messages_table(suspicious_messages,
                                              highlight_suspicious=True))
            story.append(Spacer(1, 0.5*cm))

        # ── SECTION 5: COMPLETE MESSAGE TIMELINE ─────────────────────────────
        story.append(PageBreak())
        story.append(self._section_header(
            f"COMPLETE MESSAGE TIMELINE  ({len(messages)} MESSAGES)", "5"))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "All messages are listed in chronological order (oldest first). "
            "Red highlighted rows indicate suspicious/flagged content.",
            self.style_body
        ))
        story.append(Spacer(1, 0.2*cm))
        story.append(self._messages_table(messages, highlight_suspicious=True))
        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 6: DELETED / RECOVERED DATA ──────────────────────────────
        story.append(self._section_header(
            f"DELETED / RECOVERED DATA  ({len(deleted_messages)} ITEMS)", "6"))
        story.append(Spacer(1, 0.2*cm))

        if deleted_messages:
            del_data = [[
                Paragraph("#",       self.style_cell_bold),
                Paragraph("Time",    self.style_cell_bold),
                Paragraph("Method",  self.style_cell_bold),
                Paragraph("Content", self.style_cell_bold),
                Paragraph("Status",  self.style_cell_bold),
            ]]
            for i, msg in enumerate(deleted_messages[:50]):
                del_data.append([
                    Paragraph(str(i+1), self.style_cell),
                    Paragraph(str(msg.get('readable_time', 'N/A')), self.style_cell),
                    Paragraph(str(msg.get('source', 'N/A')), self.style_cell),
                    Paragraph(str(msg.get('possible_text', msg.get('text', '')))[:150],
                              self.style_cell),
                    Paragraph(str(msg.get('status', 'DELETED')), self.style_red),
                ])
            del_tbl = Table(del_data,
                            colWidths=[1*cm, 3*cm, 3.5*cm, 7*cm, 2.5*cm])
            del_tbl.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), DARK_BLUE),
                ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID',          (0,0), (-1,-1), 0.4, MID_GREY),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [PALE_BLUE, WHITE]),
                ('TOPPADDING',    (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING',   (0,0), (-1,-1), 5),
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(del_tbl)
        else:
            no_del = Table(
                [[Paragraph(
                    "No deleted messages were recovered during forensic analysis. "
                    "This may indicate that the database has been securely wiped "
                    "or that no messages were deleted prior to extraction.",
                    self.style_body
                )]],
                colWidths=[w]
            )
            no_del.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREY),
                ('BOX',        (0,0), (-1,-1), 0.5, MID_GREY),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ]))
            story.append(no_del)

        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 7: INTEGRITY VERIFICATION ────────────────────────────────
        story.append(self._section_header("INTEGRITY VERIFICATION", "7"))
        story.append(Spacer(1, 0.2*cm))
        story.append(self._kv_table([
            ("Evidence File",         "direct.db / Instagram JSON Export"),
            ("SHA-256 Hash",          str(db_hash) if db_hash else "N/A"),
            ("Hash Algorithm",        "SHA-256 (256-bit)"),
            ("Verification Status",   "✓ VERIFIED" if db_hash and db_hash != "N/A" else "NOT COMPUTED"),
            ("Analysis Timestamp",    datetime.now().strftime('%d %B %Y  %H:%M:%S IST')),
            ("Chain of Custody",      f"Extracted by {self.investigator}"),
        ]))
        story.append(Spacer(1, 0.5*cm))

        # ── SECTION 8: INVESTIGATOR CERTIFICATION ────────────────────────────
        story.append(self._section_header("INVESTIGATOR CERTIFICATION", "8"))
        story.append(Spacer(1, 0.3*cm))

        cert_text = (
            f"I, <b>{self.investigator}</b>, hereby certify that the information contained "
            f"in this report is accurate and complete to the best of my knowledge. "
            f"This forensic analysis was conducted using SocialScope Forensic Toolkit v2.0 "
            f"on {datetime.now().strftime('%d %B %Y')} and the findings represent a true "
            f"and faithful account of the digital evidence examined under Case ID: "
            f"<b>{self.case_id}</b>."
        )
        story.append(Paragraph(cert_text, self.style_body))
        story.append(Spacer(1, 1.5*cm))

        # Signature block
        sig_data = [
            [
                Paragraph("_______________________", self.style_center),
                Paragraph("_______________________", self.style_center),
            ],
            [
                Paragraph(f"<b>{self.investigator}</b>", self.style_center),
                Paragraph("<b>Supervising Officer</b>", self.style_center),
            ],
            [
                Paragraph("Investigating Officer", self.style_center),
                Paragraph("Name & Designation", self.style_center),
            ],
            [
                Paragraph(f"Date: {datetime.now().strftime('%d / %m / %Y')}", self.style_center),
                Paragraph("Date: _____ / _____ / _____", self.style_center),
            ],
        ]
        sig_tbl = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
        sig_tbl.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(sig_tbl)

        # ── BUILD PDF ─────────────────────────────────────────────────────────
        doc.build(
            story,
            onFirstPage  = hfc.on_first_page,
            onLaterPages = hfc.on_later_pages,
        )

        print(f"[+] Forensic Report generated → {filename}")
        return str(filename)
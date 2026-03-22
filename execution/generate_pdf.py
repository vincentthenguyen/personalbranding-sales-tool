#!/usr/bin/env python3
"""
PDF Generator
Reads a combined _output.md file and produces two styled PDFs:
  - {slug}_report.pdf  — Blue-themed client-facing Competitive Media Analysis
  - {slug}_script.pdf  — Gold-themed internal NEPQ Phone Sales Playbook

Usage (standalone):
    python execution/generate_pdf.py --output .tmp/dm_injury_law_output.md

Module API (called by sales_prep.py):
    from generate_pdf import generate_pdfs
    report_pdf, script_pdf = generate_pdfs(output_path)
"""

import re
import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as pdfgen_canvas


# ---------------------------------------------------------------------------
# Color Palettes
# ---------------------------------------------------------------------------

BLUE_THEME = {
    "accent":        colors.HexColor("#1F5BA8"),
    "dark":          colors.HexColor("#1F3B6B"),
    "light_bg":      colors.HexColor("#E8F1F8"),
    "rule":          colors.HexColor("#1F5BA8"),
    "table_header":  colors.HexColor("#1F3B6B"),
    "table_row_alt": colors.HexColor("#F0F6FB"),
    "text":          colors.HexColor("#1A1A2E"),
    "label":         colors.HexColor("#1F5BA8"),
    "company":       "PersonalBranding.com",
}

GOLD_THEME = {
    "accent":        colors.HexColor("#C7955C"),
    "dark":          colors.HexColor("#8B5E30"),
    "light_bg":      colors.HexColor("#FBF9F5"),
    "rule":          colors.HexColor("#C7955C"),
    "table_header":  colors.HexColor("#8B5E30"),
    "table_row_alt": colors.HexColor("#FBF9F5"),
    "text":          colors.HexColor("#2C1A0E"),
    "label":         colors.HexColor("#C7955C"),
    "company":       "PersonalBranding.com",
}


# ---------------------------------------------------------------------------
# Custom Flowables
# ---------------------------------------------------------------------------

class ColorBox(Flowable):
    """A colored background box containing paragraphs (callout boxes)."""

    def __init__(self, paragraphs, bg_color, border_color, width, padding=10):
        super().__init__()
        self.paragraphs = paragraphs
        self.bg_color = bg_color
        self.border_color = border_color
        self._width = width
        self.padding = padding
        self._height = None

    def wrap(self, availWidth, availHeight):
        w = min(self._width, availWidth)
        inner_w = w - 2 * self.padding
        total_h = self.padding
        for p in self.paragraphs:
            _, ph = p.wrap(inner_w, availHeight)
            total_h += ph + 4
        total_h += self.padding
        self._height = total_h
        self._wrap_width = w
        return w, total_h

    def draw(self):
        c = self.canv
        w = self._wrap_width
        h = self._height
        # Draw background rectangle
        c.setFillColor(self.bg_color)
        c.setStrokeColor(self.border_color)
        c.setLineWidth(1)
        c.roundRect(0, 0, w, h, 4, fill=1, stroke=1)
        # Draw paragraphs top-down
        y = h - self.padding
        inner_w = w - 2 * self.padding
        for p in self.paragraphs:
            pw, ph = p.wrap(inner_w, h)
            y -= ph
            p.drawOn(c, self.padding, y)
            y -= 4
        # Accent left bar
        c.setFillColor(self.border_color)
        c.rect(0, 0, 3, h, fill=1, stroke=0)


class DialogueBox(Flowable):
    """A styled quote box for SAY THIS / WHY THIS WORKS blocks."""

    def __init__(self, label, paragraphs, theme, width, padding=12):
        super().__init__()
        self.label = label
        self.paragraphs = paragraphs
        self.theme = theme
        self._width = width
        self.padding = padding
        self._height = None

        # Determine colors from label
        label_upper = label.upper()
        if "SAY THIS" in label_upper:
            self.bg_color = theme["light_bg"]
            self.accent = theme["accent"]
        elif "WHY THIS WORKS" in label_upper:
            self.bg_color = colors.HexColor("#F5F5F5")
            self.accent = colors.HexColor("#888888")
        elif "KEY INSIGHT" in label_upper or "KEY REMINDER" in label_upper:
            self.bg_color = colors.HexColor("#F5F5F5")
            self.accent = theme["dark"]
        elif "COACHING NOTE" in label_upper:
            self.bg_color = colors.HexColor("#FFFDE8")
            self.accent = colors.HexColor("#B8860B")
        elif "MATT RYDER" in label_upper:
            self.bg_color = colors.HexColor("#F0F0F0")
            self.accent = colors.HexColor("#555555")
        else:
            self.bg_color = theme["light_bg"]
            self.accent = theme["accent"]

    def wrap(self, availWidth, availHeight):
        w = min(self._width, availWidth)
        inner_w = w - 2 * self.padding - 4  # 4 for left bar
        total_h = self.padding
        for p in self.paragraphs:
            _, ph = p.wrap(inner_w, availHeight)
            total_h += ph + 4
        total_h += self.padding
        self._height = total_h
        self._wrap_width = w
        return w, total_h

    def draw(self):
        c = self.canv
        w = self._wrap_width
        h = self._height
        # Background
        c.setFillColor(self.bg_color)
        c.setStrokeColor(self.accent)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, w, h, 3, fill=1, stroke=1)
        # Left accent bar
        c.setFillColor(self.accent)
        c.rect(0, 0, 4, h, fill=1, stroke=0)
        # Paragraphs
        y = h - self.padding
        inner_w = w - 2 * self.padding - 4
        for p in self.paragraphs:
            pw, ph = p.wrap(inner_w, h)
            y -= ph
            p.drawOn(c, self.padding + 4, y)
            y -= 4


# ---------------------------------------------------------------------------
# Style Factory
# ---------------------------------------------------------------------------

def build_styles(theme):
    """Return a dict of ParagraphStyle objects for the given theme."""
    base = getSampleStyleSheet()
    acc = theme["accent"]
    dark = theme["dark"]
    txt = theme["text"]

    styles = {}

    # Title block (cover-style header, large centered)
    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Times-Bold",
        fontSize=20,
        textColor=dark,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=11,
        textColor=acc,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    styles["cover_date"] = ParagraphStyle(
        "cover_date",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=0,
    )

    # Section headers
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Times-Bold",
        fontSize=14,
        textColor=dark,
        leading=18,
        spaceBefore=14,
        spaceAfter=6,
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontName="Times-Bold",
        fontSize=12,
        textColor=dark,
        leading=16,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles["h4"] = ParagraphStyle(
        "h4",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=acc,
        leading=14,
        spaceBefore=8,
        spaceAfter=3,
    )

    # Body text
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=txt,
        leading=14,
        spaceBefore=3,
        spaceAfter=3,
        alignment=TA_JUSTIFY,
    )
    styles["body_left"] = ParagraphStyle(
        "body_left",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=txt,
        leading=14,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_LEFT,
    )

    # Callout box content
    styles["callout"] = ParagraphStyle(
        "callout",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=dark,
        leading=14,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["callout_label"] = ParagraphStyle(
        "callout_label",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=acc,
        leading=12,
        spaceBefore=0,
        spaceAfter=2,
        alignment=TA_LEFT,
    )

    # Dialogue / quote text
    styles["dialogue"] = ParagraphStyle(
        "dialogue",
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        textColor=txt,
        leading=14,
        spaceBefore=2,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles["dialogue_label"] = ParagraphStyle(
        "dialogue_label",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=acc,
        leading=11,
        spaceBefore=0,
        spaceAfter=2,
        alignment=TA_LEFT,
        letterSpacing=1,
    )

    # Bullet
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=txt,
        leading=14,
        leftIndent=14,
        bulletIndent=0,
        spaceBefore=1,
        spaceAfter=1,
        alignment=TA_LEFT,
    )

    # Table header/cell
    styles["tbl_header"] = ParagraphStyle(
        "tbl_header",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=colors.white,
        leading=12,
        alignment=TA_LEFT,
    )
    styles["tbl_cell"] = ParagraphStyle(
        "tbl_cell",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=txt,
        leading=12,
        alignment=TA_LEFT,
    )
    styles["tbl_cell_bold"] = ParagraphStyle(
        "tbl_cell_bold",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=txt,
        leading=12,
        alignment=TA_LEFT,
    )

    # Phase label (e.g., QUESTION 1, PHASE 2)
    styles["phase_label"] = ParagraphStyle(
        "phase_label",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=acc,
        leading=11,
        spaceBefore=8,
        spaceAfter=2,
        alignment=TA_LEFT,
        letterSpacing=1,
    )

    # Internal use banner
    styles["banner"] = ParagraphStyle(
        "banner",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.white,
        leading=13,
        alignment=TA_CENTER,
    )

    return styles


# ---------------------------------------------------------------------------
# Header / Footer Canvas
# ---------------------------------------------------------------------------

class ThemeCanvas:
    """Mixin that draws a header/footer on each page."""

    def __init__(self, theme, firm_name, doc_type):
        self.theme = theme
        self.firm_name = firm_name
        self.doc_type = doc_type  # "report" or "script"

    def __call__(self, canv, doc):
        canv.saveState()
        w, h = letter
        margin = inch

        # ---- Header ----
        canv.setFont("Helvetica-Bold", 8)
        canv.setFillColor(self.theme["accent"])
        canv.drawString(margin, h - 0.55 * inch, self.theme["company"])

        canv.setFont("Helvetica", 8)
        canv.setFillColor(colors.HexColor("#888888"))
        canv.drawRightString(w - margin, h - 0.55 * inch, self.firm_name)

        # Header rule
        canv.setStrokeColor(self.theme["rule"])
        canv.setLineWidth(0.75)
        canv.line(margin, h - 0.65 * inch, w - margin, h - 0.65 * inch)

        # ---- Footer ----
        canv.setStrokeColor(colors.HexColor("#CCCCCC"))
        canv.setLineWidth(0.5)
        canv.line(margin, 0.55 * inch, w - margin, 0.55 * inch)

        canv.setFont("Helvetica", 7.5)
        canv.setFillColor(colors.HexColor("#888888"))
        canv.drawString(margin, 0.38 * inch, self.theme["company"])

        canv.drawCentredString(
            w / 2, 0.38 * inch,
            "INTERNAL USE ONLY — DO NOT SHARE" if self.doc_type == "script" else ""
        )

        canv.drawRightString(
            w - margin, 0.38 * inch,
            f"Page {doc.page}"
        )

        canv.restoreState()


# ---------------------------------------------------------------------------
# Markdown → Flowables Parser
# ---------------------------------------------------------------------------

def clean_inline(text):
    """Convert markdown inline bold/italic to ReportLab HTML-ish tags."""
    # Bold-italic ***text***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    # Escape ampersands (reportlab XML issue)
    text = text.replace("&", "&amp;")
    # Restore already-escaped entities
    text = text.replace("&amp;amp;", "&amp;")
    return text


def parse_markdown_table(lines):
    """Parse a markdown table block into list of list of strings."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line or re.match(r'^\|[-| :]+\|$', line):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)
    return rows


def build_table_flowable(md_lines, styles, theme, page_width):
    """Convert markdown table lines into a ReportLab Table flowable."""
    rows_data = parse_markdown_table(md_lines)
    if not rows_data:
        return None

    num_cols = max(len(r) for r in rows_data)
    # Pad short rows
    rows_data = [r + [''] * (num_cols - len(r)) for r in rows_data]

    # Convert cells to Paragraphs
    tbl_rows = []
    for i, row in enumerate(rows_data):
        style_key = "tbl_header" if i == 0 else "tbl_cell"
        new_row = []
        for cell in row:
            # Strip bold markers, apply bold style to first-col data rows
            is_bold = cell.startswith("**") and cell.endswith("**")
            cell_text = cell.strip("*").strip()
            cell_text = clean_inline(cell_text)
            if i == 0:
                new_row.append(Paragraph(cell_text, styles["tbl_header"]))
            elif is_bold:
                new_row.append(Paragraph(cell_text, styles["tbl_cell_bold"]))
            else:
                new_row.append(Paragraph(cell_text, styles["tbl_cell"]))
        tbl_rows.append(new_row)

    # Column widths: distribute evenly but constrain
    avail = page_width
    col_w = avail / num_cols

    tbl = Table(tbl_rows, colWidths=[col_w] * num_cols, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), theme["table_header"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, theme["table_row_alt"]]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def md_to_flowables(md_text, styles, theme, page_width):
    """
    Parse a markdown string and return a list of ReportLab Flowable objects.
    Handles: headers, tables, ``` code/callout blocks, > blockquotes,
             bullet lists, bold/italic inline, horizontal rules.
    """
    flowables = []
    lines = md_text.splitlines()
    i = 0
    inner_w = page_width  # usable width inside margins

    # State for accumulating multi-line blocks
    in_table = False
    table_lines = []
    in_fence = False
    fence_lines = []
    in_dialogue_label = None  # label string for current dialogue block
    pending_dialogue_paras = []
    pending_label = None

    def flush_table():
        nonlocal table_lines, in_table
        if table_lines:
            tbl = build_table_flowable(table_lines, styles, theme, inner_w)
            if tbl:
                flowables.append(Spacer(1, 6))
                flowables.append(tbl)
                flowables.append(Spacer(1, 6))
        table_lines = []
        in_table = False

    def flush_fence(fence_lines):
        """Render a ``` fenced block as a callout ColorBox."""
        if not fence_lines:
            return
        content_text = "\n".join(fence_lines).strip()
        if not content_text:
            return

        paras = []
        for fline in content_text.splitlines():
            fline = fline.strip()
            if not fline:
                paras.append(Spacer(1, 4))
                continue
            fline = clean_inline(fline)
            paras.append(Paragraph(fline, styles["callout"]))

        box = ColorBox(
            paras,
            bg_color=theme["light_bg"],
            border_color=theme["accent"],
            width=inner_w,
            padding=10,
        )
        flowables.append(Spacer(1, 6))
        flowables.append(box)
        flowables.append(Spacer(1, 6))

    # Regex patterns
    HEADER_RE = re.compile(r'^(#{1,4})\s+(.+)')
    TABLE_ROW_RE = re.compile(r'^\|')
    FENCE_RE = re.compile(r'^```')
    HR_RE = re.compile(r'^---+\s*$')
    BULLET_RE = re.compile(r'^[-*+]\s+(.+)')
    NUMBERED_RE = re.compile(r'^\d+\.\s+(.+)')
    BLOCKQUOTE_RE = re.compile(r'^>\s*(.*)')

    # These uppercase labels appear as standalone lines before SAY THIS etc.
    LABEL_RE = re.compile(
        r'^(SAY THIS|WHY THIS WORKS|KEY INSIGHT|KEY REMINDER|COACHING NOTE|'
        r'MATT RYDER.*|IF THEY.*|THE BRIDGE.*|THE NATURAL CLOSE.*|'
        r'THE 60-SECOND.*|QUESTION \d+|PHASE \d+.*)'
    )

    # Accumulate blockquote lines for dialogue boxes
    quote_buffer = []
    current_label = None

    def flush_quotes():
        nonlocal quote_buffer, current_label, pending_label
        if not quote_buffer:
            return
        paras = []
        lbl = current_label or ""
        # Label paragraph
        if lbl:
            paras.append(Paragraph(lbl, styles["dialogue_label"]))
        for qt in quote_buffer:
            qt = clean_inline(qt)
            paras.append(Paragraph(qt, styles["dialogue"]))

        box = DialogueBox(
            label=lbl,
            paragraphs=paras,
            theme=theme,
            width=inner_w,
            padding=10,
        )
        flowables.append(Spacer(1, 4))
        flowables.append(box)
        flowables.append(Spacer(1, 4))
        quote_buffer.clear()
        current_label = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Fenced block ──────────────────────────────────────────
        if FENCE_RE.match(stripped):
            if not in_fence:
                flush_quotes()
                if in_table:
                    flush_table()
                in_fence = True
                fence_lines = []
            else:
                in_fence = False
                flush_fence(fence_lines)
                fence_lines = []
            i += 1
            continue

        if in_fence:
            fence_lines.append(line)
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────────────
        if HR_RE.match(stripped):
            flush_quotes()
            if in_table:
                flush_table()
            flowables.append(Spacer(1, 4))
            flowables.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#CCCCCC"), spaceAfter=4
            ))
            i += 1
            continue

        # ── Table row ─────────────────────────────────────────────
        if TABLE_ROW_RE.match(stripped):
            flush_quotes()
            in_table = True
            table_lines.append(stripped)
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        # ── Blank line ────────────────────────────────────────────
        if not stripped:
            flush_quotes()
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # ── Headers ───────────────────────────────────────────────
        m = HEADER_RE.match(stripped)
        if m:
            flush_quotes()
            level = len(m.group(1))
            text = clean_inline(m.group(2))
            if level == 1:
                style = styles["h2"]
            elif level == 2:
                style = styles["h2"]
            elif level == 3:
                style = styles["h3"]
            else:
                style = styles["h4"]
            flowables.append(Spacer(1, 4))
            flowables.append(Paragraph(text, style))
            i += 1
            continue

        # ── Blockquote (SAY THIS dialogue) ────────────────────────
        bq_m = BLOCKQUOTE_RE.match(line)
        if bq_m:
            content = bq_m.group(1).strip()
            # Strip italic markers from the quote text
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            quote_buffer.append(content)
            i += 1
            continue
        else:
            # Not a blockquote line — flush any pending quotes
            if quote_buffer:
                flush_quotes()

        # ── Standalone LABEL lines (SAY THIS, WHY THIS WORKS, etc.) ──
        lbl_m = LABEL_RE.match(stripped)
        if lbl_m:
            current_label = stripped
            i += 1
            continue

        # ── Bullet list ───────────────────────────────────────────
        bul_m = BULLET_RE.match(stripped)
        if bul_m:
            text = clean_inline(bul_m.group(1))
            flowables.append(Paragraph(f"• {text}", styles["bullet"]))
            i += 1
            continue

        num_m = NUMBERED_RE.match(stripped)
        if num_m:
            text = clean_inline(num_m.group(1))
            # Extract number
            num = stripped.split('.')[0]
            flowables.append(Paragraph(f"{num}. {text}", styles["bullet"]))
            i += 1
            continue

        # ── Regular paragraph ─────────────────────────────────────
        text = clean_inline(stripped)
        flowables.append(Paragraph(text, styles["body"]))
        i += 1

    # Flush any remaining buffered content
    flush_quotes()
    if in_table:
        flush_table()
    if in_fence and fence_lines:
        flush_fence(fence_lines)

    return flowables


# ---------------------------------------------------------------------------
# Cover Page Builder
# ---------------------------------------------------------------------------

def build_cover_page(title_line1, title_line2, subtitle_lines, styles, theme):
    """Return flowables for a styled cover block at the top of the first page."""
    elems = []
    elems.append(Spacer(1, 0.2 * inch))

    # Accent top bar (simulate with colored Table)
    accent_row = Table(
        [[""]],
        colWidths=["100%"],
        rowHeights=[6],
    )
    accent_row.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), theme["accent"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elems.append(accent_row)
    elems.append(Spacer(1, 12))

    if title_line1:
        elems.append(Paragraph(title_line1, styles["cover_title"]))
    if title_line2:
        elems.append(Paragraph(title_line2, styles["cover_title"]))

    elems.append(Spacer(1, 8))
    for sub in subtitle_lines:
        elems.append(Paragraph(sub, styles["cover_sub"]))

    elems.append(Spacer(1, 12))

    # Bottom accent bar
    accent_row2 = Table(
        [[""]],
        colWidths=["100%"],
        rowHeights=[6],
    )
    accent_row2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), theme["accent"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elems.append(accent_row2)
    elems.append(Spacer(1, 16))

    return elems


# ---------------------------------------------------------------------------
# Main Render Function
# ---------------------------------------------------------------------------

def render_pdf(md_text, out_path, theme, firm_name, doc_type,
               cover_title1, cover_title2, cover_subs):
    """Render a single PDF from markdown text."""
    out_path = Path(out_path)
    PAGE_W, PAGE_H = letter
    MARGIN = inch
    page_width = PAGE_W - 2 * MARGIN

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=0.9 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = build_styles(theme)
    canvas_cb = ThemeCanvas(theme, firm_name, doc_type)

    flowables = []

    # Cover block
    flowables.extend(
        build_cover_page(cover_title1, cover_title2, cover_subs, styles, theme)
    )

    # Document body
    body_flowables = md_to_flowables(md_text, styles, theme, page_width)
    flowables.extend(body_flowables)

    doc.build(flowables, onFirstPage=canvas_cb, onLaterPages=canvas_cb)
    return out_path


# ---------------------------------------------------------------------------
# Split Output File & Generate Both PDFs
# ---------------------------------------------------------------------------

def split_output(output_path):
    """
    Split the combined _output.md into (report_md, script_md, firm_name).
    The file has:
        PART 1: MEDIA VISIBILITY REPORT ... (CLIENT-FACING)
        PART 2: INTERNAL SALES SCRIPT   ... (INTERNAL)
    """
    text = Path(output_path).read_text(encoding="utf-8")

    # Extract firm name from the title line "# Sales Prep: {Firm Name}"
    title_m = re.search(r'^#\s+Sales Prep:\s+(.+)', text, re.MULTILINE)
    firm_name = title_m.group(1).strip() if title_m else "Law Firm"

    # Split on PART 2 marker
    part2_m = re.search(
        r'^PART 2:\s*INTERNAL SALES SCRIPT',
        text, re.MULTILINE | re.IGNORECASE
    )
    if part2_m:
        report_md = text[:part2_m.start()].strip()
        script_md = text[part2_m.start():].strip()
    else:
        report_md = text
        script_md = ""

    # Strip the top-level header line from both
    report_md = re.sub(r'^#\s+Sales Prep:.*\n', '', report_md, flags=re.MULTILINE)
    report_md = re.sub(r'^Generated:.*\n', '', report_md, flags=re.MULTILINE)

    # Strip the PART 1 header line
    report_md = re.sub(
        r'^PART 1:.*\n', '', report_md, flags=re.MULTILINE | re.IGNORECASE
    )
    report_md = re.sub(
        r'^CLIENT-FACING REPORT.*\n', '', report_md,
        flags=re.MULTILINE | re.IGNORECASE
    )

    # Strip PART 2 header lines from script
    script_md = re.sub(
        r'^PART 2:.*\n', '', script_md, flags=re.MULTILINE | re.IGNORECASE
    )
    script_md = re.sub(
        r'^INTERNAL SALES SCRIPT.*\n', '', script_md,
        flags=re.MULTILINE | re.IGNORECASE
    )

    return report_md.strip(), script_md.strip(), firm_name


def extract_date(output_path):
    """Extract the 'Generated: ...' date from the output file."""
    text = Path(output_path).read_text(encoding="utf-8")
    m = re.search(r'^Generated:\s*(.+)', text, re.MULTILINE)
    return m.group(1).strip() if m else "2026"


def generate_pdfs(output_path):
    """
    Main entry point. Reads {slug}_output.md and produces two PDFs.
    Returns (report_pdf_path, script_pdf_path).
    """
    output_path = Path(output_path)
    slug = output_path.stem.replace("_output", "")
    parent = output_path.parent

    report_pdf = parent / f"{slug}_report.pdf"
    script_pdf = parent / f"{slug}_script.pdf"

    report_md, script_md, firm_name = split_output(output_path)
    date_str = extract_date(output_path)

    # ---- Report PDF (blue) ----
    print(f"\n[PDF] Generating report PDF → {report_pdf.name}")
    render_pdf(
        md_text=report_md,
        out_path=report_pdf,
        theme=BLUE_THEME,
        firm_name=firm_name,
        doc_type="report",
        cover_title1="COMPETITIVE MEDIA ANALYSIS",
        cover_title2=firm_name,
        cover_subs=[
            f"vs. Top Competitors · Prepared by PersonalBranding.com · {date_str}"
        ],
    )
    print(f"  ✓ Report PDF: {report_pdf}")

    # ---- Script PDF (gold) ----
    if script_md:
        print(f"[PDF] Generating script PDF → {script_pdf.name}")
        render_pdf(
            md_text=script_md,
            out_path=script_pdf,
            theme=GOLD_THEME,
            firm_name=firm_name,
            doc_type="script",
            cover_title1="PHONE SALES PLAYBOOK",
            cover_title2=f"Closing {firm_name}",
            cover_subs=[
                "NEPQ Framework · Neuro-Emotional Persuasion Questioning",
                "PersonalBranding.com · Internal Use Only",
                date_str,
            ],
        )
        print(f"  ✓ Script PDF: {script_pdf}")
    else:
        script_pdf = None
        print("  [PDF] No Part 2 content found — skipping script PDF.")

    return report_pdf, script_pdf


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate styled PDFs from a sales prep output.md file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the _output.md file"
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"ERROR: File not found: {output_path}")
        sys.exit(1)

    report_pdf, script_pdf = generate_pdfs(output_path)

    print(f"\n{'='*60}")
    print("PDFs generated:")
    print(f"  Report (send to prospect): {report_pdf}")
    if script_pdf:
        print(f"  Script (internal only):    {script_pdf}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

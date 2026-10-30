"""UMY appendix-style proposal layout; product wording stays in Markdown."""

import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)

PAGE_W, PAGE_H = A4
MARGIN = 54
NAVY = colors.HexColor('#0B2039')
TEAL = colors.HexColor('#007F86')
MUTED = colors.HexColor('#52677D')
RULE = colors.HexColor('#CBD8E2')


def page_chrome(canvas, doc, label, heading=None):
    """Shared appendix masthead and document-local page numbering."""
    canvas.saveState()
    canvas.setFont('Plex', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, PAGE_H - 32, 'UMY HACKATHON DEEPTECH 2026')
    canvas.setFillColor(TEAL)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 32, 'LAMPIRAN · FORMAT PROPOSAL')
    if heading:
        canvas.setFillColor(TEAL)
        canvas.rect(MARGIN, PAGE_H - 66, 8, 8, fill=1, stroke=0)
        canvas.setFont('Plex-Bold', 18)
        canvas.setFillColor(NAVY)
        canvas.drawString(MARGIN + 18, PAGE_H - 67, heading)
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(1)
        canvas.line(MARGIN, PAGE_H - 79, PAGE_W - MARGIN, PAGE_H - 79)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(.6)
    canvas.line(MARGIN, 40, PAGE_W - MARGIN, 40)
    canvas.setFillColor(MUTED)
    canvas.setFont('Plex', 7.4)
    canvas.drawString(MARGIN, 26, label)
    canvas.setFillColor(NAVY)
    canvas.setFont('Plex-Bold', 8)
    canvas.drawRightString(PAGE_W - MARGIN, 26, str(doc.page))
    canvas.restoreState()


class SectionHeading(Flowable):
    """Teal number in the margin, sans-serif section label, and fine rule."""

    def __init__(self, number, title, note=None):
        super().__init__()
        self.number, self.title, self.note = number, title, note
        self.keepWithNext = True
        self.spaceBefore = 10
        self.spaceAfter = 6

    def wrap(self, width, height):
        self.width = width
        self.caption = Paragraph(self.title, ParagraphStyle(
            'section-label', fontName='Plex-SemiBold', fontSize=12,
            leading=14.3, textColor=NAVY,
        ))
        _, caption_height = self.caption.wrap(width - 30, height)
        self.height = max(17, caption_height) + 5 + (11 if self.note else 0)
        self.caption_height = caption_height
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(RULE)
        c.setLineWidth(.45)
        c.line(0, self.height, self.width, self.height)
        c.setFillColor(TEAL)
        c.setFont('Plex-SemiBold', 17)
        c.drawString(0, self.height - 19, self.number)
        self.caption.drawOn(c, 30, self.height - 5 - self.caption_height)
        if self.note:
            c.setFont('Plex-SemiBold', 8)
            c.setFillColor(TEAL)
            c.drawString(30, 1, self.note)
        c.restoreState()


class BoxedTitle(Flowable):
    def __init__(self, paragraph):
        super().__init__()
        self.paragraph = paragraph
        self.spaceAfter = 4

    def wrap(self, width, height):
        self.width = width
        _, h = self.paragraph.wrap(width - 16, height)
        self.height = h + 16
        return width, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(colors.HexColor('#95AFC3'))
        self.canv.setDash(2, 2)
        self.canv.setLineWidth(.6)
        self.canv.rect(0, 0, self.width, self.height, fill=0)
        self.canv.restoreState()
        self.paragraph.drawOn(self.canv, 8, 8)


class Checkbox(Flowable):
    def __init__(self, selected=False):
        super().__init__()
        self.selected = selected
        self.width, self.height = 11, 13.8

    def draw(self):
        c = self.canv
        c.saveState()
        c.setLineWidth(.6)
        c.setStrokeColor(NAVY)
        c.rect(0, 2, 8.5, 8.5)
        if self.selected:
            c.setStrokeColor(TEAL)
            c.setLineWidth(1.4)
            path = c.beginPath()
            path.moveTo(1.8, 6)
            path.lineTo(3.7, 3.8)
            path.lineTo(7.3, 9)
            c.drawPath(path)
        c.restoreState()


def theme_block(markdown, width, helpers, sty):
    """Use the source field values, preserving the chosen cluster and team text."""
    match = re.fullmatch(
        r'\s*\*\*Bidang strategis:\*\* (.*?) \*\*Klaster:\*\* (.*?) '
        r'\*\*Tim:\*\* (.*?)\s*', markdown, re.S,
    )
    if not match:
        raise ValueError('Tema Fokus Inovasi must retain its three named Markdown fields')
    field, cluster, team = match.groups()
    if not field.startswith('Kesehatan - ') or 'Sustainable and Green Healthcare' not in cluster:
        raise ValueError('Template checkboxes must be mapped to the actual selected field/cluster')
    p = lambda text: Paragraph(helpers.escaped_text(text), sty['p'])
    label_style = ParagraphStyle('theme-label', parent=sty['p'],
                                 fontName='Plex-SemiBold', fontSize=9.5, leading=12)
    label = lambda text: Paragraph(text, label_style)
    rows = [
        [label('Bidang strategis:'), Checkbox(True), p(field)],
    ]
    field_table = Table(rows, colWidths=[88, 14, width - 102], hAlign='LEFT')
    field_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    names = [
        'Smart Diagnostic and Screening', 'Digital Health and Artificial Intelligence',
        'Connected Health and IoMT', 'Medical Device and Rehabilitation Technology',
        'Smart Hospital and Healthcare Efficiency', 'Preventive and Community Health',
        'Biotechnology and Advanced Materials', cluster,
    ]
    cells = []
    # The unselected choices are form labels; the selected value keeps the source wording.
    option_style = ParagraphStyle('cluster-option', fontName='Plex', fontSize=9.5,
                                  leading=12, textColor=NAVY)
    for i in range(0, 8, 2):
        row = []
        for j in [i, i + 1]:
            row.extend([Checkbox(j == 7), Paragraph(helpers.escaped_text(names[j]), option_style)])
        cells.append(row)
    choices = Table(cells, colWidths=[14, (width - 28) / 2, 14, (width - 28) / 2],
                    hAlign='LEFT')
    choices.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return [field_table, label('Klaster: (pilih satu)'), Spacer(1, 2), choices,
            Paragraph('<b>Tim:</b> ' + helpers.escaped_text(team), sty['p'])]


def proposal_sections(text):
    """Keep each original body verbatim; page comments are layout instructions only."""
    matches = list(re.finditer(r'^#{1,2} ([1-7])\. (.+)$', text, re.M))
    if [m.group(1) for m in matches] != ['1', '2', '3', '4', '4', '5', '6', '7']:
        raise ValueError('Unexpected proposal structure; refusing to omit an unmapped section')
    return [
        (m.group(1), m.group(2),
         text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
         .replace('<!-- page -->', '').strip())
        for i, m in enumerate(matches)
    ]


def build_proposal(output, source, helpers):
    """Render the filled form, retaining the complete source and screenshot figure."""
    doc = BaseDocTemplate(
        str(output), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=51, bottomMargin=49, title='HematDaya - Proposal UMY 2026',
        author='Tim Petani Digital',
    )
    sty = helpers.styles('Times', 12, 13.8, False)
    sty['p'].spaceAfter = 6
    sty['table_padding'] = 5
    sty['table_space_after'] = 8
    sty['cell'].leading = 13.8
    heading = ParagraphStyle('proposal-title', fontName='Plex-Bold', fontSize=16,
                             leading=19, textColor=NAVY, spaceAfter=8)
    main_heading = Paragraph('Substansi Proposal Peserta Hackathon DeepTech', heading)
    story = [main_heading]
    for number, title, body in proposal_sections(source.read_text()):
        note = {'3': 'MAKS. 250 KATA', '4': 'MAKSIMUM 2 HALAMAN',
                '5': 'MAKSIMUM 1 HALAMAN', '7': 'DIUNGGAH/DIISI DALAM SISTEM'}.get(number)
        story.append(SectionHeading(number, title, note))
        if number == '1':
            tokens = helpers.MD.parse(body)
            story.append(BoxedTitle(Paragraph(helpers.inline(tokens[1].children), sty['p'])))
        elif number == '2':
            story.append(KeepTogether(theme_block(body, doc.width, helpers, sty)))
        else:
            story.extend(helpers.render_markdown(body, sty, doc.width, base=source.parent))
    def paint(canvas, document):
        page_chrome(canvas, document, 'Lampiran · Substansi Proposal | Tim Petani Digital')
    doc.addPageTemplates(PageTemplate(
        id='proposal', onPage=paint,
        frames=Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ))
    doc.build(story)

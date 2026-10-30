"""Fill the revised UMY integrity-pact form with supplied team signature images."""

import html
import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle

from umy_template import MARGIN, MUTED, NAVY, PAGE_H, PAGE_W, RULE, TEAL


def _style(name, size=11.2, leading=16, font='Plex', **kwargs):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=kwargs.pop('textColor', NAVY), **kwargs)


def _paragraph(c, text, x, top, width, style):
    p = Paragraph(text, style)
    _, h = p.wrap(width, PAGE_H)
    p.drawOn(c, x, top - h)
    return top - h


def _tables(text, helpers):
    tables, rows, row = [], None, None
    for token in helpers.MD.parse(text):
        if token.type == 'table_open':
            rows = []
        elif token.type == 'tr_open':
            row = []
        elif token.type == 'inline' and row is not None:
            row.append(token.content)
        elif token.type == 'tr_close':
            rows.append(row)
            row = None
        elif token.type == 'table_close':
            tables.append(rows)
            rows = None
    if len(tables) != 2:
        raise ValueError('The pact source must contain a team-data and signature table.')
    return tables


def _read_source(source, helpers):
    text = source.read_text(encoding='utf-8')
    front = text.split('## Data Tim', 1)[0].strip().split('\n\n')
    if len(front) != 4:
        raise ValueError('The pact must retain its title, programme, university, and theme.')
    tables = _tables(text, helpers)
    preamble = text.split('## Pernyataan\n', 1)[1].split('### 1.', 1)[0].strip()
    matches = list(re.finditer(r'^### ([1-7])\. (.+)$', text, re.M))
    if [m.group(1) for m in matches] != list('1234567'):
        raise ValueError('The revised pact must contain all seven numbered commitments.')
    clauses = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else text.index('## Sanksi')
        clauses.append((match.group(1), match.group(2), text[match.end():end].strip()))
    sanctions = text.split('## Sanksi\n', 1)[1].split('## Penutup', 1)[0].strip().splitlines()
    closing = text.split('## Penutup\n', 1)[1].split('## Tanggal', 1)[0].strip().split('\n\n')
    date = text.split('## Tanggal\n', 1)[1].split('## Tanda Tangan', 1)[0].strip()
    if len(sanctions) != 4 or len(closing) != 2 or len(tables[1][1:]) != 4:
        raise ValueError('Expected four sanctions, two closing paragraphs, and four signatories.')
    return front, tables[0], preamble, clauses, sanctions, closing, date, tables[1]


def _footer(c, page):
    c.setStrokeColor(RULE)
    c.setLineWidth(.5)
    c.line(MARGIN, 40, PAGE_W - MARGIN, 40)
    c.setFillColor(MUTED)
    c.setFont('Plex', 7.4)
    c.drawString(MARGIN, 26, 'Lampiran · Pakta Integritas | Revisi')
    c.setFont('Plex-Bold', 8)
    c.setFillColor(NAVY)
    c.drawRightString(PAGE_W - MARGIN, 26, str(page))


def _banner(c, front):
    height = 177
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - height, PAGE_W, height, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#18334C'))
    for x in range(8, int(PAGE_W), 12):
        for y in range(int(PAGE_H - height) + 8, int(PAGE_H), 12):
            c.circle(x, y, .65, fill=1, stroke=0)
    c.setFont('Plex', 8)
    c.setFillColor(colors.HexColor('#B7CBDC'))
    c.drawString(MARGIN, PAGE_H - 32, 'UMY HACKATHON DEEPTECH 2026')
    c.setFillColor(colors.HexColor('#42DBCF'))
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 32, 'LAMPIRAN')
    c.setFillColor(colors.white)
    c.setFont('Plex-Bold', 29)
    c.drawString(MARGIN, PAGE_H - 85, front[0].lstrip('# '))
    y = PAGE_H - 110
    for line in front[1:3]:
        y = _paragraph(c, html.escape(line), MARGIN, y, PAGE_W - 2 * MARGIN,
                       _style('banner-label', 10.5, 15, 'Plex-SemiBold', textColor=colors.HexColor('#DEE8F2'))) - 3
    _paragraph(c, html.escape(front[3].strip('*')), MARGIN, y - 1, PAGE_W - 2 * MARGIN,
               _style('banner-theme', 10.2, 14, 'Plex-Italic', textColor=colors.HexColor('#42DBCF')))
    c.setFillColor(colors.HexColor('#42DBCF'))
    c.rect(0, PAGE_H - height - 2, PAGE_W, 2, fill=1, stroke=0)
    return PAGE_H - height - 20


def _data_table(c, rows, y, width):
    head = _style('data-head', 10.3, 14, 'Plex-SemiBold', textColor=colors.white)
    label = _style('data-label', 10, 14, 'Plex-SemiBold')
    value = _style('data-value', 10.2, 14)
    data = [[Paragraph(html.escape(cell), head) for cell in rows[0]]]
    data += [[Paragraph(html.escape(row[0]), label), Paragraph(html.escape(row[1]), value)] for row in rows[1:]]
    table = Table(data, colWidths=[151, width - 151])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F0F5F8')),
        ('GRID', (0, 0), (-1, -1), .45, RULE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    _, height = table.wrap(width, PAGE_H)
    table.drawOn(c, MARGIN, y - height)
    return y - height


def _clause(c, item, y, body):
    number, heading, text = item
    c.setFillColor(colors.HexColor('#E5F3F2'))
    c.rect(MARGIN, y - 21, 21, 21, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.setFont('Plex-SemiBold', 11)
    c.drawCentredString(MARGIN + 10.5, y - 14.5, number)
    return _paragraph(c, '<b>' + html.escape(heading) + ':</b> ' + html.escape(text),
                      MARGIN + 32, y, PAGE_W - 2 * MARGIN - 32, body) - 10


def _sanctions(c, sanctions, y, width):
    gap, inset = 6, 10
    card_width = (width - gap) / 2
    sty = _style('sanction-text', 10.5, 14.5)
    for pair in [sanctions[:2], sanctions[2:]]:
        paragraphs = [Paragraph('<font color="#007F86"><b>' + html.escape(s[:2])
                                + '</b></font> ' + html.escape(s[3:]), sty) for s in pair]
        heights = [p.wrap(card_width - 2 * inset, PAGE_H)[1] for p in paragraphs]
        h = max(heights) + 2 * inset
        for i, paragraph in enumerate(paragraphs):
            x = MARGIN + 32 + i * (card_width + gap)
            c.setFillColor(colors.HexColor('#F0F5F8'))
            c.rect(x, y - h, card_width, h, fill=1, stroke=0)
            paragraph.drawOn(c, x + inset, y - inset - heights[i])
        y -= h + gap
    return y


def _signatures(c, rows, y, source, width):
    widths = [32, 143, 88, 142, width - 405]
    head = _style('signature-head', 9.6, 12.5, 'Plex-SemiBold', textColor=colors.white)
    body = _style('signature-data', 9.5, 13)
    data = [[Paragraph(html.escape(cell), head) for cell in rows[0]]]
    for row in rows[1:]:
        path = source.parent / row[4]
        image = Image(str(path))
        scale = min((widths[4] - 12) / image.imageWidth, 35 / image.imageHeight)
        image.drawWidth = image.imageWidth * scale
        image.drawHeight = image.imageHeight * scale
        data.append([*[Paragraph(html.escape(value), body) for value in row[:4]], image])
    table = Table(data, colWidths=widths, rowHeights=[27, 45, 45, 45, 45])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY), ('GRID', (0, 0), (-1, -1), .45, RULE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    _, height = table.wrap(width, PAGE_H)
    if y - height < 49:
        raise ValueError(f'The pact signature table would overlap the footer ({y - height:.1f} pt).')
    table.drawOn(c, MARGIN, y - height)


def build_pakta(output, source, helpers):
    front, team, preamble, clauses, sanctions, closing, date, signatures = _read_source(source, helpers)
    width = PAGE_W - 2 * MARGIN
    body = _style('pact-body')
    c = canvas.Canvas(str(output), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle('HematDaya - Pakta Integritas UMY Revisi')
    c.setAuthor(dict(team[1:])['Nama Tim'])
    y = _data_table(c, team, _banner(c, front), width) - 16
    y = _paragraph(c, html.escape(preamble), MARGIN, y, width, body) - 12
    for clause in clauses[:4]:
        y = _clause(c, clause, y, body)
    if y < 49:
        raise ValueError(f'The pact first page would overlap its footer ({y:.1f} pt).')
    _footer(c, 1)
    c.showPage()
    c.setFont('Plex', 8)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, PAGE_H - 32, 'UMY HACKATHON DEEPTECH 2026')
    c.setFillColor(TEAL)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 32, 'LAMPIRAN · PAKTA INTEGRITAS')
    y = PAGE_H - 63
    for clause in clauses[4:]:
        y = _clause(c, clause, y, body)
    y = _sanctions(c, sanctions, y, width - 32) - 9
    c.setStrokeColor(RULE)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= 15
    for paragraph in closing:
        y = _paragraph(c, html.escape(paragraph), MARGIN, y, width, body) - 10
    y = _paragraph(c, html.escape(date), MARGIN, y - 2, width,
                   _style('pact-date', alignment=2)) - 14
    _signatures(c, signatures, y, source, width)
    _footer(c, 2)
    c.showPage()
    c.save()

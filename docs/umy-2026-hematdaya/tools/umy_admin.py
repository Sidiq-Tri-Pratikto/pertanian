"""Fill the two-page UMY cover and identity layout from its Markdown source."""

import html
import re
from pathlib import Path
from types import SimpleNamespace

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

from umy_template import MARGIN, MUTED, NAVY, PAGE_H, PAGE_W, RULE, TEAL, page_chrome


def _plain(value):
    return html.escape(value, quote=False)


def _style(name, font="Times", size=12, leading=13.8, **kwargs):
    options = dict(fontName=font, fontSize=size, leading=leading,
                   textColor=NAVY, alignment=TA_LEFT)
    options.update(kwargs)
    return ParagraphStyle(name, **options)


def _paragraph(c, text, x, top, width, style):
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, PAGE_H)
    paragraph.drawOn(c, x, top - height)
    return top - height


def _centered(c, text, top, width, style):
    return _paragraph(c, _plain(text), (PAGE_W - width) / 2, top, width, style)


def _source_data(source, helpers):
    text = Path(source).read_text(encoding="utf-8")
    front, remainder = text.split("## Sampul\n", 1)
    cover, identity = remainder.split("## Lembar Identitas\n", 1)
    front_blocks = [part.strip() for part in front.strip().split("\n\n")]
    cover_blocks = [part.strip() for part in cover.strip().split("\n\n")]
    if len(cover_blocks) != 10:
        raise ValueError("Sampul harus memiliki sepuluh blok isian sesuai sumber Markdown.")

    tables = []
    rows = None
    row = None
    for token in helpers.MD.parse(identity):
        if token.type == "table_open":
            rows = []
        elif token.type == "tr_open":
            row = []
        elif token.type == "inline" and row is not None:
            row.append(token.content)
        elif token.type == "tr_close":
            rows.append(row)
            row = None
        elif token.type == "table_close":
            tables.append(rows)
            rows = None
    if len(tables) != 2:
        raise ValueError("Lembar identitas memerlukan tabel ketua dan tabel anggota.")
    chairman = dict(tables[0][1:])
    members = tables[1][1:]
    title = re.search(r"^1\. Judul:\s*(.+)$", identity, re.M).group(1)
    partner = re.search(r"^3\. Lembaga mitra riset dan alamat:\s*(.+)$", identity, re.M).group(1)
    after_members = identity.split(tables[1][-1][-1] + " |", 1)[1].strip()
    signature, note = after_members.split("\n\nCatatan:", 1)
    signature_blocks = [part.strip() for part in signature.split("\n\n")]
    if len(signature_blocks) != 5:
        raise ValueError("Blok tanda tangan memerlukan kota/tanggal, jabatan, ruang, nama, dan identitas.")
    return front_blocks, cover_blocks, title, chairman, partner, members, signature_blocks, "Catatan:" + note


def _cover_page(c, doc, front, blocks):
    page_chrome(c, doc, "Lampiran · Sampul proposal", heading="Halaman Sampul Proposal")
    left = MARGIN + 16
    width = PAGE_W - 2 * left
    bottom = 145
    top = PAGE_H - 111
    c.setFillColor(colors.HexColor("#E7F1F2"))
    c.rect(left + 6, bottom - 6, width, top - bottom, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setStrokeColor(RULE)
    c.setLineWidth(.8)
    c.rect(left, bottom, width, top - bottom, fill=1, stroke=1)

    bold = _style("cover-bold", "Plex-Bold", 18, 23, alignment=TA_CENTER)
    subtitle = _style("cover-subtitle", "Plex-Bold", 12, 16, alignment=TA_CENTER)
    label = _style("cover-label", "Plex", 11, 15, alignment=TA_CENTER)
    title = _style("cover-title", "Times-Bold", 17, 21, alignment=TA_CENTER)
    centered = _style("cover-centered", "Plex", 12, 16, alignment=TA_CENTER)
    body_width = width - 38

    _centered(c, blocks[0], top - 40, body_width, bold)
    _centered(c, blocks[1], top - 76, 280, subtitle)
    _centered(c, blocks[2], top - 174, body_width, label)
    title_bottom = _centered(c, blocks[3], top - 203, body_width, title)
    _centered(c, blocks[4], title_bottom - 17, body_width, centered)
    _centered(c, blocks[5], bottom + 210, body_width, label)
    _centered(c, blocks[6], bottom + 185, body_width, subtitle)
    _centered(c, blocks[7], bottom + 102, body_width, subtitle)
    _centered(c, blocks[8], bottom + 78, body_width, subtitle)
    _centered(c, blocks[9], bottom + 40, body_width, subtitle)

    metadata = _style("cover-metadata", "Times", 9.2, 11.2, textColor=MUTED)
    heading = front[0].lstrip("# ")
    y = _paragraph(c, _plain(heading), MARGIN, 126, PAGE_W - 2 * MARGIN,
                   _style("source-heading", "Plex-SemiBold", 9.2, 11.2, textColor=MUTED))
    for block in front[1:]:
        y = _paragraph(c, _plain(block), MARGIN, y - 5, PAGE_W - 2 * MARGIN, metadata)
    if y < 47:
        raise ValueError("Catatan sampul tidak muat di atas footer.")


def _field(c, letter, label, value, y, width):
    label_width = 154
    x = MARGIN + 21
    style = _style("identity-value", "Times", 12, 13.8)
    paragraph = Paragraph(value, style)
    value_width = width - 21 - label_width - 10
    _, height = paragraph.wrap(value_width, PAGE_H)
    row_height = max(height, 14) + 4
    _paragraph(c, _plain(f"{letter}."), x, y, 16,
               _style("identity-letter", "Plex", 10.5, 13.8, textColor=MUTED))
    _paragraph(c, _plain(label), x + 20, y, label_width - 23,
               _style("identity-label", "Plex", 10.5, 13.8))
    _paragraph(c, ":", x + label_width - 4, y, 8, style)
    c.setStrokeColor(RULE)
    c.setDash(1, 2)
    c.setLineWidth(.4)
    c.line(x + label_width + 7, y - height - 1, MARGIN + width, y - height - 1)
    c.setDash()
    paragraph.drawOn(c, x + label_width + 7, y - height)
    return y - row_height


def _identity_page(c, doc, title, chairman, partner, members, signature, note):
    page_chrome(c, doc, "Lampiran · Lembar identitas", heading="Lembar Identitas")
    width = PAGE_W - 2 * MARGIN
    y = PAGE_H - 104
    heading = _style("identity-section", "Plex-SemiBold", 11.3, 15)
    data = _style("identity-data", "Times", 12, 13.8)
    _paragraph(c, "<font color='#007F86'>1.</font>  Judul", MARGIN, y, 124, heading)
    y = _paragraph(c, _plain(title), MARGIN + 126, y, width - 126, data) - 9
    y = _paragraph(c, "<font color='#007F86'>2.</font>  Ketua Tim Pelaksana", MARGIN, y, width, heading) - 6

    fields = [
        ("a", "Nama Lengkap", _plain(chairman["Nama lengkap"])),
        ("b", "Jenis Kelamin", _plain(chairman["Jenis kelamin"])),
        ("c", "NIDN/NIDK/NUPTK", "-<br/><font size='10'>Identitas profesional: "
         + _plain(chairman["Nomor identitas"]) + "</font>"),
        ("d", "Jabatan Struktural", _plain(chairman["Jabatan struktural"])),
        ("e", "Jabatan Fungsional", _plain(chairman["Jabatan fungsional/profesi"])),
        ("f", "Institusi", _plain(chairman["Institusi"])),
        ("g", "Alamat", _plain(chairman["Alamat institusi"])),
        ("h", "Telpon/Faks", _plain(chairman["Telepon/Faks"])),
        ("i", "Alamat Rumah", _plain(chairman["Alamat rumah"])),
        ("j", "Telpon/Faks/E-mail", _plain(chairman["Telepon/Email"])),
    ]
    for letter, label, value in fields:
        y = _field(c, letter, label, value, y, width)
    y -= 6
    _paragraph(c, "<font color='#007F86'>3.</font>  Lembaga Mitra Riset (*)", MARGIN, y, 187, heading)
    y = _paragraph(c, _plain(partner), MARGIN + 190, y, width - 190, data) - 8
    y = _paragraph(c, "<font color='#007F86'>4.</font>  Anggota Tim Pelaksana", MARGIN, y, width, heading) - 6

    cell = _style("member-data", "Times", 12, 13.8)
    head = _style("member-head", "Plex-SemiBold", 10.5, 13, textColor=colors.white)
    rows = [[Paragraph(text, head) for text in ["No.", "Nama", "NIK/NIP", "Institusi"]]]
    for index, member in enumerate(members, 1):
        rows.append([Paragraph(_plain(text), cell) for text in [str(index) + ".", *member]])
    table = Table(rows, colWidths=[34, 143, 126, width - 303])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), .45, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    _, height = table.wrap(width, PAGE_H)
    table.drawOn(c, MARGIN, y - height)
    y -= height + 13

    signature_x = MARGIN + width * .54
    signature_width = width * .46
    for index, block in enumerate(signature):
        if index == 2:
            y = _paragraph(c, _plain(block), signature_x, y - 12, signature_width,
                           _style("signature-placeholder", "Times-Italic", 9.5, 11.4, textColor=MUTED)) - 11
        else:
            y = _paragraph(c, _plain(block), signature_x, y, signature_width, data) - 3
    y = _paragraph(c, _plain(note), MARGIN, y - 5, width,
                   _style("identity-note", "Times", 9, 10.8, textColor=MUTED))
    if y < 47:
        raise ValueError(f"Lembar identitas tidak muat: catatan berakhir pada y={y:.1f}.")


def build_administration(output, source, helpers):
    """Write exactly two pages, preserving the source's identity data and notes."""
    front, cover, title, chairman, partner, members, signature, note = _source_data(source, helpers)
    c = canvas.Canvas(str(output), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("HematDaya - Sampul dan Lembar Identitas UMY")
    c.setAuthor(cover[4])
    doc = SimpleNamespace(page=1, leftMargin=MARGIN, rightMargin=MARGIN)
    _cover_page(c, doc, front, cover)
    c.showPage()
    doc.page = 2
    _identity_page(c, doc, title, chairman, partner, members, signature, note)
    c.showPage()
    c.save()

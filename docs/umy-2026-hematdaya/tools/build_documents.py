"""Render the frozen generic PRD and UMY proposal. Requires reportlab, markdown-it-py.

Use --font-dir with the four licensed Microsoft Times core fonts. Fonts are embedded
in the PDFs, not redistributed as repository assets. The generic Markdown stays intact.
"""
import argparse
import html
import re
from pathlib import Path

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle, Image,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
MD = MarkdownIt().enable('table')
INK = colors.HexColor('#163D42')


def clean(text):
    return re.sub('[\u2010-\u2015\u2212]', '-', text)


def escaped_text(text):
    value = html.escape(clean(text))
    for symbol in ['→', '≥']:
        value = value.replace(symbol, f'<font name="Symbols">{symbol}</font>')
    return value


def inline(children, mono=False):
    result = []
    for t in children or []:
        if t.type == 'text': result.append(escaped_text(t.content))
        elif t.type in ('softbreak', 'hardbreak'): result.append(' ' if t.type == 'softbreak' else '<br/>')
        elif t.type == 'strong_open': result.append('<b>')
        elif t.type == 'strong_close': result.append('</b>')
        elif t.type == 'em_open': result.append('<i>')
        elif t.type == 'em_close': result.append('</i>')
        elif t.type == 'code_inline':
            value = html.escape(clean(t.content))
            result.append(f'<font name="Mono">{value}</font>' if mono else value)
        elif t.type == 'link_open':
            result.append(f'<link href="{html.escape(t.attrGet("href"), quote=True)}" color="#135A70">')
        elif t.type == 'link_close': result.append('</link>')
        elif t.type == 'html_inline': result.append(html.escape(t.content))
        else: raise ValueError(f'Unhandled inline token: {t.type}')
    return ''.join(result)


def styles(family, size, leading, generic):
    base = dict(fontName=family, fontSize=size, leading=leading, textColor=colors.black,
                spaceAfter=6, splitLongWords=True, allowWidows=0, allowOrphans=0)
    s = {'p': ParagraphStyle('body', alignment=TA_JUSTIFY, **base)}
    s['list'] = ParagraphStyle('list', parent=s['p'], leftIndent=15, firstLineIndent=0, bulletIndent=0)
    for level in range(1, 5):
        hsize = (18 if level == 1 else 13 if level == 2 else 11) if generic else 12
        s[f'h{level}'] = ParagraphStyle(f'h{level}', parent=s['p'], fontName=family+'-Bold',
            fontSize=hsize, leading=hsize*1.2, alignment=TA_LEFT, keepWithNext=True,
            spaceBefore=12 if generic else 5, spaceAfter=7 if generic else 4,
            textColor=INK if generic else colors.black)
    s['cell'] = ParagraphStyle('cell', parent=s['p'], fontSize=8.4 if generic else size,
        leading=11.3 if generic else leading, alignment=TA_LEFT, spaceAfter=0, allowWidows=1)
    s['code'] = ParagraphStyle('code', fontName='Mono', fontSize=7.8, leading=10.6,
        backColor=colors.HexColor('#F1F4F5'), borderPadding=7, spaceBefore=4, spaceAfter=8)
    return s


def table(rows, sty, width, generic):
    n = len(rows[0])
    if n == 3:
        weights = [.17, .29, .54]
        if rows[0][0] == 'ID': weights = [.10, .31, .59]
    elif n == 2:
        weights = [.31, .69]
        if 'rute' in re.sub('<[^>]+>', '', rows[0][0]).lower(): weights = [.48, .52]
    else: weights = [1/n]*n
    cells = [[Paragraph(c, sty['cell']) for c in row] for row in rows]
    tbl = LongTable(cells, colWidths=[width*w for w in weights], repeatRows=1,
                    hAlign='LEFT', splitByRow=1, splitInRow=1)
    tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#B9C2C4')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EAF0F1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5 if generic else 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5 if generic else 4),
    ]))
    return tbl


def figure_row(images, width, base):
    # A paragraph holding only images becomes one row of equal-height screenshots.
    height = 4.8*cm
    cells, widths = [], []
    for t in images:
        src = base/t.attrGet('src')
        img = Image(str(src), height=height, width=height, kind='proportional')
        cells.append(img); widths.append(img.drawWidth + .3*cm)
    assert sum(widths) <= width, 'figure row too wide'
    from reportlab.platypus import Table
    row = Table([cells], colWidths=widths, hAlign='CENTER')
    row.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'),
                             ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    return row


def render_markdown(text, sty, width, generic=False, base=None):
    tokens = MD.parse(text)
    result, lists = [], []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == 'heading_open':
            p = Paragraph(inline(tokens[i+1].children, generic), sty[t.tag])
            if generic and t.tag == 'h2': p.toc_heading = True
            result.append(p); i += 3; continue
        if t.type == 'paragraph_open':
            kids = [c for c in tokens[i+1].children if c.type != 'softbreak' and not (c.type == 'text' and not c.content.strip())]
            if kids and all(c.type == 'image' for c in kids):
                result.extend([figure_row(kids, width, base), Spacer(1, 4)]); i += 3; continue
            bullet = None
            if lists:
                item = lists[-1]
                bullet = f'{item[1]}.' if item[0] == 'ordered_list_open' else '-'
                if item[0] == 'ordered_list_open': item[1] += 1
            result.append(Paragraph(inline(tokens[i+1].children, generic),
                          sty['list'] if lists else sty['p'], bulletText=bullet))
            i += 3; continue
        if t.type == 'table_open':
            rows, row = [], []
            i += 1
            while tokens[i].type != 'table_close':
                if tokens[i].type == 'tr_open': row = []
                elif tokens[i].type == 'inline': row.append(inline(tokens[i].children, generic))
                elif tokens[i].type == 'tr_close': rows.append(row)
                i += 1
            assert rows and all(len(row) == len(rows[0]) for row in rows)
            result.extend([table(rows, sty, width, generic), Spacer(1, 7)])
        elif t.type == 'fence':
            label = 'Diagram arsitektur - notasi sumber' if t.info == 'mermaid' else None
            if label: result.append(Paragraph(label, sty['h3']))
            # Wrap long code lines without changing the authoritative Markdown source.
            code = html.escape(clean(t.content)).replace(' ', '&#160;').replace('\n', '<br/>')
            result.append(Paragraph(code, sty['code']))
        elif t.type in ('bullet_list_open', 'ordered_list_open'):
            lists.append([t.type, int(t.attrGet('start') or 1)])
        elif t.type in ('bullet_list_close', 'ordered_list_close'): lists.pop()
        elif t.type == 'html_block':
            if t.content.strip() == '<!-- page -->': result.append(PageBreak())
            else: raise ValueError(f'Unhandled HTML: {t.content}')
        elif t.type == 'hr': result.append(Spacer(1, 8))
        elif t.type not in ('list_item_open', 'list_item_close', 'blockquote_open', 'blockquote_close'):
            raise ValueError(f'Unhandled block token: {t.type}')
        i += 1
    return result


class Document(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if getattr(flowable, 'toc_heading', False):
            title = flowable.getPlainText()
            key = 'section_' + re.match(r'\d+', title).group()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, 0)
            self.notify('TOCEntry', (0, title, self.page, key))


def footer(label, family):
    def paint(c, doc):
        c.saveState()
        c.setStrokeColor(colors.HexColor('#A9B9BD')); c.setLineWidth(.4)
        c.line(doc.leftMargin, 1.65*cm, A4[0]-doc.rightMargin, 1.65*cm)
        c.setFont(family, 8); c.setFillColor(colors.HexColor('#46575B'))
        c.drawString(doc.leftMargin, 1.2*cm, label)
        c.drawRightString(A4[0]-doc.rightMargin, 1.2*cm, str(doc.page))
        c.restoreState()
    return paint


def build(font_dir):
    for name, filename in [('Times','Times.TTF'), ('Times-Bold','Timesbd.TTF'),
                           ('Times-Italic','Timesi.TTF'), ('Times-BoldItalic','Timesbi.TTF')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir/filename)))
    for name, filename in [('Sans','NotoSans-Regular.ttf'), ('Sans-Bold','NotoSans-Bold.ttf'),
                           ('Sans-Italic','NotoSans-Italic.ttf'),
                           ('Sans-BoldItalic','NotoSans-BoldItalic.ttf')]:
        pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/noto/'+filename))
    pdfmetrics.registerFont(TTFont('Mono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
    pdfmetrics.registerFont(TTFont('Symbols', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    for family in ['Times', 'Sans']:
        pdfmetrics.registerFontFamily(family, normal=family, bold=family+'-Bold',
            italic=family+'-Italic', boldItalic=family+'-BoldItalic')

    source = ROOT/'submission/proposal/Proposal-HematDaya-UMY.md'
    text = source.read_text()
    summary = text.split('## 3. Executive Summary\n', 1)[1].split('## 4.', 1)[0]
    words = len(re.sub(r'\[\d+\]', '', summary).split())
    assert words <= 250, words
    proposal = Document(str(source.with_suffix('.pdf')), pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=1.65*cm, bottomMargin=2*cm,
        title='HematDaya - Proposal UMY 2026', author='Tim Petani Digital')
    pstyles = styles('Times', 12, 13.8, False)
    proposal.build(render_markdown(text, pstyles, proposal.width, base=source.parent),
                   onFirstPage=footer('Petani Digital | HematDaya | UMY 2026 | Klaster 08', 'Times'),
                   onLaterPages=footer('Petani Digital | HematDaya | UMY 2026 | Klaster 08', 'Times'))

    prd = ROOT/'prd/01_PRD_HematDaya_Generic_ID.md'
    doc = Document(str(prd.with_suffix('.pdf')), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=1.8*cm, bottomMargin=2.1*cm,
        title='HematDaya - Dokumen Kebutuhan Produk Generik 1.2', author='Tim Petani Digital')
    pst = styles('Sans', 9.7, 13.6, True)
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('toc', fontName='Sans', fontSize=9.1, leading=12.4,
                                     spaceBefore=3, leftIndent=0)]
    front, body = prd.read_text().split('## 0.', 1)
    cover = render_markdown(front, pst, doc.width, True)
    cover += [Spacer(1, 1.3*cm),
        Paragraph('Pemantauan listrik untuk rumah tangga, usaha, dan industri', pst['h1']),
        Paragraph('Satu dasar produk untuk memahami energi yang tercatat, kontribusi beban, '
                  'perubahan konsumsi, serta bukti di balik setiap pengamatan. '
                  'Jenis peralatan tidak dibatasi pada AC; jadwal dan data keluaran bersifat opsional.', pst['p']),
        Spacer(1, .4*cm), Paragraph('Keputusan inti', pst['h2']),
        table([['Aspek', 'Landasan produk'],
               ['Lingkup', 'Pemantauan dan saran. Tidak ada pengendalian atau pemutusan listrik.'],
               ['Jalur awal', 'CSV dan demo deterministik; adapter meter langsung memerlukan verifikasi.'],
               ['Kebenaran data', 'Satuan dan interval eksplisit, tanpa penghitungan ganda, data hilang bukan nol.'],
               ['Pengalaman', 'Beranda, Perangkat, dan Saran; antarmuka Indonesia dan alur yang dapat dipulihkan.'],
               ['Penggunaan kembali', 'Monolit modular, inti perhitungan bersama, modul opsional, dan adapter.']], pst, doc.width, True),
        Spacer(1, .4*cm), Paragraph('Status dokumen', pst['h2']),
        Paragraph('Spesifikasi pengembangan ini memuat 24 bagian, 22 persyaratan fungsional, '
                  '20 persyaratan UX, dan 58 skenario penerimaan. Semua target perlu dibuktikan '
                  'pada implementasi; dokumen ini tidak menyatakan integrasi, akurasi lapangan, '
                  'atau penghematan yang sudah tercapai.', pst['p']),
        PageBreak(), Paragraph('Daftar isi', pst['h2']), toc, PageBreak()]
    doc.multiBuild(cover + render_markdown('## 0.'+body, pst, doc.width, True),
                   onFirstPage=footer('HematDaya | PRD Generik 1.2 | Spesifikasi pengembangan', 'Sans'),
                   onLaterPages=footer('HematDaya | PRD Generik 1.2 | Spesifikasi pengembangan', 'Sans'))

    admin = ROOT/'submission/administrasi/Administrasi-HematDaya-UMY.md'
    adm = Document(str(admin.with_suffix('.pdf')), pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm, topMargin=1.7*cm, bottomMargin=2*cm,
        title='HematDaya - Sampul dan Lembar Identitas UMY', author='Tim Petani Digital')
    center = ParagraphStyle('cover', fontName='Times-Bold', fontSize=16, leading=21,
                            alignment=TA_CENTER, spaceAfter=10)
    small = ParagraphStyle('cover-small', parent=center, fontName='Times', fontSize=12, leading=16)
    assets = ROOT/'submission/proposal/assets'
    from reportlab.platypus import Table
    logos = Table([[Image(str(assets/'logo-tutwuri.jpg'), width=2.8*cm, height=2.8*cm, kind='proportional'),
                    Image(str(assets/'logo-lpdp.png'), width=3.7*cm, height=2.8*cm, kind='proportional')]],
                  colWidths=[4.4*cm, 4.4*cm], hAlign='CENTER')
    story = [Spacer(1, .6*cm), Paragraph('PROPOSAL', center),
             Paragraph('PESERTA PROGRAM PENDANAAN<br/>HACKATHON DEEPTECH', center),
             Spacer(1, .8*cm), logos, Spacer(1, 1*cm), Paragraph('JUDUL INOVASI', small),
             Paragraph('HematDaya: Pemantauan Listrik dan Saran Berbasis Bukti untuk Berbagai Kebutuhan', center),
             Paragraph('Tim Petani Digital', small), Spacer(1, 1.5*cm),
             Paragraph('PENYELENGGARA KEGIATAN<br/>UNIVERSITAS MUHAMMADIYAH YOGYAKARTA', small),
             Spacer(1, 1.6*cm),
             Paragraph('Direktorat Jenderal Riset dan Pengembangan<br/>Kementerian Pendidikan Tinggi, Sains, dan Teknologi', small),
             Paragraph('TAHUN 2026', center), PageBreak(), Paragraph('LEMBAR IDENTITAS', center)]
    ast = styles('Times', 10.5, 12.4, False)
    ast['cell'].fontSize = 10.5; ast['cell'].leading = 12.4
    identity = admin.read_text().split('## Lembar Identitas\n', 1)[1]
    signature_before, signature_after = identity.split('(Ruang tanda tangan - belum ditandatangani)', 1)
    story += render_markdown(signature_before, ast, adm.width)
    story += [Spacer(1, 1.1*cm)]
    story += render_markdown(signature_after, ast, adm.width)
    adm.build(story, onFirstPage=footer('HematDaya | Berkas administrasi pendamping | Belum ditandatangani', 'Times'),
              onLaterPages=footer('HematDaya | Berkas administrasi pendamping | Belum ditandatangani', 'Times'))
    from pypdf import PdfReader
    for path, expected in [(source.with_suffix('.pdf'), 3), (admin.with_suffix('.pdf'), 2)]:
        count = len(PdfReader(path).pages)
        assert count == expected, f'{path.name}: {count} pages, expected {expected}'
    print(f'Executive summary: {words} words. Proposal: 3 pages. Administration: 2 pages.')
    print(f'Generic PRD: {len(PdfReader(prd.with_suffix(".pdf")).pages)} pages.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--font-dir', type=Path, required=True)
    build(parser.parse_args().font_dir)

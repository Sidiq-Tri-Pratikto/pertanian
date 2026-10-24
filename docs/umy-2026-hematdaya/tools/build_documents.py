"""Render the frozen generic PRD and UMY proposal. Requires reportlab, markdown-it-py.

Select outputs with --only proposal administrasi (or prd, pakta). Times New Roman is
loaded from --font-dir or system fonts; IBM Plex Sans labels are bundled under OFL.
All selected PDFs are validated in a temporary directory before outputs are replaced.
The generic Markdown stays intact.
"""
import argparse
import html
import re
import shutil
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
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
        ('TOPPADDING', (0,0), (-1,-1), sty.get('table_padding', 5 if generic else 4)),
        ('BOTTOMPADDING', (0,0), (-1,-1), sty.get('table_padding', 5 if generic else 4)),
    ]))
    return tbl


def figure_row(images, width, base):
    # Preserve natural aspect ratios and a common height within the available row.
    height, gap = 4.8*cm, .3*cm
    cells, natural_widths = [], []
    for t in images:
        src = base/t.attrGet('src')
        img = Image(str(src))
        cells.append(img)
        natural_widths.append(height * img.imageWidth / img.imageHeight)
    available = width - gap * (len(cells) - 1)
    if not cells or available <= 0:
        raise ValueError('The figure row needs images and enough width for its gaps.')
    scale = min(1, available / sum(natural_widths))
    widths = []
    for index, (img, natural_width) in enumerate(zip(cells, natural_widths)):
        img.drawHeight = height * scale
        img.drawWidth = natural_width * scale
        widths.append(img.drawWidth + (gap if index < len(cells) - 1 else 0))
    from reportlab.platypus import Table
    row = Table([cells], colWidths=widths, hAlign='CENTER')
    row.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'),
                             ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), gap),
                             ('RIGHTPADDING', (-1,0), (-1,-1), 0),
                             ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
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
            result.extend([table(rows, sty, width, generic), Spacer(1, sty.get('table_space_after', 7))])
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


TARGETS = ('proposal', 'prd', 'administrasi')
TARGET_CHOICES = (*TARGETS, 'pakta')
FONT_ROOT = Path(__file__).resolve().parent / 'fonts' / 'ibm-plex-sans'


def find_font(directories, filenames, label):
    """Resolve a font without substituting an unrequested typeface."""
    for directory in directories:
        for filename in filenames:
            path = directory / filename
            if path.is_file():
                return path
    tried = ', '.join(str(directory) for directory in directories)
    raise FileNotFoundError(f'{label} was not found in: {tried}')


def register_family(name, faces):
    for suffix, path in faces.items():
        pdfmetrics.registerFont(TTFont(name + suffix, str(path)))
    pdfmetrics.registerFontFamily(
        name, normal=name, bold=name + '-Bold', italic=name + '-Italic',
        boldItalic=name + '-BoldItalic',
    )


def register_fonts(font_dir, selected):
    """Register only the families needed by the selected document targets."""
    system = [
        Path('/System/Library/Fonts/Supplemental'), Path('/Library/Fonts'),
        Path.home() / 'Library/Fonts',
        Path('/usr/share/fonts/truetype/msttcorefonts'),
        Path('/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman'),
        Path('/usr/share/fonts/truetype/noto'),
        Path('/usr/share/fonts/truetype/dejavu'),
        Path.home() / '.fonts', Path.home() / '.local/share/fonts',
    ]
    if {'proposal', 'administrasi'} & set(selected):
        times_dirs = [Path(font_dir)] if font_dir is not None else system
        names = {
            '': ('Times.TTF', 'times.ttf', 'Times_New_Roman.ttf', 'Times New Roman.ttf'),
            '-Bold': ('Timesbd.TTF', 'timesbd.ttf', 'Times_New_Roman_Bold.ttf', 'Times New Roman Bold.ttf'),
            '-Italic': ('Timesi.TTF', 'timesi.ttf', 'Times_New_Roman_Italic.ttf', 'Times New Roman Italic.ttf'),
            '-BoldItalic': ('Timesbi.TTF', 'timesbi.ttf', 'Times_New_Roman_Bold_Italic.ttf', 'Times New Roman Bold Italic.ttf'),
        }
        register_family('Times', {
            suffix: find_font(times_dirs, filenames, 'Licensed Times New Roman' + suffix)
            for suffix, filenames in names.items()
        })
    if {'proposal', 'administrasi', 'pakta'} & set(selected):
        plex = {
            '': 'IBMPlexSans-Regular.ttf', '-Bold': 'IBMPlexSans-Bold.ttf',
            '-Italic': 'IBMPlexSans-Italic.ttf', '-BoldItalic': 'IBMPlexSans-BoldItalic.ttf',
        }
        register_family('Plex', {suffix: FONT_ROOT / name for suffix, name in plex.items()})
        pdfmetrics.registerFont(TTFont('Plex-SemiBold', str(FONT_ROOT / 'IBMPlexSans-SemiBold.ttf')))
        pdfmetrics.registerFontFamily(
            'Plex-SemiBold', normal='Plex-SemiBold', bold='Plex-Bold',
            italic='Plex-Italic', boldItalic='Plex-BoldItalic',
        )
        # The template's small symbols use the same bundled, Unicode-capable face.
        pdfmetrics.registerFont(TTFont('Symbols', str(FONT_ROOT / 'IBMPlexSans-Regular.ttf')))

    if 'prd' in selected:
        names = {
            '': ('NotoSans-Regular.ttf', 'Arial.ttf', 'arial.ttf'),
            '-Bold': ('NotoSans-Bold.ttf', 'Arial Bold.ttf', 'arialbd.ttf'),
            '-Italic': ('NotoSans-Italic.ttf', 'Arial Italic.ttf', 'ariali.ttf'),
            '-BoldItalic': ('NotoSans-BoldItalic.ttf', 'Arial Bold Italic.ttf', 'arialbi.ttf'),
        }
        # Prefer Noto when installed, retaining the original Linux typography.
        sans_dirs = [Path('/usr/share/fonts/truetype/noto')] + system
        register_family('Sans', {
            suffix: find_font(sans_dirs, filenames, 'Noto Sans / Arial' + suffix)
            for suffix, filenames in names.items()
        })
        mono = find_font(
            [Path('/usr/share/fonts/truetype/dejavu')] + system,
            ('DejaVuSansMono.ttf', 'Courier New.ttf', 'cour.ttf'), 'Monospace font',
        )
        symbol = find_font(
            [Path('/usr/share/fonts/truetype/dejavu')] + system,
            ('DejaVuSans.ttf', 'Arial Unicode.ttf', 'Arial.ttf'), 'Unicode symbols font',
        )
        pdfmetrics.registerFont(TTFont('Mono', str(mono)))
        pdfmetrics.registerFont(TTFont('Symbols', str(symbol)))


def summary_word_count(source):
    text = source.read_text(encoding='utf-8')
    match = re.search(
        r'^## 3\. Executive Summary\s*\n(.*?)(?=^## 4\.)', text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError('The proposal must contain sections 3 (Executive Summary) and 4.')
    words = len(re.sub(r'\[\d+\]', '', match.group(1)).split())
    if words > 250:
        raise ValueError(f'Executive summary: {words} words; maximum is 250.')
    return words


def build_prd(output, source):
    prd = source
    doc = Document(str(output), pagesize=A4,
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



def replace_output(candidate, destination):
    """Copy to the destination filesystem, then replace the existing PDF atomically."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix='.' + destination.stem + '-', suffix='.pdf',
        dir=destination.parent, delete=False,
    ) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copyfile(candidate, temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def build(font_dir=None, only=None, output_dir=None):
    """Build selected documents; publish none if a selected document fails validation."""
    from pypdf import PdfReader

    selected = tuple(dict.fromkeys(only if only is not None else TARGETS))
    if not selected or any(target not in TARGET_CHOICES for target in selected):
        raise ValueError('Select at least one of: proposal, administrasi, prd, pakta.')
    sources = {
        'proposal': ROOT / 'submission/proposal/Proposal-HematDaya-UMY.md',
        'administrasi': ROOT / 'submission/administrasi/Administrasi-HematDaya-UMY.md',
        'prd': ROOT / 'prd/01_PRD_HematDaya_Generic_ID.md',
        'pakta': ROOT / 'submission/pakta-integritas/Pakta-Integritas-HematDaya-UMY-Revisi.md',
    }
    words = summary_word_count(sources['proposal']) if 'proposal' in selected else None
    register_fonts(font_dir, selected)
    renderers = {'prd': build_prd}
    if 'proposal' in selected:
        from umy_template import build_proposal
        renderers['proposal'] = lambda output, source: build_proposal(output, source, sys.modules[__name__])
    if 'administrasi' in selected:
        from umy_admin import build_administration
        renderers['administrasi'] = lambda output, source: build_administration(output, source, sys.modules[__name__])
    if 'pakta' in selected:
        from umy_pakta import build_pakta
        renderers['pakta'] = lambda output, source: build_pakta(output, source, sys.modules[__name__])

    with tempfile.TemporaryDirectory(prefix='umy-documents-') as directory:
        candidates, pages = {}, {}
        for target in selected:
            source = sources[target]
            candidate = Path(directory) / source.with_suffix('.pdf').name
            renderers[target](candidate, source)
            count = len(PdfReader(candidate).pages)
            if target == 'proposal' and not 1 <= count <= 3:
                raise ValueError(
                    f'Proposal: {count} pages; maximum is 3. '
                    'No output PDFs were replaced. Preserve the full text and review the layout.'
                )
            if target == 'administrasi' and count != 2:
                raise ValueError(
                    f'Administration: {count} pages; expected 2. No output PDFs were replaced.'
                )
            if target == 'pakta' and count != 2:
                raise ValueError(
                    f'Pakta integritas: {count} pages; expected 2. No output PDFs were replaced.'
                )
            candidates[target], pages[target] = candidate, count
        outputs = {}
        for target in selected:
            source = sources[target]
            destination = (
                Path(output_dir) / source.with_suffix('.pdf').name
                if output_dir is not None else source.with_suffix('.pdf')
            )
            replace_output(candidates[target], destination)
            outputs[target] = destination
            print(f'{target}: {pages[target]} pages -> {destination}')
    if words is not None:
        print(f'Executive summary: {words} words (maximum 250).')
    return outputs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--font-dir', type=Path,
        help='Directory containing licensed Times New Roman files; otherwise discover system fonts.',
    )
    parser.add_argument(
        '--only', nargs='+', choices=TARGET_CHOICES,
        help='Selected outputs; default: proposal, prd, administrasi.',
    )
    parser.add_argument(
        '--output-dir', type=Path,
        help='Write selected PDFs to this directory instead of replacing repository PDFs.',
    )
    args = parser.parse_args()
    build(args.font_dir, args.only, args.output_dir)

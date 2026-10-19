# Cap header dan footer gaya templat UMY. Pemakaian: stamp_umy.py berkas.pdf "JUDUL FOOTER" "LABEL KANAN" [skip_first_page=1] [header_on_first=0]
import sys, os, pymupdf
src, foot, rlabel = sys.argv[1], sys.argv[2], sys.argv[3]
skip_first = (sys.argv[4] if len(sys.argv) > 4 else "1") == "1"       # sampul tanpa furnitur
header_first = (sys.argv[5] if len(sys.argv) > 5 else "1") == "1"      # header di halaman pertama non-sampul
GREY = (0x5B/255, 0x67/255, 0x79/255); TEAL = (0x0A/255, 0x79/255, 0x80/255); NAVY = (0x0A/255, 0x1D/255, 0x36/255); RULE = (0xDD/255, 0xE4/255, 0xE8/255)
def width(t, size, font, sp):
    return sum(pymupdf.get_text_length(c, fontname=font, fontsize=size) for c in t) + sp * (len(t) - 1)
def spaced(page, x, y, t, size, color, font, sp, right=False):
    if right: x -= width(t, size, font, sp)
    for c in t:
        page.insert_text(pymupdf.Point(x, y), c, fontname=font, fontsize=size, color=color)
        x += pymupdf.get_text_length(c, fontname=font, fontsize=size) + sp
doc = pymupdf.open(src)
L = 2.5 / 2.54 * 72
for i, page in enumerate(doc):
    if skip_first and i == 0: continue
    W, Hh = page.rect.width, page.rect.height
    first_body = (i == (1 if skip_first else 0))
    if not first_body or header_first:
        spaced(page, L, 42, "UMY HACKATHON DEEPTECH 2026", 7.2, GREY, "helv", 1.7)
        spaced(page, W - L, 42, rlabel, 7.2, TEAL, "hebo", 1.7, right=True)
    num = str(i + 1)
    fw = width(foot, 8.2, "helv", 0)
    page.insert_text(pymupdf.Point(L, Hh - 36), foot, fontname="helv", fontsize=8.2, color=GREY)
    nw = pymupdf.get_text_length(num, fontname="hebo", fontsize=8.5)
    page.insert_text(pymupdf.Point(W - L - nw, Hh - 36), num, fontname="hebo", fontsize=8.5, color=NAVY)
    page.draw_line(pymupdf.Point(L + fw + 16, Hh - 38.5), pymupdf.Point(W - L - nw - 16, Hh - 38.5), color=RULE, width=0.8)
tmp = src + ".tmp"; doc.save(tmp, garbage=3, deflate=True); doc.close(); os.replace(tmp, src)
print("dicap:", src, "halaman", len(doc) if False else "ok")

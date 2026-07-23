import json, sys
sys.path.insert(0, '/usr/lib64/python3.14/site-packages')
from fpdf import FPDF

pdf = FPDF(unit='mm', format='A4')
pdf.add_page()

bins = json.load(open('bins.json'))
uuids = list(bins.keys())
img_path = 'prullenbak-qr.png'

# 2x2 grid, each 40mm, 10mm gap between them, centered on A4
cell = 40
gap = 10
tw = 2 * cell + gap
start_x = (210 - tw) / 2
start_y = (297 - tw) / 2

pad = 2
line_w = 0.5
qr_w = 36

for i in range(4):
    uuid = uuids[i] if i < len(uuids) else uuids[0]
    col = i % 2
    row = i // 2
    x = start_x + col * (cell + gap)
    y = start_y + row * (cell + gap)

    pdf.set_line_width(line_w)
    pdf.set_draw_color(51, 51, 51)
    pdf.rect(x, y, cell, cell)

    qr_off = (cell - qr_w) / 2
    pdf.image(img_path, x + qr_off, y + pad, w=qr_w)

# UUID in leesbaar font bovenaan de pagina
uuid = uuids[0]
pdf.set_font('Courier', '', 12)
pdf.set_text_color(51, 51, 51)
pdf.set_xy(0, 10)
pdf.cell(210, 7, f"UUID: {uuid}", align='C')

pdf.output('qr-afdruk.pdf')
print('OK')

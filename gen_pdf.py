import json, sys, io, qrcode
sys.path.insert(0, '/usr/lib64/python3.14/site-packages')
from fpdf import FPDF

bins = json.load(open('bins.json'))
ids = list(bins.keys())

# Generate a QR for each bin
qrs = {}
for bid in ids[:4]:
    url = f"https://qrmeldingen.github.io/zaanstad/m.html?id={bid}"
    img = qrcode.make(url, box_size=10, border=1)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qrs[bid] = buf

pdf = FPDF(unit='mm', format='A4')
pdf.add_page()

cell = 40
gap = 10
tw = 2 * cell + gap
start_x = (210 - tw) / 2
start_y = (297 - tw) / 2

pad = 2
line_w = 0.5
qr_w = 36

for i in range(4):
    bid = ids[i] if i < len(ids) else ids[0]
    col = i % 2
    row = i // 2
    x = start_x + col * (cell + gap)
    y = start_y + row * (cell + gap)

    pdf.set_line_width(line_w)
    pdf.set_draw_color(51, 51, 51)
    pdf.rect(x, y, cell, cell)

    qr_off = (cell - qr_w) / 2
    pdf.image(qrs[bid], x + qr_off, y + pad, w=qr_w)

pdf.set_font('Courier', '', 12)
pdf.set_text_color(51, 51, 51)
pdf.set_xy(0, 10)
pdf.cell(210, 7, f"Bak: {ids[0]}", align='C')

pdf.output('qr-afdruk.pdf')
print('OK')

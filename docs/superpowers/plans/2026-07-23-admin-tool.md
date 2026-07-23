# Admin Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Bouw een interne web-tool op meldingen.eddydevink.nl om prullenbakken te registreren

**Architecture:** FastAPI app op Nextcloud server, nginx reverse proxy, GitHub Pages voor publiek

**Tech Stack:** Python 3.14, FastAPI, uvicorn, fpdf2, qrcode[pil], nginx, systemd, DirectAdmin API

---

### Task 1: Server voorbereiden — packages, git clone, SSH key

**Files:**
- Create: (server) `/home/aiaiaiaiagent/meldingen-app/.gitconfig`
- Modify: (server) git config

- [ ] **Step 1: SSH naar nextcloud en installeer Python packages**

```bash
ssh nextcloud
pip install fpdf2 qrcode[pil]
```

Expected: packages installed successfully

- [ ] **Step 2: Clone de repo op de server**

```bash
ssh nextcloud
mkdir -p /home/aiaiaiaiagent/meldingen-app
cd /home/aiaiaiaiagent/meldingen-app
git clone git@github.com:qrmeldingen/zaanstad.git repo
```

Expected: repo cloned to `/home/aiaiaiaiagent/meldingen-app/repo/`

- [ ] **Step 3: Genereer SSH key voor git push zonder prompts**

```bash
ssh nextcloud
ssh-keygen -t ed25519 -f /home/aiaiaiaiagent/.ssh/id_ed25519_qrmeldingen -N ""
cat /home/aiaiaiaiagent/.ssh/id_ed25519_qrmeldingen.pub
```

Voeg de public key toe aan GitHub (qrmeldingen account) via Settings → SSH keys

- [ ] **Step 4: Configureer SSH voor qrmeldingen**

Create `/home/aiaiaiaiagent/.ssh/config.d/qrmeldingen`:
```
Host github.com-qrmeldingen
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_qrmeldingen
```

En voeg `Include ~/.ssh/config.d/*` toe aan `/home/aiaiaiaiagent/.ssh/config`.

---

### Task 2: DNS record — DirectAdmin + WAN IP Guard

**Files:**
- Modify: (server) `/home/aiaiaiaiagent/wan-ip-guard/.env` — voeg `meldingen` toe aan DOMAINS

- [ ] **Step 1: Voeg A-record toe via DirectAdmin API**

```bash
ssh nextcloud
# Haal credentials uit wan-ip-guard .env
source /home/aiaiaiaiagent/wan-ip-guard/.env
# Voeg A-record toe
curl -X POST "https://s246.webhostingserver.nl:2223/CMD_API_DNS_CONTROL" \
  -u "$DIRECTADMIN_USER:$DIRECTADMIN_LOGIN_KEY" \
  -d "domain=eddydevink.nl&action=add&type=A&name=meldingen&value=$(curl -s ifconfig.me)"
```

- [ ] **Step 2: Voeg meldingen.eddydevink.nl toe aan WAN IP Guard**

Edit `/home/aiaiaiaiagent/wan-ip-guard/.env`:
Voeg `meldingen` toe aan de DOMAINS lijst zodat WAN IP Guard het A-record automatisch updatet bij IP wijziging.

- [ ] **Step 3: Test DNS resolutie**

```bash
dig meldingen.eddydevink.nl +short
```
Expected: het WAN IP van de server

---

### Task 3: FastAPI app — main.py

**Files:**
- Create: (server) `/home/aiaiaiaiagent/meldingen-app/app/main.py`
- Create: (server) `/home/aiaiaiaiagent/meldingen-app/app/__init__.py`
- Create: (server) `/home/aiaiaiaiagent/meldingen-app/repo/` (git repo path)

- [ ] **Step 1: Write main.py**

```python
import json
import uuid as uuid_mod
import subprocess
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
import qrcode

app = FastAPI()

REPO = Path(__file__).resolve().parent.parent / "repo"
BINS = REPO / "bins.json"
QR_DIR = REPO
PDF_PATH = REPO / "qr-afdruk.pdf"
GEN_PDF = REPO / "gen_pdf.py"

TEMPLATE = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nieuwe prullenbak registreren</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: sans-serif; max-width: 500px; margin: 2em auto; padding: 1em; }}
  h1 {{ font-size: 1.4em; margin-bottom: 1em; }}
  label {{ display: block; margin-top: 1em; font-weight: bold; }}
  input, textarea {{ width: 100%; padding: 0.6em; font-size: 1em; border: 1px solid #ccc; border-radius: 4px; }}
  textarea {{ height: 4em; }}
  button {{ width: 100%; padding: 0.8em; font-size: 1.1em; margin-top: 1.5em; border: none; border-radius: 4px; cursor: pointer; }}
  .btn-primary {{ background: #2563eb; color: #fff; }}
  .btn-secondary {{ background: #e5e7eb; color: #111; }}
  .result {{ margin-top: 2em; padding: 1em; background: #f0fdf4; border: 1px solid #16a34a; border-radius: 4px; display: none; }}
  .result img {{ display: block; max-width: 200px; margin: 1em auto; }}
  .error {{ background: #fef2f2; border-color: #dc2626; }}
  #status {{ margin-top: 1em; font-style: italic; }}
</style>
</head>
<body>
<h1>Nieuwe prullenbak</h1>
<form id="form">
  <label>Tekst (optioneel)</label>
  <textarea id="text" placeholder="volle prullenbak">volle prullenbak</textarea>
  <button type="button" class="btn-secondary" id="btn-gps">Huidige locatie ophalen</button>
  <div id="coords"></div>
  <button type="submit" class="btn-primary" id="btn-submit" disabled>Opslaan</button>
</form>
<div id="status"></div>
<div class="result" id="result">
  <h2>Opgeslagen!</h2>
  <p id="result-uuid"></p>
  <img id="result-qr" src="" alt="QR">
  <a id="result-pdf" href="" target="_blank">PDF openen</a>
</div>
<script>
let currentLat = null, currentLng = null;
const coordsEl = document.getElementById('coords');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const btnSubmit = document.getElementById('btn-submit');

document.getElementById('btn-gps').onclick = () => {{
  statusEl.textContent = 'Locatie bepalen...';
  navigator.geolocation.getCurrentPosition(
    pos => {{
      currentLat = pos.coords.latitude;
      currentLng = pos.coords.longitude;
      coordsEl.innerHTML = `<p>📍 {currentLat.toFixed(5)}, {currentLng.toFixed(5)}</p>`;
      btnSubmit.disabled = false;
      statusEl.textContent = '';
    }},
    err => {{ statusEl.innerHTML = '<span style="color:#c00">GPS fout: ' + err.message + '</span>'; }},
    {{ enableHighAccuracy: true }}
  );
}};

document.getElementById('form').onsubmit = async e => {{
  e.preventDefault();
  if (!currentLat) return;
  statusEl.textContent = 'Bezig met opslaan...';
  const text = document.getElementById('text').value || 'volle prullenbak';
  const res = await fetch('/register', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ lat: currentLat, lng: currentLng, text }})
  }});
  const data = await res.json();
  statusEl.textContent = '';
  if (res.ok) {{
    resultEl.style.display = 'block';
    document.getElementById('result-uuid').textContent = 'UUID: ' + data.uuid;
    document.getElementById('result-qr').src = data.uuid + '.png';
    document.getElementById('result-pdf').href = data.pdf_url;
  }} else {{
    statusEl.innerHTML = '<span style="color:#c00">Fout: ' + JSON.stringify(data) + '</span>';
  }}
}};
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def form():
    return TEMPLATE


@app.post("/register")
async def register(lat: float = Form(...), lng: float = Form(...), text: str = Form("volle prullenbak")):
    uid = str(uuid_mod.uuid4())
    cat = "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/afval/sub_categories/afvalbak"

    # Update bins.json
    bins = json.loads(BINS.read_text()) if BINS.exists() else {}
    bins[uid] = {"lat": lat, "lng": lng, "text": text, "cat": cat}
    BINS.write_text(json.dumps(bins, indent=2, ensure_ascii=False) + "\n")

    # Genereer QR
    qr_url = f"https://qrmeldingen.github.io/zaanstad/m.html?uuid={uid}"
    qr_img = qrcode.make(qr_url)
    qr_path = QR_DIR / f"{uid}.png"
    qr_img.save(qr_path)

    # Genereer PDF
    subprocess.run(["python3", str(GEN_PDF)], cwd=str(REPO), check=True)

    # Git commit + push
    subprocess.run(["git", "add", "bins.json", f"{uid}.png", "qr-afdruk.pdf"], cwd=str(REPO), check=True)
    subprocess.run(["git", "commit", "-m", f"Voeg prullenbak {uid[:8]} toe"], cwd=str(REPO), check=True)
    subprocess.run(["git", "push"], cwd=str(REPO), check=True)

    pdf_url = f"{uid}.png"  # client-side relative

    return {"uuid": uid, "qr_url": f"{uid}.png", "pdf_url": "qr-afdruk.pdf"}
```

Let op: We gebruiken `Form(...)` ipv `Body(...)` omdat het formulier `application/x-www-form-urlencoded` stuurt via JS.

- [ ] **Step 2: Write `__init__.py`**

```python
# empty
```

- [ ] **Step 3: Test app lokaal op server**

```bash
ssh nextcloud
cd /home/aiaiaiaiagent/meldingen-app
uvicorn app.main:app --port 8001 --host 127.0.0.1
```

Test in tweede terminal:
```bash
curl -X POST "http://127.0.0.1:8001/register" \
  -d "lat=52.456&lng=4.818&text=test"
```
Expected: JSON response met uuid, qr_url, pdf_url

---

### Task 4: gen_pdf.py aanpassen voor server-gebruik

**Files:**
- Modify: (repo) `gen_pdf.py`

- [ ] **Step 1: Pas gen_pdf.py aan zodat hij ook meerdere UUIDs correct toont**

```python
import json, sys
from pathlib import Path
from fpdf import FPDF

repo = Path(__file__).resolve().parent
bins = json.loads((repo / "bins.json").read_text())
uuids = list(bins.keys())
img_path = repo / "prullenbak-qr.png"

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
    uid = uuids[i] if i < len(uuids) else uuids[0]
    qr_file = repo / f"{uid}.png"
    if not qr_file.exists():
        qr_file = img_path
    col = i % 2
    row = i // 2
    x = start_x + col * (cell + gap)
    y = start_y + row * (cell + gap)
    pdf.set_line_width(line_w)
    pdf.set_draw_color(51, 51, 51)
    pdf.rect(x, y, cell, cell)
    qr_off = (cell - qr_w) / 2
    pdf.image(str(qr_file), x + qr_off, y + pad, w=qr_w)

pdf.output(str(repo / "qr-afdruk.pdf"))
print('OK')
```

- [ ] **Step 2: Test lokaal**

```bash
cd /tmp/melding && python3 gen_pdf.py && ls -lh qr-afdruk.pdf
```
Expected: PDF gegenereerd

---

### Task 5: Nginx vhost + systemd service

**Files:**
- Create: (server) `/etc/nginx/conf.d/meldingen.eddydevink.nl.conf`
- Create: (server) `/etc/systemd/system/meldingen-app.service`

- [ ] **Step 1: Schrijf systemd unit**

```ini
[Unit]
Description=QR Meldingen Admin Tool
After=network.target

[Service]
Type=simple
User=aiaiaiaiagent
WorkingDirectory=/home/aiaiaiaiagent/meldingen-app
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
ssh nextcloud
sudo -A tee /etc/systemd/system/meldingen-app.service << 'EOF'
[Unit]
Description=QR Meldingen Admin Tool
After=network.target

[Service]
Type=simple
User=aiaiaiaiagent
WorkingDirectory=/home/aiaiaiaiagent/meldingen-app
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo -A systemctl daemon-reload
sudo -A systemctl enable --now meldingen-app
sudo -A systemctl status meldingen-app
```

- [ ] **Step 2: Schrijf nginx vhost**

```nginx
server {
    server_name meldingen.eddydevink.nl;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/meldingen.eddydevink.nl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/meldingen.eddydevink.nl/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = meldingen.eddydevink.nl) {
        return 301 https://$host$request_uri;
    }
    listen 80;
    server_name meldingen.eddydevink.nl;
    return 404;
}
```

```bash
ssh nextcloud
sudo -A tee /etc/nginx/conf.d/meldingen.eddydevink.nl.conf << 'NGINXCONF'
server {
    server_name meldingen.eddydevink.nl;
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/meldingen.eddydevink.nl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/meldingen.eddydevink.nl/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}
server {
    if ($host = meldingen.eddydevink.nl) { return 301 https://$host$request_uri; }
    listen 80;
    server_name meldingen.eddydevink.nl;
    return 404;
}
NGINXCONF
```

- [ ] **Step 3: Certbot SSL certificaat aanvragen**

```bash
ssh nextcloud
sudo -A certbot --nginx -d meldingen.eddydevink.nl
```

- [ ] **Step 4: Nginx herladen**

```bash
ssh nextcloud
sudo -A nginx -t && sudo -A systemctl reload nginx
```

---

### Task 6: Test de volledige flow

- [ ] **Step 1: Test formulier via browser**

Open `https://meldingen.eddydevink.nl/` op Android.
Verwacht: formulier met GPS knop en tekstveld.

- [ ] **Step 2: Test registratie**

Klik "Huidige locatie ophalen", wacht op GPS, klik "Opslaan".
Verwacht: UUID + QR + PDF link.

- [ ] **Step 3: Controleer GitHub Pages**

Open `https://qrmeldingen.github.io/zaanstad/m.html?uuid=<nieuwe-uuid>`
Verwacht: "Melding verstuurd!" met SIG-nummer.

- [ ] **Step 4: Commit plan en design doc**

```bash
cd /tmp/melding
git add docs/
git commit -m "Voeg design doc en implementatieplan toe voor admin tool"
git push
```

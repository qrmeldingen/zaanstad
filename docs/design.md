# QR-meldingen Admin Tool — Design

**Datum:** 2026-07-23
**Project:** qrmeldingen/zaanstad

## Doel

Een interne web-tool op `meldingen.eddydevink.nl` waarmee ik op locatie (Android) nieuwe
prullenbakken kan registreren. De tool slaat de data lokaal op in `bins.json`, genereert
QR-code en afdruk-PDF, en pusht naar GitHub Pages zodat de publieke scan-pagina (`m.html`)
de nieuwe bak kent.

## Architectuur

```
┌─────────────────────┐       GPS + formulier        ┌──────────────────────────────┐
│  Android Phone      │  ───────────────────────────▶  │  Nextcloud server (Fedora)   │
│  (Chrome, GPS aan)  │                               │  nginx → FastAPI (8001)     │
└─────────────────────┘                               │  systemd service            │
        ▲                                              │  Git repo: qrmeldingen/     │
        │                                              └──────────┬───────────────────┘
        │                                                         │ git commit + push
        │                                                         ▼
        │                                               ┌──────────────────────┐
        │                                               │  GitHub Pages         │
        └───────────────────────────────────────────────│  qrmeldingen.github. │
                  Publiek: scan QR → m.html               io/zaanstad            │
                                                        └──────────────────────┘
```

## Componenten

### 1. FastAPI app (`meldingen-app`)

- Locatie op nextcloud server
- Python 3.14 + FastAPI + uvicorn
- Systemd service op poort 8001

**Endpoints:**
- `GET /` — HTML-formulier (enkele pagina, geen framework)
- `POST /register` — JSON body `{lat, lng, text}`, returns `{uuid, qr_url, pdf_url}`

**Acties bij register:**
1. Genereer UUID v4
2. Voeg entry toe aan `bins.json`
3. Genereer QR-code PNG (`<uuid>.png`, 500x500)
4. Genereer PDF (4 stickers A4 via `gen_pdf.py`)
5. Git add + commit + push naar `github.com/qrmeldingen/zaanstad`
6. Response: `{uuid, qr_url, pdf_url}`

### 2. Formulier (HTML + JS)

- Single HTML-pagina, gemobieliseerd
- GPS via `navigator.geolocation.getCurrentPosition()`
- Velden: lat/lng (auto), text (default "volle prullenbak")
- "Huidige locatie" + "Opslaan" knoppen
- Na submit: toont UUID + QR inline + PDF link

### 3. Nginx vhost

- `server_name meldingen.eddydevink.nl`
- SSL via Certbot
- Proxy pass naar `http://127.0.0.1:8001`

### 4. DNS

- A-record `meldingen.eddydevink.nl` via DirectAdmin
- Toevoegen aan WAN IP Guard update-lijst

### 5. Bestaande GitHub Pages

- `m.html` — onveranderd
- `bins.json` — wordt geüpdatet door admin-tool
- `<uuid>.png` — QR per bak
- `qr-afdruk.pdf` — hergenereerd na elke wijziging

## Veldenset (in `bins.json`)

```json
{
  "<uuid>": {
    "lat": 52.45659,
    "lng": 4.81898,
    "text": "volle prullenbak",
    "cat": "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/afval/sub_categories/afvalbak"
  }
}
```

## Vereisten op server

- `fpdf2 qrcode` pip packages installeren
- Git clone van qrmeldingen/zaanstad
- SSH key voor git push zonder prompts
- Systemd unit
- DirectAdmin A-record + WAN IP Guard update

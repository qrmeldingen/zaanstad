# QR Meldingen Zaanstad

Scan de QR-code met je smartphone → melding wordt automatisch verstuurd naar de gemeente Zaanstad.

## Voor wie

Voor vaste meldingen op steeds dezelfde locatie, zoals een vaak volle prullenbak. Geen formulier meer doorlopen — één scan en de melding is weg.

## Hoe het werkt

1. Elke locatie heeft een uniek UUID
2. UUID staat in `bins.json` met coördinaten, categorie en omschrijving
3. `m.html` leest de UUID uit de URL, zoekt de data op in `bins.json` en POST direct naar de SIA API
4. Na versturen wordt de teller opgehoogd via countapi.mileshilliard.com

## Bestanden

| Bestand | Doel |
|---|---|
| `m.html` | Melding-pagina — scan QR → POST |
| `bins.json` | UUID → locatie, categorie, tekst |
| `stats.html` | Overzicht van alle UUIDs met scan-tellingen |
| `prullenbak-qr.png` | QR-code voor deze prullenbak |

## Nieuwe locatie toevoegen

1. Genereer een UUID (bv. via `uuidgen` of https://uuidgenerator.net)
2. Voeg entry toe aan `bins.json`:
   ```json
   "jouw-uuid-hier": {
     "lat": 52.45659,
     "lng": 4.81898,
     "text": "omschrijving",
     "cat": "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/overig/sub_categories/overig"
   }
   ```
3. Genereer QR-code naar `https://qrmeldingen.github.io/zaanstad/m.html?uuid=<jouw-uuid>`
4. Print en plak op de locatie

## Categorieën

De `cat`-URL bepaalt het type melding. Voorbeelden uit de SIA API:

- `overig/overig` — `https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/overig/sub_categories/overig`

Vind de juiste categorie via `https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/`.

## API

De POST gaat naar `https://api.meldingen.zaanstad.nl/signals/v1/public/signals/`.

Body:
```json
{
  "location": {
    "geometrie": {
      "type": "Point",
      "coordinates": [lng, lat]
    }
  },
  "source": "online",
  "category": {
    "sub_category": "https://...terms/categories/.../sub_categories/..."
  },
  "reporter": { "sharing_allowed": false },
  "incident_date_start": "ISO datum",
  "text": "omschrijving"
}
```

## Statistieken

Per UUID wordt het aantal scans bijgehouden via [countapi.mileshilliard.com](https://countapi.mileshilliard.com/).

- Overzicht: `https://qrmeldingen.github.io/zaanstad/stats.html`
- Teller raadplegen: `GET https://countapi.mileshilliard.com/api/v1/get/zaanstad_<UUID>`

## Steden uitbreiden

Per stad een aparte repo maken:
- `qrmeldingen/zaanstad`
- `qrmeldingen/amsterdam`
- etc.

## Tech

- Hosting: GitHub Pages (statisch, gratis, HTTPS)
- Tellingen: countapi.mileshilliard.com (gratis, geen account nodig)
- API: SIA (Signalen) van de gemeente — CORS staat `*` toe

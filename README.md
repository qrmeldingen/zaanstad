# QR Meldingen Zaanstad

Scan de QR-code op een prullenbak → bevestig → melding naar de gemeente Zaanstad.

## Hoe het werkt

1. Elke prullenbak heeft een gemeentelijk ID (bv. `4120958`) uit de open data van Zaanstad
2. ID + GPS-coördinaten staan in `bins.json` (2038 bakken uit WFS `geo:bor_afvalbak`)
3. QR-code bevat `https://qrmeldingen.github.io/zaanstad/m.html?id=<ID>`
4. `m.html` toont type, wijk en een kaartje met pin — gebruiker bevestigt
5. Na bevestiging: POST naar Signalen API van de gemeente
6. Gemeente ontvangt melding (bv. `SIG-113767`)

## Bestanden

| Bestand | Doel |
|---|---|
| `m.html` | Scan-pagina met bevestigingsscherm + Leaflet-kaart |
| `bins.json` | Alle 2038 prullenbakken met ID, lat/lng, type, wijk |
| `fetch_bins.py` | Downloadt actuele data van de Zaanstad WFS |
| `gen_pdf.py` | Genereert afdruk-PDF met 4 QR-stickers per A4 |
| `stats.html` | Overzicht met scan-tellingen |
| `docs/zaanstad-open-data.md` | Documentatie van de WFS-bron |
| `docs/design.md` | Oorspronkelijk ontwerp (verouderd) |

## Flow

```
QR scannen → m.html?id=4120958
  → bins.json laden
  → toon: type + wijk + kaart
  → gebruiker: [Ja, melden] of [Annuleren]
  → POST naar api.meldingen.zaanstad.nl/signals/v1/public/signals/
  → resultaat: "Melding verstuurd: SIG-xxxxx"
```

## Data: gemeente Zaanstad WFS

Alle 2038 straatprullenbakken komen uit de officiële open data op:

```
https://maps.zaanstad.nl/geoserver/wfs?service=WFS&version=2.0.0
  &request=GetFeature&typeName=geo:bor_afvalbak
  &outputFormat=application/json&srsName=EPSG:4326
```

Zie `docs/zaanstad-open-data.md` voor alle velden en queries.

## Nieuwe locatie toevoegen (handmatig)

1. Kies een uniek ID (of gebruik een UUID voor niet-WFS-bakken)
2. Voeg entry toe aan `bins.json`:
   ```json
   "4120958": {
     "lat": 52.42994639,
     "lng": 4.84677886,
     "text": "Enkele bak - Zaandam Zuid",
     "cat": "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/afval/sub_categories/afvalbak",
     "source": "wfs"
   }
   ```
   Voor handmatige bakken: `"source": "manual"`.
3. Genereer QR naar `https://qrmeldingen.github.io/zaanstad/m.html?id=<ID>`
4. Print en plak

## Dataset opfrissen

```bash
python3 fetch_bins.py
git add bins.json && git commit -m "Ververs data" && git push
```

Let op: handmatige bakken (`source: manual`) gaan verloren bij een verse download.

## Tech

- Hosting: GitHub Pages (statisch, gratis, HTTPS)
- Kaart: Leaflet + OpenStreetMap tiles (gratis, geen API key)
- Meldingen: Signalen (SIA) API van de gemeente — CORS staat `*` toe
- Tellingen: countapi.mileshilliard.com

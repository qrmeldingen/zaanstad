# Open Data: Afvalbakken Gemeente Zaanstad

## WFS-endpoint

De gemeente Zaanstad ontsluit geografische data via een publieke GeoServer:

```
https://maps.zaanstad.nl/geoserver/wfs
```

## Beschikbare afval-lagen

Uit `GetCapabilities` en `DescribeFeatureType` zijn deze relevante lagen gevonden:

| Laag | Omschrijving |
|---|---|
| `geo:bor_afvalbak` | Straatprullenbakken (beheer openbare ruimte) |
| `geo:afvalcontainers` | Grote ondergrondse/bovengrondse verzamelcontainers |

Alleen `geo:bor_afvalbak` is gebruikt — die bevat de kleine straatprullenbakken
die geschikt zijn voor QR-meldingen.

## Laag `geo:bor_afvalbak` — velden

| Veld | Type | Voorbeeld |
|---|---|---|
| `id` | string | `4120958` |
| `objectnummer` | string | `null` |
| `guid` | string | `{47D8293A-075E-4B12-A503-02AD8C2D9EA2}` |
| `type` | string | `Enkele bak` |
| `type_afval` | string | `null` |
| `ondergronds` | string | `null` |
| `beheerder_gedetailleerd` | string | `Gemeente Zaanstad OR - Afval en Reiniging` |
| `eigenaar_gedetailleerd` | string | `Gemeente Zaanstad` |
| `onderhoudsplichtige` | string | `null` |
| `wijk` | string | `Zaandam Zuid` |
| `buurt` | string | `Vijfhoekpark` |
| `lastupdate` | string | `20250507171334` |
| `valid_from` | string | `20230724075436` |
| `valid_till` | string | `null` |
| `geom` | Point | RD (EPSG:28992) of WGS84 (EPSG:4326) |

## Coordinaten

RD-coordinaten (EPSG:28992) worden standaard geleverd.
Met `srsName=EPSG:4326` worden WGS84-coordinaten teruggegeven,
waarbij de GeoJSON-conventie `[lng, lat]` wordt aangehouden.

## Data ophalen

### Alle bakken als GeoJSON (WGS84)

```
https://maps.zaanstad.nl/geoserver/wfs
  ?service=WFS
  &version=2.0.0
  &request=GetFeature
  &typeName=geo:bor_afvalbak
  &outputFormat=application/json
  &srsName=EPSG:4326
  &count=2100
```

Let op: `count` moet hoger zijn dan het aantal features (2038) om alles in één
response te krijgen. De server ondersteunt geen paginering via `startIndex`
voor deze laag (geeft 400 error).

### Alleen bepaalde velden (sneller)

```
  &propertyName=id,type,wijk,buurt
```

## Gedownloade data

- **Datum:** 2026-07-24
- **Totaal:** 2038 features (waarvan 5 zonder geometrie)
- **ID-bereik:** `4120958` t/m `6251086` (niet aaneengesloten)
- **Script:** `fetch_bins.py` in de repo-root
- **Output:** `bins.json` (325 kB) — het centrale register voor QR-meldingen

### Types (aantallen)

| Type | Aantal |
|---|---|
| Enkele bak | 790 |
| Enkele bak met afsluitklep | 564 |
| Hondenpoepbak | 418 |
| Onbekend (type=null) | 85 |
| Minicontainer | 49 |
| Blikmikker | 30 |
| Persbak | 25 |
| Afvalbak met bovenkap | 23 |
| Uitneembare afvalbak | 20 |
| Afvalbak met omhulsel | 16 |
| Adoptiebak | 13 |
| Afvalbak met omlijsting | 4 |
| Peukentegel | 1 |

### Verdeling over wijken (top 10)

| Wijk | Aantal |
|---|---|
| Wormerveer | 169 |
| Assendelft-Noord | 160 |
| Zaandam Zuid | 155 |
| Nieuw West | 132 |
| Zaandam West | 129 |
| Pelders- en Hoornseveld | 124 |
| Krommenie Oost | 124 |
| Oude Haven | 123 |
| Poelenburg | 116 |
| Zaandam Noord | 108 |

## Conversie naar bins.json

Het script `fetch_bins.py` doet:

1. GET-request naar WFS met `srsName=EPSG:4326`
2. Elke feature wordt omgezet naar een entry in `bins.json`
3. De gemeentelijke `id` wordt gebruikt als key (bv. `"4120958"`)
4. Coordinaten worden afgerond op 8 decimalen
5. Veld `text` wordt samengesteld uit `type - wijk`
6. Veld `cat` bevat de Signalen API-categorie-URL voor `afval/afvalbak`
7. Veld `source: "wfs"` markert de herkomst

```json
{
  "4120958": {
    "lat": 52.42994639,
    "lng": 4.84677886,
    "text": "Enkele bak - Zaandam Zuid",
    "cat": "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/afval/sub_categories/afvalbak",
    "source": "wfs"
  }
}
```

## Dataset opfrissen

De WFS-data verandert niet vaak, maar voor een verse download:

```bash
python3 fetch_bins.py
```

Dit overschrijft `bins.json` met de actuele data van de gemeente.
Let op: handmatig toegevoegde bakken (`source: "manual"`) gaan dan verloren.

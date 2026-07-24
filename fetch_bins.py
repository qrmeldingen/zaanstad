import json, urllib.request

WFS_URL = (
    "https://maps.zaanstad.nl/geoserver/wfs"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeName=geo:bor_afvalbak"
    "&outputFormat=application/json"
    "&srsName=EPSG:4326"
    "&count=2100"
)

resp = urllib.request.urlopen(WFS_URL)
data = json.load(resp)

bins = {}
for f in data["features"]:
    geom = f.get("geometry")
    if geom is None:
        continue
    lng, lat = geom["coordinates"]
    props = f["properties"]
    bin_id = str(props["id"])
    typ = props["type"] or "Onbekend"
    wijk = props["wijk"] or "Onbekend"
    bins[bin_id] = {
        "lat": round(lat, 8),
        "lng": round(lng, 8),
        "text": f"{typ} - {wijk}",
        "cat": "https://api.meldingen.zaanstad.nl/signals/v1/public/terms/categories/afval/sub_categories/afvalbak",
        "source": "wfs",
    }

with open("bins.json", "w") as out:
    json.dump(bins, out, indent=2, ensure_ascii=False)

print(f"Geschreven: {len(bins)} afvalbakken naar bins.json")

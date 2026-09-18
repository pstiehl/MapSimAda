"""Fetch the Val d'Orcia OSM extract from Overpass. Data (c) OpenStreetMap contributors, ODbL."""
import pathlib, requests
OUT = pathlib.Path(__file__).resolve().parents[1]/"data/raw/osm"
OUT.mkdir(parents=True, exist_ok=True)
BBOX = "42.98,11.48,43.12,11.68"
Q = f"""[out:json][timeout:180];
(
  way["railway"~"^(rail|narrow_gauge|disused|abandoned)$"]({BBOX});
  way["highway"]({BBOX});
  way["building"]({BBOX});
  way["landuse"]({BBOX});
  way["natural"]({BBOX});
  way["waterway"]({BBOX});
  node["place"]({BBOX});
  node["railway"="station"]({BBOX});
  node["railway"="halt"]({BBOX});
  node["natural"="tree"]({BBOX});
);
out body;
>;
out skel qt;"""
r = requests.post("https://overpass-api.de/api/interpreter", data=Q.encode(),
                  headers={"Content-Type": "text/plain",
                           "User-Agent": "MapSimAda/0.1 (open-data terrain pipeline)"},
                  timeout=300)
r.raise_for_status()
(OUT/"valdorcia.osm.json").write_bytes(r.content)
print(f"wrote {len(r.content):,} bytes -> {OUT/'valdorcia.osm.json'}")

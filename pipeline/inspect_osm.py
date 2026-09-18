"""Inspect the Val d'Orcia OSM extract and pull out the rail corridor."""
import json, collections, pathlib, math

RAW = pathlib.Path.home()/".openclaw/work/MapSimAda/data/raw/osm/valdorcia.osm.json"
OUT = pathlib.Path.home()/".openclaw/work/MapSimAda/data/derived"
OUT.mkdir(parents=True, exist_ok=True)

doc = json.loads(RAW.read_text())
els = doc["elements"]
nodes = {e["id"]: e for e in els if e["type"] == "node"}
ways  = [e for e in els if e["type"] == "way"]
print(f"nodes={len(nodes):,}  ways={len(ways):,}")

def tally(key):
    c = collections.Counter()
    for w in ways:
        v = w.get("tags", {}).get(key)
        if v: c[v] += 1
    return c

for key, top in (("railway", 99), ("highway", 8), ("landuse", 8), ("natural", 5)):
    c = tally(key)
    if c:
        print(f"\n[{key}] {sum(c.values()):,} ways")
        for v, n in c.most_common(top):
            print(f"   {v:<22} {n:>6,}")

print(f"\n[building] {sum(1 for w in ways if 'building' in w.get('tags',{})):,} ways")

places = [e for e in els if e["type"]=="node" and e.get("tags",{}).get("place")]
print("\n[places]")
for p in sorted(places, key=lambda p: p["tags"].get("place","")):
    t=p["tags"]
    if t.get("place") in ("city","town","village","hamlet") and t.get("name"):
        print(f"   {t['place']:<10} {t['name']}")

stations = [e for e in els if e["type"]=="node" and e.get("tags",{}).get("railway") in ("station","halt")]
print(f"\n[rail stations/halts] {len(stations)}")
for s in stations:
    t=s["tags"]
    print(f"   {t.get('railway'):<8} {t.get('name','(unnamed)'):<34} {s['lat']:.5f},{s['lon']:.5f}")

# --- extract the rail corridor as GeoJSON ---
rail = [w for w in ways if w.get("tags",{}).get("railway") in
        ("rail","narrow_gauge","disused","abandoned")]
feats=[]
total_km=0.0
def haversine(a,b):
    R=6371.0088
    p1,p2=math.radians(a[1]),math.radians(b[1])
    dp=p2-p1; dl=math.radians(b[0]-a[0])
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
for w in rail:
    coords=[(nodes[n]["lon"], nodes[n]["lat"]) for n in w["nodes"] if n in nodes]
    if len(coords)<2: continue
    total_km+=sum(haversine(coords[i],coords[i+1]) for i in range(len(coords)-1))
    feats.append({"type":"Feature","properties":{k:v for k,v in w["tags"].items()
                  if k in ("railway","name","usage","gauge","electrified","ref")},
                  "geometry":{"type":"LineString","coordinates":coords}})
gj={"type":"FeatureCollection",
    "properties":{"source":"OpenStreetMap contributors","licence":"ODbL 1.0"},
    "features":feats}
(OUT/"rail_corridor.geojson").write_text(json.dumps(gj))
print(f"\n[rail corridor] {len(feats)} segments, {total_km:.1f} km -> data/derived/rail_corridor.geojson")

names=collections.Counter(f["properties"].get("name") for f in feats if f["properties"].get("name"))
for n,c in names.most_common(10):
    print(f"   {n}  ({c} segments)")

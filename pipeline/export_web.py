"""Export the slice into browser-ready assets: raw uint16 heightfield + a single
stitched rail polyline in local metric coordinates."""
import pathlib, json, struct
import numpy as np, rasterio
from pyproj import Transformer

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
DER, PUB = HOME/"data/derived", HOME/"web/public"
PUB.mkdir(parents=True, exist_ok=True)

with rasterio.open(DER/"valdorcia_dem_utm32n.tif") as src:
    z = src.read(1).astype(np.float32); T = src.transform
    W, H = src.width, src.height
    ox, oy = T.c, T.f                      # UTM of raster top-left
    px, py = T.a, abs(T.e)

z = np.where(z < -1000, np.nan, z)
zmin, zmax = float(np.nanmin(z)), float(np.nanmax(z))
z = np.nan_to_num(z, nan=zmin)

grid = ((z - zmin)/(zmax - zmin)*65535).astype('<u2')
(PUB/"terrain.bin").write_bytes(grid.tobytes())
print(f"terrain.bin  {W}x{H}  {grid.nbytes/1e6:.2f} MB  {zmin:.1f}-{zmax:.1f} m")

# ---- rail: stitch segments into one ordered polyline ----
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
rail = json.loads((DER/"rail_corridor.geojson").read_text())
segs = []
for f in rail["features"]:
    if f["properties"].get("railway") != "rail": continue
    pts = [to_utm.transform(lo, la) for lo, la in f["geometry"]["coordinates"]]
    if len(pts) > 1: segs.append(pts)
print(f"stitching {len(segs)} rail segments")

def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** .5
chain, segs = list(segs.pop(0)), segs
TOL = 60.0
changed = True
while changed and segs:
    changed = False
    for i, s in enumerate(segs):
        for cand, attach in ((s, "fwd"), (s[::-1], "rev")):
            if dist(chain[-1], cand[0]) < TOL:
                chain += cand[1:]; segs.pop(i); changed = True; break
            if dist(chain[0], cand[-1]) < TOL:
                chain = cand[:-1] + chain; segs.pop(i); changed = True; break
        if changed: break

def sample_h(x, y):
    c = int(round((x-ox)/px)); r = int(round((oy-y)/py))
    return float(z[min(max(r,0),H-1), min(max(c,0),W-1)])

path = [{"x": round(x-ox, 2), "y": round(oy-y, 2), "z": round(sample_h(x, y), 2)}
        for x, y in chain]
length = sum(dist((path[i]['x'],path[i]['y']), (path[i+1]['x'],path[i+1]['y']))
             for i in range(len(path)-1))
print(f"rail path: {len(path)} points, {length/1000:.2f} km continuous")

manifest = {
  "width": W, "height": H, "pxSize": round(px, 4),
  "spanX": round(W*px, 1), "spanY": round(H*py, 1),
  "zMin": round(zmin, 2), "zMax": round(zmax, 2),
  "railPath": path,
  "spawn": {"x": round(W*px*0.5, 1), "y": round(H*py*0.5, 1)},
  "attribution": [
    "Elevation: Copernicus WorldDEM-30 \u00a9 DLR e.V. 2010-2014 and \u00a9 Airbus "
    "Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA",
    "Rail & features: \u00a9 OpenStreetMap contributors, ODbL 1.0"
  ]
}
(PUB/"slice.json").write_text(json.dumps(manifest))
print(f"slice.json   {(PUB/'slice.json').stat().st_size/1024:.1f} KB")

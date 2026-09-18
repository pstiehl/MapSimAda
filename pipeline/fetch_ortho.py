"""Fetch Regione Toscana 20cm orthophotography for the slice via the GEOscopio OFC_RT
WMS, in the same UTM 32N frame as the terrain, and mosaic it into one ground texture.

Layer choice is a licence decision, not a quality one. The general OFC service
(map=wmsofc) is a mixed-vintage, mixed-ownership composite whose own abstract requires
displaying each data owner's disclaimer -- it does not clear the register's bar. This
service (map=owsofc_rt) serves imagery whose orthophoto rights belong to Regione
Toscana, under the regional CC-BY open-geodata policy, and reports
AccessConstraints: none / Fees: none.

Do not switch LAYER to an AGEA-sourced or false-colour variant without re-checking
docs/LICENSES.md first.
"""
import pathlib, io
import rasterio, requests
from PIL import Image

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
DER, PUB = HOME/"data/derived", HOME/"web/public"
PUB.mkdir(parents=True, exist_ok=True)

WMS   = "https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms"
MAP   = "owsofc_rt"
LAYER = "rt_ofc.5k24.32bit"      # OFC 2024/2025, 20cm GSD, rights: Regione Toscana
N, TILE = 4, 2048                # 4x4 -> 8192px over ~16.8 km ~= 2.05 m/px

with rasterio.open(DER/"valdorcia_dem_utm32n.tif") as s:
    b = s.bounds
print(f"terrain bounds UTM32N: {b.left:.0f},{b.bottom:.0f} -> {b.right:.0f},{b.top:.0f}", flush=True)

full = Image.new("RGB", (TILE*N, TILE*N))
dx, dy = (b.right-b.left)/N, (b.top-b.bottom)/N
sess = requests.Session()
sess.headers["User-Agent"] = "MapSimAda/0.1 (open-data terrain pipeline)"

for r in range(N):
    for c in range(N):
        left, right  = b.left + c*dx, b.left + (c+1)*dx
        bottom, top  = b.top - (r+1)*dy, b.top - r*dy
        p = {"map": MAP, "service": "WMS", "request": "GetMap", "version": "1.3.0",
             "layers": LAYER, "styles": "", "crs": "EPSG:32632",
             "bbox": f"{left},{bottom},{right},{top}",   # projected CRS -> E,N order
             "width": TILE, "height": TILE, "format": "image/jpeg"}
        resp = sess.get(WMS, params=p, timeout=240)
        resp.raise_for_status()
        if "image" not in resp.headers.get("Content-Type", ""):
            raise SystemExit(f"WMS error r{r}c{c}: {resp.text[:300]}")
        full.paste(Image.open(io.BytesIO(resp.content)).convert("RGB"), (c*TILE, r*TILE))
        print(f"  tile r{r}c{c}  {len(resp.content)/1024:.0f} KB", flush=True)

out = PUB/"ortho.jpg"
full.save(out, "JPEG", quality=84, optimize=True)
print(f"\northo.jpg  {full.size[0]}x{full.size[1]}  {out.stat().st_size/1e6:.2f} MB  "
      f"{(b.right-b.left)/(TILE*N):.2f} m/px", flush=True)
print("source: Regione Toscana - SIPT, Geoscopio WMS OFC_RT, layer " + LAYER, flush=True)
print("licence: CC-BY (regional open geodata); orthophoto rights Regione Toscana", flush=True)

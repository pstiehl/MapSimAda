"""Fetch Regione Toscana orthophotography (CC-BY) for the slice via GEOscopio WMS,
in the same UTM 32N frame as the terrain, and mosaic it into one ground texture."""
import pathlib, io, math
import rasterio, requests
from PIL import Image

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
DER, PUB = HOME/"data/derived", HOME/"web/public"
PUB.mkdir(parents=True, exist_ok=True)
WMS = "https://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms"

with rasterio.open(DER/"valdorcia_dem_utm32n.tif") as s:
    b = s.bounds
print(f"terrain bounds UTM32N: {b.left:.0f},{b.bottom:.0f} -> {b.right:.0f},{b.top:.0f}")

N, TILE = 2, 2048                      # 2x2 tiles of 2048px -> 4096px, ~4.1 m/px
full = Image.new("RGB", (TILE*N, TILE*N))
dx, dy = (b.right-b.left)/N, (b.top-b.bottom)/N

for r in range(N):
    for c in range(N):
        left, right = b.left + c*dx, b.left + (c+1)*dx
        top, bottom = b.top - r*dy, b.top - (r+1)*dy
        p = {"map": "wmsofc", "service": "WMS", "request": "GetMap", "version": "1.3.0",
             "layers": "rt_ofc", "styles": "", "crs": "EPSG:32632",
             "bbox": f"{bottom},{left},{top},{right}",     # 1.3.0 axis order for projected: E,N -> minx,miny,maxx,maxy
             "width": TILE, "height": TILE, "format": "image/jpeg"}
        p["bbox"] = f"{left},{bottom},{right},{top}"
        resp = requests.get(WMS, params=p, timeout=180,
                            headers={"User-Agent": "MapSimAda/0.1 (open-data terrain pipeline)"})
        resp.raise_for_status()
        if "image" not in resp.headers.get("Content-Type",""):
            raise SystemExit(f"WMS error r{r}c{c}: {resp.text[:300]}")
        im = Image.open(io.BytesIO(resp.content)).convert("RGB")
        full.paste(im, (c*TILE, r*TILE))
        print(f"  tile r{r}c{c}  {len(resp.content)/1024:.0f} KB")

out = PUB/"ortho.jpg"
full.save(out, "JPEG", quality=86, optimize=True)
mpp = (b.right-b.left)/(TILE*N)
print(f"\northo.jpg  {full.size[0]}x{full.size[1]}  {out.stat().st_size/1e6:.2f} MB  {mpp:.2f} m/px")
print("licence: CC-BY, Regione Toscana - SIPT (Geoscopio WMS OFC)")

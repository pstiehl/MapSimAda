"""Hillshade preview of the slice with the rail corridor and settlements overlaid."""
import pathlib, json, math
import numpy as np, rasterio
from pyproj import Transformer
from PIL import Image, ImageDraw

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
DER  = HOME/"data/derived"

with rasterio.open(DER/"valdorcia_dem_utm32n.tif") as src:
    z = src.read(1).astype(np.float32); T = src.transform; W,H = src.width, src.height

# hillshade, sun from the northwest
az, alt = math.radians(315.0), math.radians(45.0)
dy, dx = np.gradient(z, abs(T.e), T.a)
slope  = np.arctan(np.hypot(dx, dy))
aspect = np.arctan2(-dx, dy)
hs = (np.sin(alt)*np.cos(slope) + np.cos(alt)*np.sin(slope)*np.cos(az-aspect))
hs = np.clip(hs, 0, 1)

# tint by elevation: valley green -> ridge warm stone
zn = np.clip((z - z.min())/(z.max()-z.min()), 0, 1)
low  = np.array([ 92, 112,  64], np.float32)
high = np.array([206, 188, 150], np.float32)
rgb  = (low + (high-low)*zn[...,None]) * (0.35 + 0.65*hs[...,None])
img  = Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).resize((W*2,H*2), Image.LANCZOS)
d    = ImageDraw.Draw(img)

to_utm = Transformer.from_crs("EPSG:4326","EPSG:32632",always_xy=True)
inv = ~T
def px(lon,lat):
    x,y = to_utm.transform(lon,lat); c,r = inv*(x,y); return (c*2, r*2)

rail = json.loads((DER/"rail_corridor.geojson").read_text())
for f in rail["features"]:
    pts=[px(*c) for c in f["geometry"]["coordinates"]]
    if len(pts)>1:
        d.line(pts, fill=(30,30,34), width=7)
        d.line(pts, fill=(236,196,72) if f["properties"].get("railway")=="rail"
                       else (150,150,150), width=3)

for name,lon,lat in [("Pienza",11.6786,43.0779),("San Quirico d'Orcia",11.6053,43.0597),
                     ("Montalcino",11.4894,43.0567),("Bagno Vignoni",11.6183,43.0300),
                     ("Castiglione d'Orcia",11.6156,43.0011),("Torrenieri",11.5522,43.0867)]:
    x,y = px(lon,lat)
    if 0<=x<W*2 and 0<=y<H*2:
        d.ellipse([x-6,y-6,x+6,y+6], fill=(250,250,250), outline=(20,20,20), width=2)
        d.text((x+11,y-7), name, fill=(255,255,255), stroke_width=3, stroke_fill=(0,0,0))

d.text((14,14), "Val d'Orcia — MapSimAda v0   16.8 x 16.1 km   0-664 m",
       fill=(255,255,255), stroke_width=3, stroke_fill=(0,0,0))
d.text((14,H*2-30), "Elevation: Copernicus GLO-30 (ESA/EU)   Rail: (c) OpenStreetMap contributors, ODbL",
       fill=(235,235,235), stroke_width=3, stroke_fill=(0,0,0))

out = DER/"valdorcia_preview.png"
img.save(out); print("wrote", out, img.size)

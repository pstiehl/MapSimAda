"""Crop + merge Copernicus GLO-30 to the Val d'Orcia slice, reproject to metric UTM 32N,
emit a 16-bit heightmap PNG plus metadata the renderer can consume.

Void handling: GLO-30 COGs ship with nodata=None, so voids arrive as literal 0.0 and
are indistinguishable from sea level to any naive reader. This slice is inland Tuscany
(true minimum ~138 m), so 0.0 is unambiguously invalid here and is masked before the
merge. Interior holes are then inpainted; remaining edge nodata -- including the wedges
the WGS84->UTM rotation leaves in the corners -- is cropped off rather than invented.
A coastal slice must revisit this rule: there, 0.0 is real.
"""
import pathlib, json
import numpy as np, rasterio
from rasterio.merge import merge
from rasterio.fill import fillnodata
from rasterio.warp import calculate_default_transform, reproject, Resampling

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
RAW, DER = HOME/"data/raw/dem", HOME/"data/derived"
DER.mkdir(parents=True, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 11.48, 42.98, 11.68, 43.12
DST_CRS = "EPSG:32632"          # UTM 32N - metres, correct for central Italy
INLAND_FLOOR = 1.0              # metres; below this is a void in THIS slice

paths = sorted(RAW.glob("*.tif"))
srcs = []
for p in paths:
    s = rasterio.open(p)
    print(f"  {p.name[:38]}  nodata={s.nodata}  zeros={(s.read(1)==0).sum():,}")
    srcs.append(s)

mosaic, transform = merge(srcs, bounds=(WEST, SOUTH, EAST, NORTH), nodata=np.nan)
band = mosaic[0].astype(np.float32)
voids_in = int((band < INLAND_FLOOR).sum() + np.isnan(band).sum())
band[band < INLAND_FLOOR] = np.nan
print(f"masked {voids_in:,} void cells in the WGS84 crop ({band.shape[1]}x{band.shape[0]})")

meta = srcs[0].meta.copy()
meta.update(height=band.shape[0], width=band.shape[1], transform=transform)

t, w, h = calculate_default_transform(meta["crs"], DST_CRS,
                                      meta["width"], meta["height"],
                                      WEST, SOUTH, EAST, NORTH)
dst = np.full((h, w), np.nan, dtype=np.float32)
reproject(source=band, destination=dst,
          src_transform=transform, src_crs=meta["crs"], src_nodata=np.nan,
          dst_transform=t, dst_crs=DST_CRS, dst_nodata=np.nan,
          resampling=Resampling.bilinear)

# inpaint interior holes from their own neighbourhood
mask = np.isfinite(dst)
print(f"after reprojection: {int((~mask).sum()):,} nodata cells of {dst.size:,}")
dst = fillnodata(dst, mask=mask.astype(np.uint8), max_search_distance=64, smoothing_iterations=2)

# crop away any edge nodata (rotation wedges) instead of fabricating terrain there
good = np.isfinite(dst)
rows, cols = np.where(good)
def tightest(arr):
    r0, r1, c0, c1 = 0, arr.shape[0], 0, arr.shape[1]
    while r0 < r1 and not np.isfinite(arr[r0, c0:c1]).all(): r0 += 1
    while r1 > r0 and not np.isfinite(arr[r1-1, c0:c1]).all(): r1 -= 1
    while c0 < c1 and not np.isfinite(arr[r0:r1, c0]).all(): c0 += 1
    while c1 > c0 and not np.isfinite(arr[r0:r1, c1-1]).all(): c1 -= 1
    return r0, r1, c0, c1
r0, r1, c0, c1 = tightest(dst)
dst = dst[r0:r1, c0:c1]
t = rasterio.transform.Affine(t.a, t.b, t.c + c0*t.a, t.d, t.e, t.f + r0*t.e)
h, w = dst.shape
print(f"cropped to fully-valid core: {w} x {h} px  (trimmed {r0}+{626-r1} rows, {c0}+{654-c1} cols)")

assert np.isfinite(dst).all(), "nodata survived the crop"
zmin, zmax = float(dst.min()), float(dst.max())
span_x, span_y = w*t.a, h*abs(t.e)
print(f"elevation  : {zmin:.1f} m -> {zmax:.1f} m   (was 0.0 before the void fix)")
print(f"ground span: {span_x/1000:.2f} km E-W x {span_y/1000:.2f} km N-S @ {t.a:.2f} m/px")

out_meta = meta.copy()
out_meta.update(crs=DST_CRS, transform=t, width=w, height=h, dtype="float32",
                count=1, nodata=None)
with rasterio.open(DER/"valdorcia_dem_utm32n.tif", "w", **out_meta) as f:
    f.write(dst, 1)

png = (np.clip((dst-zmin)/(zmax-zmin), 0, 1)*65535).astype(np.uint16)
with rasterio.open(DER/"valdorcia_heightmap_u16.png", "w", driver="PNG",
                   width=w, height=h, count=1, dtype="uint16") as f:
    f.write(png, 1)

(DER/"terrain_manifest.json").write_text(json.dumps({
  "name": "valdorcia_slice_v0",
  "crs": DST_CRS,
  "bbox_wgs84": [WEST, SOUTH, EAST, NORTH],
  "raster": {"width": w, "height": h, "metres_per_pixel": round(t.a, 4)},
  "ground_span_m": {"x": round(span_x,1), "y": round(span_y,1)},
  "elevation_m": {"min": round(zmin,2), "max": round(zmax,2)},
  "void_handling": {"rule": f"elevation < {INLAND_FLOOR} m treated as nodata (inland slice)",
                    "masked_cells": voids_in,
                    "method": "mask -> bilinear reproject with nan -> fillnodata inpaint -> crop to valid core",
                    "caveat": "invalid for coastal slices, where 0 m is real"},
  "heightmap": {"file": "valdorcia_heightmap_u16.png", "encoding": "uint16 linear",
                "decode": "elev_m = min + (v/65535)*(max-min)"},
  "source": {"dataset": "Copernicus DEM GLO-30",
             "attribution": "Produced using Copernicus WorldDEM-30 \u00a9 DLR e.V. 2010-2014 and "
                            "\u00a9 Airbus Defence and Space GmbH 2014-2018 provided under "
                            "COPERNICUS by the European Union and ESA; all rights reserved.",
             "upgrade_path": "Regione Toscana 1m LiDAR DTM/DSM (2019-2021)"}
}, indent=2))
print("\nwrote dem, heightmap, manifest")

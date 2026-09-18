"""Crop + merge Copernicus GLO-30 to the Val d'Orcia slice, reproject to metric UTM 32N,
emit a 16-bit heightmap PNG plus metadata the renderer can consume."""
import pathlib, json
import numpy as np, rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
RAW, DER = HOME/"data/raw/dem", HOME/"data/derived"
DER.mkdir(parents=True, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 11.48, 42.98, 11.68, 43.12
DST_CRS = "EPSG:32632"          # UTM 32N - metres, correct for central Italy

srcs = [rasterio.open(p) for p in sorted(RAW.glob("*.tif"))]
print(f"merging {len(srcs)} tiles: {[p.name[:34] for p in sorted(RAW.glob('*.tif'))]}")
mosaic, transform = merge(srcs, bounds=(WEST, SOUTH, EAST, NORTH))
meta = srcs[0].meta.copy()
meta.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform)
print(f"cropped WGS84 grid: {mosaic.shape[2]} x {mosaic.shape[1]} px")

t, w, h = calculate_default_transform(meta["crs"], DST_CRS,
                                      meta["width"], meta["height"],
                                      WEST, SOUTH, EAST, NORTH)
dst = np.zeros((h, w), dtype=np.float32)
reproject(source=mosaic[0], destination=dst,
          src_transform=transform, src_crs=meta["crs"],
          dst_transform=t, dst_crs=DST_CRS, resampling=Resampling.bilinear)

out_meta = meta.copy()
out_meta.update(crs=DST_CRS, transform=t, width=w, height=h, dtype="float32", count=1)
with rasterio.open(DER/"valdorcia_dem_utm32n.tif", "w", **out_meta) as f:
    f.write(dst, 1)

valid = dst[dst > -1000]
zmin, zmax = float(valid.min()), float(valid.max())
span_x, span_y = w * t.a, h * abs(t.e)
print(f"UTM grid   : {w} x {h} px  @ {t.a:.2f} m/px")
print(f"ground span: {span_x/1000:.2f} km E-W  x  {span_y/1000:.2f} km N-S")
print(f"elevation  : {zmin:.1f} m -> {zmax:.1f} m  (relief {zmax-zmin:.1f} m)")
print(f"mean       : {float(valid.mean()):.1f} m")

norm = np.clip((dst - zmin) / (zmax - zmin), 0, 1)
png = (norm * 65535).astype(np.uint16)
with rasterio.open(DER/"valdorcia_heightmap_u16.png", "w", driver="PNG",
                   width=w, height=h, count=1, dtype="uint16") as f:
    f.write(png, 1)

manifest = {
  "name": "valdorcia_slice_v0",
  "crs": DST_CRS,
  "bbox_wgs84": [WEST, SOUTH, EAST, NORTH],
  "raster": {"width": w, "height": h, "metres_per_pixel": round(t.a, 4)},
  "ground_span_m": {"x": round(span_x, 1), "y": round(span_y, 1)},
  "elevation_m": {"min": round(zmin, 2), "max": round(zmax, 2)},
  "heightmap": {"file": "valdorcia_heightmap_u16.png", "encoding": "uint16 linear",
                "decode": "elev_m = min + (v/65535)*(max-min)"},
  "source": {"dataset": "Copernicus DEM GLO-30",
             "attribution": "Produced using Copernicus WorldDEM-30 \u00a9 DLR e.V. 2010-2014 and "
                            "\u00a9 Airbus Defence and Space GmbH 2014-2018 provided under "
                            "COPERNICUS by the European Union and ESA; all rights reserved.",
             "upgrade_path": "Regione Toscana 1m LiDAR DTM/DSM (2019-2021)"}
}
(DER/"terrain_manifest.json").write_text(json.dumps(manifest, indent=2))
print("\nwrote: valdorcia_dem_utm32n.tif, valdorcia_heightmap_u16.png, terrain_manifest.json")

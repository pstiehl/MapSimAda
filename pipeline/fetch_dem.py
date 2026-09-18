"""Fetch Copernicus GLO-30 DEM tiles covering the slice. Free, full and open licence."""
import pathlib, requests
OUT = pathlib.Path(__file__).resolve().parents[1]/"data/raw/dem"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
for tile in ("N42_00_E011_00", "N43_00_E011_00"):
    name = f"Copernicus_DSM_COG_10_{tile}_DEM"
    dst = OUT/f"{name}.tif"
    if dst.exists():
        print(f"skip {name} (cached)"); continue
    r = requests.get(f"{BASE}/{name}/{name}.tif", timeout=300); r.raise_for_status()
    dst.write_bytes(r.content); print(f"wrote {len(r.content):,} bytes -> {dst.name}")

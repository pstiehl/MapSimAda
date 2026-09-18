# MapSimAda

A walkable, rideable simulation of real places, built entirely from open geospatial
data. First slice: the Val d'Orcia, Tuscany.

Offline-first. Multiplayer-capable later. No streamed third-party map dependency.

## Why not Google Maps

Offline play, shipping our own world, and MMO-scale concurrency are each prohibited
or economically untenable under the Map Tiles API terms. Open data supports all
three and we own the result. See `docs/LICENSES.md`.

## Current slice — Val d'Orcia (v0)

| | |
|---|---|
| Bounds | 11.48–11.68 E, 42.98–43.12 N (WGS84) |
| Projection | EPSG:32632 (UTM 32N) — metres, world units 1:1 |
| Ground span | 16.8 × 16.1 km |
| Elevation | 0 → 664 m |
| Settlements | Pienza, San Quirico d'Orcia, Montalcino, Bagno Vignoni, Castiglione d'Orcia, Torrenieri + hamlets |
| Rail | Asciano–Monte Antico heritage line, 22.8 km in-slice, Torrenieri-Montalcino station |
| Land cover | 862 vineyard parcels, 881 orchard/olive, 245 tree rows, 5,275 buildings |

## Pipeline

```bash
python3 -m venv --without-pip .venv && curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3 -
.venv/bin/pip install numpy rasterio shapely pyproj requests

.venv/bin/python3 pipeline/fetch_osm.py       # Overpass -> data/raw/osm/
.venv/bin/python3 pipeline/fetch_dem.py       # Copernicus GLO-30 -> data/raw/dem/
.venv/bin/python3 pipeline/inspect_osm.py     # feature tally + rail corridor
.venv/bin/python3 pipeline/build_terrain.py   # crop, reproject, heightmap + manifest
```

`data/raw/` is gitignored. The pipeline is the source of truth; the data is a cache.

## Roadmap

- **v0** terrain + rail corridor + walk/ride traversal ← *here*
- **v1** Regione Toscana 1 m LiDAR, orthophoto texturing, procedural vines/cypress
- **v2** streamed tiles + IndexedDB offline cache
- **v3** authoritative server, shared world

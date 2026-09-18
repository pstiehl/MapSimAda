# Data & Asset Licence Register — MapSimAda

Every external input must appear here **before** it enters the pipeline, with its
licence, its obligations, and whether it survives a *public* release. No exceptions.

Status legend: ✅ cleared · ⚠️ cleared with obligations · ⛔ excluded

---

## ⛔ Google Maps Platform — EXCLUDED BY DESIGN

Photorealistic 3D Tiles, Map Tiles API, Street View, Maps JS.

| Our requirement | Google's terms |
|---|---|
| Offline play | Prohibited. Map Tiles API policy forbids offline use. |
| Ship our own world | Prohibited. No caching, no geodata extraction, no derivative works. |
| MMO at scale | Streamed + billed per session; cost scales with concurrent players. |
| Own the assets | Never. Licence is revocable; region coverage can change. |

Not a cost decision — a *capability* decision. Every headline goal of this project
is something Google's licence forbids. **Do not import Google data into this repo,
including as "temporary" reference geometry.**

---

## ⚠️ OpenStreetMap — ODbL 1.0  *(the one real legal question)*

Source: Overpass API. Covers roads, rail, buildings, land use, watercourses, place names.

Required attribution: **© OpenStreetMap contributors**, visible in-game.

ODbL splits outputs in two, and the split decides our obligations:

- **Produced Work** — rendered frames, screenshots, the visual experience.
  Attribution only. No share-alike. *The game as players see it lives here.*
- **Derivative Database** — a modified/extracted database. If publicly distributed,
  must be released under ODbL.

The open question: our baked terrain/feature tiles carry OSM-derived geometry. If
they are queryable geometry, they plausibly read as a Derivative Database and
share-alike attaches. If they are meshes and textures, they read as a Produced Work.

**Mitigation adopted now (cheap while the codebase is young):**
1. OSM-derived geometry stays quarantined in `data/derived/osm/*`, never mixed with
   original art or game logic.
2. The build bakes geometry → meshes. Shipped client assets carry no queryable OSM
   database.
3. If share-alike is ever triggered, we publish *that quarantined directory* under
   ODbL. Game code, art, and netcode stay unaffected.

⚠️ **Confirm with counsel before public launch.** This is an engineering mitigation,
not a legal opinion. It is the single highest-consequence licence question in the
project, and it is much cheaper to architect for now than to retrofit.

---

## ✅ Copernicus DEM GLO-30 — free, full and open

30 m global elevation. Currently the terrain base.

Required attribution, verbatim:

> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence
> and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA;
> all rights reserved.

No share-alike. Safe to bake into shipped assets.

---

## ⚠️ Regione Toscana LiDAR + orthophotos — LICENCE TO VERIFY

1×1 m DTM/DSM (2019–2021 flights) and 2025 orthophotos. This is the quality upgrade
that makes Tuscany look like Tuscany — 1 m ground resolution beats most shipped games.

**Not yet cleared.** Italian regional open geodata is normally CC-BY 4.0 or IODL 2.0,
both of which would be fine, but the specific terms are unconfirmed. Do not bake into
shipped assets until the licence text is read and recorded here.

---

## ✅ Engine & libraries

| Component | Licence |
|---|---|
| three.js | MIT |
| rasterio / shapely / pyproj / numpy | BSD / MIT family |

---

## Rules of engagement

1. New data source → add a row here first, then write the fetch code.
2. Anything marked ⛔ or unverified never reaches `web/public/`.
3. `docs/ATTRIBUTION.md` is generated from this file and must be reachable from
   the game's main screen — not buried in a settings submenu.

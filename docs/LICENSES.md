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

## ✅ Regione Toscana orthophotography 2024/2025 — CC-BY — **IN USE**

20 cm GSD colour aerial imagery, full regional coverage. This is the ground texture.

- Service: `https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms?map=owsofc_rt`
- Layer: `rt_ofc.5k24.32bit` — *"OFC 2024/2025 (GSD 20cm) di proprietà di Regione Toscana"*
- Capabilities report `AccessConstraints: none`, `Fees: none`
- Policy: regional open geodata released CC-BY / CC-BY-SA (Atto di Indirizzo 2013)

Required attribution, rendered on-screen:

> Aerial imagery: Regione Toscana — SIPT, ortofoto 2024/2025 (20 cm), CC-BY

### ⛔ The layer next door that does NOT clear

The general orthophoto service (`map=wmsofc`, layer `rt_ofc`) is tempting and wrong.
It is a mixed-vintage, mixed-ownership composite, and its own service abstract states:

> *Per obblighi di licenza gli strati delle ortofoto sono visualizzabili solo in
> abbinamento ai disclaimer dei rispettivi proprietari del dato.*

Viewable only alongside each data owner's disclaimer — so blanket regional CC-BY does
not cover it. It was fetched once during development and deliberately discarded.
**Do not point `fetch_ortho.py` back at it.** The same caution applies to the
AGEA-sourced variants (`rt_ofc.5k25.*`), whose source photograms are AGEA property.

---

## ⚠️ Regione Toscana LiDAR 1 m DTM/DSM — LICENCE TO VERIFY

1×1 m DTM/DSM from the 2019–2021 flights. Still the biggest outstanding upgrade:
terrain is currently 25.6 m/px, which is the limiting factor on ground-level realism.

**Not yet cleared.** Regional policy points to CC-BY/CC-BY-SA, but part of the Tuscan
LiDAR holdings belong to the Ministero dell'Ambiente (PCN) rather than the Region, and
those carry different terms. Confirm ownership per sheet before use.

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

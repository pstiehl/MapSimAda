"""Export OSM buildings, vegetation parcels and tree rows into local metric coords
for the renderer. Data (c) OpenStreetMap contributors, ODbL 1.0."""
import pathlib, json
import numpy as np, rasterio
from pyproj import Transformer

HOME = pathlib.Path.home()/".openclaw/work/MapSimAda"
RAW, DER, PUB = HOME/"data/raw/osm", HOME/"data/derived", HOME/"web/public"

with rasterio.open(DER/"valdorcia_dem_utm32n.tif") as s:
    z = s.read(1); T = s.transform; W,H = s.width, s.height
    ox, oy, px, py = T.c, T.f, T.a, abs(T.e)
SPANX, SPANY = W*px, H*py

def h(x, y):
    c = int(round(x/px)); r = int(round(y/py))
    return float(z[min(max(r,0),H-1), min(max(c,0),W-1)])

doc = json.loads((RAW/"valdorcia.osm.json").read_text())
nodes = {e["id"]: e for e in doc["elements"] if e["type"]=="node"}
ways  = [e for e in doc["elements"] if e["type"]=="way"]
to_utm = Transformer.from_crs("EPSG:4326","EPSG:32632",always_xy=True)

def local(w):
    pts=[]
    for n in w["nodes"]:
        nd = nodes.get(n)
        if not nd: continue
        X,Y = to_utm.transform(nd["lon"], nd["lat"])
        lx, ly = X-ox, oy-Y
        if -400 <= lx <= SPANX+400 and -400 <= ly <= SPANY+400:
            pts.append((round(lx,1), round(ly,1)))
    return pts

def area(p):
    return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1]
                   for i in range(len(p))))/2

# ---- buildings: footprint centroid, area, rough orientation, height guess ----
builds=[]
for w in ways:
    t=w.get("tags",{})
    if "building" not in t: continue
    p=local(w)
    if len(p)<4: continue
    a=area(p)
    if a<12 or a>60000: continue
    cx=sum(q[0] for q in p)/len(p); cy=sum(q[1] for q in p)/len(p)
    lv=t.get("building:levels")
    try: levels=float(lv)
    except: levels = 2.0 if a>110 else 1.0
    # dominant edge angle -> so boxes align with the real footprint
    best=0; bl=0
    for i in range(len(p)-1):
        dx,dy=p[i+1][0]-p[i][0], p[i+1][1]-p[i][1]
        L=(dx*dx+dy*dy)**.5
        if L>bl: bl, best = L, np.arctan2(dy,dx)
    wd=max(4.0, min(bl, 40.0))
    builds.append({"x":round(cx,1),"y":round(cy,1),"z":round(h(cx,cy),1),
                   "w":round(wd,1),"d":round(max(4.0,min(a/max(wd,1),34.0)),1),
                   "hgt":round(levels*3.4+1.2,1),"rot":round(float(best),3),
                   "kind":("church" if t.get("building")in("church","chapel") else "house")})

# ---- vegetation parcels: scatter points inside polygons by class ----
DENSITY = {"vineyard":0.0016, "orchard":0.0011, "forest":0.0013, "wood":0.0013, "scrub":0.0006}
rng = np.random.default_rng(7)
veg = {k: [] for k in ("vine","olive","tree","bush")}
KIND = {"vineyard":"vine","orchard":"olive","forest":"tree","wood":"tree","scrub":"bush"}
for w in ways:
    t=w.get("tags",{})
    cls = t.get("landuse") or t.get("natural")
    if cls not in DENSITY: continue
    p=local(w)
    if len(p)<4: continue
    a=area(p)
    if a<200: continue
    xs=[q[0] for q in p]; ys=[q[1] for q in p]
    poly=np.array(p)
    n=int(min(a*DENSITY[cls], 900))
    if n<1: continue
    # rejection-sample inside the footprint
    cand=np.column_stack([rng.uniform(min(xs),max(xs),n*3), rng.uniform(min(ys),max(ys),n*3)])
    inside=[]
    px_,py_=poly[:,0],poly[:,1]
    for X,Y in cand:
        c=False; j=len(poly)-1
        for i in range(len(poly)):
            if ((py_[i]>Y)!=(py_[j]>Y)) and (X < (px_[j]-px_[i])*(Y-py_[i])/(py_[j]-py_[i]+1e-9)+px_[i]): c=not c
            j=i
        if c: inside.append((X,Y))
        if len(inside)>=n: break
    k=KIND[cls]
    for X,Y in inside:
        veg[k].append([round(X,1),round(Y,1),round(h(X,Y),1)])

# ---- tree rows: the cypress lines, sampled along the way ----
cypress=[]
for w in ways:
    if w.get("tags",{}).get("natural")!="tree_row": continue
    p=local(w)
    for i in range(len(p)-1):
        (x0,y0),(x1,y1)=p[i],p[i+1]
        L=((x1-x0)**2+(y1-y0)**2)**.5
        for s in np.arange(0, L, 7.0):
            X,Y = x0+(x1-x0)*s/L, y0+(y1-y0)*s/L
            cypress.append([round(X,1),round(Y,1),round(h(X,Y),1)])

out={"buildings":builds, "cypress":cypress,
     **{k:v for k,v in veg.items()}}
(PUB/"features.json").write_text(json.dumps(out,separators=(',',':')))
print(f"buildings {len(builds):,}   cypress {len(cypress):,}")
for k,v in veg.items(): print(f"{k:9} {len(v):,}")
print(f"features.json {(PUB/'features.json').stat().st_size/1e6:.2f} MB")

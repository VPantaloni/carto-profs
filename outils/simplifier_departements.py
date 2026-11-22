"""Contours des départements (france-geojson, Admin Express IGN, Licence ouverte) simplifiés pour Carto-profs."""
import json, sys
src, dst = sys.argv[1], sys.argv[2]
TOL = 0.007   # degrés (~600 m) : assez pour un trait de contour à l’échelle d’une académie
def dp(pts, tol):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0]-a[0], b[1]-a[1]; n2 = dx*dx+dy*dy
    dmax, imax = 0, 0
    for i in range(1, len(pts)-1):
        p = pts[i]
        if n2 == 0: d = ((p[0]-a[0])**2+(p[1]-a[1])**2)**.5
        else:
            t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/n2))
            d = ((p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2)**.5
        if d > dmax: dmax, imax = d, i
    if dmax <= tol: return [a, b]
    return dp(pts[:imax+1], tol)[:-1] + dp(pts[imax:], tol)
def anneau(r):
    s = dp(r, TOL)
    s = [[round(x, 4), round(y, 4)] for x, y in s]
    if s[0] != s[-1]: s.append(s[0])
    return s if len(s) >= 4 else None
d = json.load(open(src)); out = []
for f in d["features"]:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    np = []
    for poly in polys:
        rings = [anneau(r) for r in poly]
        if rings[0] is None: continue
        np.append([r for r in rings if r])
    out.append({"type": "Feature", "properties": {"code": f["properties"]["code"], "nom": f["properties"]["nom"]},
                "geometry": {"type": "MultiPolygon", "coordinates": np}})
res = {"type": "FeatureCollection", "attribution": "Contours : france-geojson (G. David), d’après Admin Express © IGN, Licence ouverte", "features": out}
json.dump(res, open(dst, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "départements")

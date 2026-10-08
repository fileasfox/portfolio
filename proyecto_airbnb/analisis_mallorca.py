"""
Alquiler vacacional en Mallorca · ¿Cuánto vale una vista al mar?
Datos: Inside Airbnb, Mallorca, extracción 23/06/2026 (CC BY 4.0).

Uso:
    python analisis_mallorca.py <carpeta_datos> [carpeta_salida]

Genera resultados.json (cifras del portafolio) y mapa.json (municipios en SVG).
Bloques: 1) calidad del dato  2) estructura del mercado  3) prima de precio por
atributo (regresión hedónica)  4) estacionalidad  5) municipios
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent
R = {}

l = pd.read_csv(src / "listings.csv.gz", low_memory=False, encoding="utf-8")
FECHA_EXTRACCION = pd.Timestamp(l["last_scraped"].max())

# ------------------------------------------------------------------ 1. Calidad del dato
l["precio"] = pd.to_numeric(l["price"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
lic = l["license"].fillna("").str.strip()
l["tiene_licencia"] = lic.str.contains(r"ETV|ETVPL|ETV60|TI|AT|registration", case=False, regex=True)
l["licencia_exenta"] = lic.str.contains("exempt", case=False)
p1, p99 = l["precio"].quantile([0.01, 0.99])

R["calidad"] = {
    "fecha_extraccion": str(FECHA_EXTRACCION.date()),
    "anuncios": int(len(l)),
    "columnas": int(l.shape[1]),
    "ids_duplicados": int(l["id"].duplicated().sum()),
    "sin_precio_pct": round(l["precio"].isna().mean() * 100, 1),
    "sin_precio_n": int(l["precio"].isna().sum()),
    "precio_p1_p99": [round(float(p1), 0), round(float(p99), 0)],
    "precio_max": round(float(l["precio"].max()), 0),
    "sin_licencia_visible_pct": round((~l["tiene_licencia"] & ~l["licencia_exenta"]).mean() * 100, 1),
    "sin_reseñas_pct": round((l["number_of_reviews"] == 0).mean() * 100, 1),
    # ¿faltan precios al azar o en anuncios inactivos? (sesgo de selección)
    "reseñas_ltm_mediana_con_precio": float(l.loc[l["precio"].notna(), "number_of_reviews_ltm"].median()),
    "reseñas_ltm_mediana_sin_precio": float(l.loc[l["precio"].isna(), "number_of_reviews_ltm"].median()),
}

# ------------------------------------------------------------------ 2. Estructura del mercado
R["mercado"] = {
    "tipo_alojamiento_pct": (l["room_type"].value_counts(normalize=True) * 100).round(1).to_dict(),
    "precio_mediano_noche": round(float(l["precio"].median()), 0),
    "capacidad_mediana": float(l["accommodates"].median()),
}
hosts = l.groupby("host_id").size()
tramo = pd.cut(l["calculated_host_listings_count"], [0, 1, 4, 19, 10**6], labels=["1", "2-4", "5-19", "20+"])
R["mercado"]["anuncios_por_tramo_anfitrion_pct"] = (tramo.value_counts(normalize=True, sort=False) * 100).round(1).to_dict()
R["mercado"]["anfitriones"] = int(len(hosts))
top = hosts.sort_values(ascending=False)
R["mercado"]["top10_anfitriones_pct_anuncios"] = round(top.head(10).sum() / len(l) * 100, 1)

rev = l["estimated_revenue_l365d"].dropna()
rev = rev[rev > 0].sort_values(ascending=False)
R["mercado"]["ingreso_estimado_mediano_anual"] = round(float(rev.median()), 0)
R["mercado"]["top10pct_anuncios_pct_ingresos"] = round(rev.head(int(len(rev) * 0.1)).sum() / rev.sum() * 100, 1)
R["mercado"]["ocupacion_estimada_mediana_noches"] = float(
    l.loc[l["estimated_occupancy_l365d"] > 0, "estimated_occupancy_l365d"].median())

# ------------------------------------------------------------------ 3. Prima de precio por atributo
# amenities es una lista JSON: se evalúa elemento a elemento, porque "pool table" o
# "pool view" no son piscinas y una búsqueda de texto libre los contaba como tales.
items = l["amenities"].fillna("[]").map(lambda s: [a.lower() for a in json.loads(s)])
ATRIBUTOS = {
    "Piscina": r"^(private |shared )?(outdoor |indoor )?pool\b(?! table| view)",
    "Vista al mar": r"^(sea|ocean|beach) views?\b",
    "Acceso a playa": r"beach access|beachfront|waterfront",
    "Aire acondicionado": r"air conditioning|central air",
    "Jacuzzi": r"hot tub|jacuzzi",
    "Parking gratuito": r"^free (parking|driveway|street parking)",
    "Barbacoa": r"bbq grill|barbecue",
    "Cargador VE": r"ev charger",
    "Gimnasio": r"\bgym\b",
}
for k, rx in ATRIBUTOS.items():
    pat = re.compile(rx)
    l[k] = items.map(lambda xs: any(pat.search(x) for x in xs)).astype(float)
R["calidad"]["pool_generico_n"] = int(items.map(lambda xs: "pool" in xs).sum())

m = l[(l["room_type"] == "Entire home/apt") & l["precio"].between(p1, p99)].copy()
m = m.dropna(subset=["accommodates", "bedrooms", "bathrooms"])
m["log_precio"] = np.log(m["precio"])
# El precio es una cotización para unas fechas concretas (jun–ene): hay que controlar la temporada.
m["mes_entrada"] = pd.to_datetime(m["price_quote_checkin_date"], errors="coerce").dt.to_period("M").astype(str)
pt = m["property_type"].str.lower()
m["tipo_propiedad"] = np.select(
    [pt.str.contains("villa|chalet|cottage|farm|finca|country"),
     pt.str.contains("rental unit|condo|serviced|loft|apartment")],
    ["Villa / finca", "Apartamento"], default="Casa / otros")
num = ["accommodates", "bedrooms", "bathrooms"]
attrs = list(ATRIBUTOS)
X = pd.concat([
    m[num],
    m[attrs],
    pd.get_dummies(m["neighbourhood_cleansed"], prefix="mun", drop_first=True, dtype=float),
    pd.get_dummies(m["tipo_propiedad"], prefix="tipo", drop_first=True, dtype=float),
    pd.get_dummies(m["mes_entrada"], prefix="mes", drop_first=True, dtype=float),
], axis=1)
X.insert(0, "const", 1.0)
Xv, yv = X.to_numpy(float), m["log_precio"].to_numpy(float)
beta, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
resid = yv - Xv @ beta
n, k = Xv.shape
sigma2 = resid @ resid / (n - k)
# errores estándar robustos (HC1) para no asumir varianza constante
XtX_inv = np.linalg.pinv(Xv.T @ Xv)
meat = (Xv * resid[:, None] ** 2).T @ Xv
se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv) * n / (n - k))
r2 = 1 - (resid @ resid) / ((yv - yv.mean()) @ (yv - yv.mean()))
coef = pd.DataFrame({"b": beta, "se": se}, index=X.columns)

prima = []
for a in attrs:
    b, s = coef.loc[a]
    prima.append({
        "atributo": a,
        "prima_pct": round((np.exp(b) - 1) * 100, 1),
        "ic95": [round((np.exp(b - 1.96 * s) - 1) * 100, 1), round((np.exp(b + 1.96 * s) - 1) * 100, 1)],
        "pct_anuncios": round(m[a].mean() * 100, 1),
        "mediana_con": round(float(m.loc[m[a] == 1, "precio"].median()), 0) if m[a].sum() else None,
        "mediana_sin": round(float(m.loc[m[a] == 0, "precio"].median()), 0),
    })
R["hedonico"] = {
    "muestra": int(n),
    "r2": round(float(r2), 3),
    "controles": "capacidad, dormitorios, baños, municipio, tipo de propiedad y mes de entrada",
    "prima_por_dormitorio_pct": round((np.exp(coef.loc["bedrooms", "b"]) - 1) * 100, 1),
    "atributos": sorted(prima, key=lambda d: -d["prima_pct"]),
}

# Coeficientes completos para el simulador de precio de la web.
# Al volver del logaritmo, exp(predicción) subestima la media: se corrige con el factor de Duan.
mun_vals = sorted(m["neighbourhood_cleansed"].unique())
R["simulador"] = {
    "const": float(coef.loc["const", "b"]),
    "smearing": round(float(np.mean(np.exp(resid))), 4),
    "num": {c: float(coef.loc[c, "b"]) for c in num},
    "num_rango": {c: [int(m[c].quantile(0.05)), int(m[c].quantile(0.95)), int(m[c].median())] for c in num},
    "atributos": {a: float(coef.loc[a, "b"]) for a in attrs},
    "municipio": {v: float(coef.loc[f"mun_{v}", "b"]) if f"mun_{v}" in coef.index else 0.0 for v in mun_vals},
    "municipio_n": {v: int((m["neighbourhood_cleansed"] == v).sum()) for v in mun_vals},
    "tipo": {v: float(coef.loc[f"tipo_{v}", "b"]) if f"tipo_{v}" in coef.index else 0.0
             for v in sorted(m["tipo_propiedad"].unique())},
    "mes": {v: float(coef.loc[f"mes_{v}", "b"]) if f"mes_{v}" in coef.index else 0.0
            for v in sorted(m["mes_entrada"].unique()) if v != "NaT"},
}

# Tabla compacta para la consola SQL del navegador (mismos nombres que la vista listings_limpio)
pg = l[["id", "host_id", "neighbourhood_cleansed", "room_type", "accommodates", "bedrooms", "bathrooms", "precio",
        "number_of_reviews", "number_of_reviews_ltm", "estimated_revenue_l365d", "estimated_occupancy_l365d",
        "calculated_host_listings_count", "Piscina", "Vista al mar", "Aire acondicionado"]].copy()
pg.columns = ["id", "host_id", "municipio", "room_type", "accommodates", "bedrooms", "bathrooms", "precio",
              "number_of_reviews", "number_of_reviews_ltm", "ingreso_12m", "noches_12m", "anuncios_anfitrion",
              "piscina", "vista_mar", "aire_acondicionado"]
# Identificadores seudonimizados: la consola no necesita los IDs reales de Airbnb
pg["id"] = np.arange(1, len(pg) + 1)
pg["host_id"] = pg["host_id"].map({h: i for i, h in enumerate(pg["host_id"].unique(), 1)})
for c in ["piscina", "vista_mar", "aire_acondicionado"]:
    pg[c] = pg[c].astype(int)
PLAYGROUND = {"listings_limpio": {"columnas": list(pg.columns),
                                  "filas": json.loads(pg.to_json(orient="values"))}}

# ------------------------------------------------------------------ 4. Estacionalidad
rv = pd.read_csv(src / "reviews.csv", parse_dates=["date"])
rm = rv.groupby([rv["date"].dt.year.rename("anio"), rv["date"].dt.month.rename("mes")]).size().reset_index(name="resenas")
PLAYGROUND["reviews_mes"] = {"columnas": list(rm.columns), "filas": rm.values.tolist()}
rv = rv[(rv["date"] >= "2023-01-01") & (rv["date"] < "2026-01-01")]
ym = rv.groupby([rv["date"].dt.year, rv["date"].dt.month]).size()
R["reseñas_por_mes"] = {int(y): [int(ym.get((y, mth), 0)) for mth in range(1, 13)] for y in (2023, 2024, 2025)}
tot = {y: sum(v) for y, v in R["reseñas_por_mes"].items()}
R["reseñas_crecimiento_pct"] = {"2024": round((tot[2024] / tot[2023] - 1) * 100, 1),
                                "2025": round((tot[2025] / tot[2024] - 1) * 100, 1)}
med = np.array(list(R["reseñas_por_mes"].values())).mean(axis=0)
R["estacionalidad_ratio_pico_valle"] = round(float(med.max() / med.min()), 1)
R["temporada_alta_pct_reseñas"] = round(float(med[4:9].sum() / med.sum() * 100), 1)  # may–sep

# Calendario: % de noches no disponibles (reservadas o bloqueadas) en los 12 meses completos siguientes
cal = pd.read_csv(src / "calendar.csv.gz", usecols=["listing_id", "date", "available"], parse_dates=["date"])
cal["mes"] = cal["date"].dt.to_period("M")
ini = FECHA_EXTRACCION.to_period("M")
cal = cal[(cal["mes"] >= ini) & (cal["mes"] < ini + 12)]
nd = cal.groupby("mes")["available"].apply(lambda s: (s == "f").mean() * 100).round(1)
R["calendario_no_disponible_pct"] = [{"mes": str(k), "pct": float(v)} for k, v in nd.items()]

# ------------------------------------------------------------------ 5. Municipios
g = l.groupby("neighbourhood_cleansed").agg(
    anuncios=("id", "size"),
    precio_mediano=("precio", "median"),
    ingreso_mediano=("estimated_revenue_l365d", lambda s: s[s > 0].median()),
    piscina_pct=("Piscina", "mean"),
)
g["piscina_pct"] = (g["piscina_pct"] * 100).round(1)
g = g.round(0)
R["municipios_top_anuncios"] = [{"municipio": k, **{c: (None if pd.isna(v[c]) else float(v[c])) for c in g.columns}}
                                for k, v in g.sort_values("anuncios", ascending=False).head(12).iterrows()]
R["municipios_n"] = int(len(g))

# Mapa simplificado: proyección equirectangular corregida por latitud
geo = json.loads((src / "neighbourhoods.geojson").read_text(encoding="utf-8"))
lat0 = np.deg2rad(39.6)
pts = []
for f in geo["features"]:
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for ring in poly:
            pts.extend(ring)
pts = np.array(pts)
minx, maxx = pts[:, 0].min() * np.cos(lat0), pts[:, 0].max() * np.cos(lat0)
miny, maxy = pts[:, 1].min(), pts[:, 1].max()
W = 600
S = W / (maxx - minx)
H = round((maxy - miny) * S)
mapa = {"w": W, "h": H, "municipios": []}
for f in geo["features"]:
    nombre = f["properties"]["neighbourhood"]
    geom = f["geometry"]
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    d = []
    for poly in polys:
        ring = np.array(poly[0])
        step = max(1, len(ring) // 120)
        ring = ring[::step]
        xy = [((x * np.cos(lat0) - minx) * S, (maxy - y) * S) for x, y in ring]
        d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in xy) + "Z")
    fila = g.loc[nombre] if nombre in g.index else None
    mapa["municipios"].append({
        "nombre": nombre, "d": "".join(d),
        "anuncios": None if fila is None else int(fila["anuncios"]),
        "precio_mediano": None if fila is None or pd.isna(fila["precio_mediano"]) else float(fila["precio_mediano"]),
    })

(out / "playground.json").write_text(json.dumps(PLAYGROUND, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(out / "resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
(out / "mapa.json").write_text(json.dumps(mapa, ensure_ascii=False), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False, indent=2))

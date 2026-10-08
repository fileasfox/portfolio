"""
Datos del dashboard de mercado (Mallorca, Inside Airbnb).

Uso:
    python dashboard.py <carpeta_datos> [carpeta_salida]

Genera dashboard.json con dos piezas:
  - anuncios: una fila por anuncio, en columnas compactas, para calcular medianas en el navegador
    (las medianas no se pueden sumar: hay que tener las filas).
  - cubos: noches y reseñas por municipio x tramo de anfitrión x capacidad x mes, guardando
    numerador y denominador. Así cualquier combinación de filtros da la ocupación correcta
    (suma de noches no disponibles / suma de noches), nunca una media de porcentajes.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent

TRAMOS = ["1", "2-4", "5-19", "20+"]
CAPACIDAD = ["1-2", "3-4", "5-6", "7+"]

l = (pd.read_csv(src / "listings.csv.gz", low_memory=False,
                 usecols=["id", "neighbourhood_cleansed", "calculated_host_listings_count", "accommodates", "price",
                          "estimated_revenue_l365d", "number_of_reviews_ltm", "review_scores_rating", "last_scraped"])
     .rename(columns={"neighbourhood_cleansed": "municipio"})
     .assign(precio=lambda d: pd.to_numeric(d["price"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"),
             tramo=lambda d: pd.cut(d["calculated_host_listings_count"], [0, 1, 4, 19, 10**6], labels=TRAMOS),
             capacidad=lambda d: pd.cut(d["accommodates"], [0, 2, 4, 6, 10**3], labels=CAPACIDAD))
     .dropna(subset=["tramo", "capacidad"]))
FECHA = pd.Timestamp(l["last_scraped"].max())
MUNICIPIOS = sorted(l["municipio"].unique())
codigo = {m: i for i, m in enumerate(MUNICIPIOS)}

# Clave del cubo: índices de municipio, tramo y capacidad
l["clave"] = (l["municipio"].map(codigo).astype(str) + "|" + l["tramo"].cat.codes.astype(str)
              + "|" + l["capacidad"].cat.codes.astype(str))
dimension = l.set_index("id")["clave"]


def entero(s: pd.Series) -> list:
    return [None if pd.isna(v) else int(round(v)) for v in s]


anuncios = {
    "m": l["municipio"].map(codigo).tolist(),
    "t": l["tramo"].cat.codes.tolist(),
    "c": l["capacidad"].cat.codes.tolist(),
    "p": entero(l["precio"]),
    "i": entero(l["estimated_revenue_l365d"].where(l["estimated_revenue_l365d"] > 0)),
    "r": entero(l["number_of_reviews_ltm"]),
    "s": [None if pd.isna(v) else round(float(v), 2) for v in l["review_scores_rating"]],
}

# Calendario: 12 meses completos desde la extracción
ini = FECHA.to_period("M")
meses_cal = pd.period_range(ini, periods=12, freq="M")
cal = pd.read_csv(src / "calendar.csv.gz", usecols=["listing_id", "date", "available"], parse_dates=["date"])
cal = cal.assign(mes=cal["date"].dt.to_period("M"), no_disp=cal["available"].eq("f"))
cal = cal[cal["mes"].isin(meses_cal)]
cal["clave"] = cal["listing_id"].map(dimension)
huerfanos = int(cal["clave"].isna().sum())   # noches de anuncios que no están en listings
cal_cubo = (cal.dropna(subset=["clave"])
            .groupby(["clave", "mes"]).agg(no_disp=("no_disp", "sum"), noches=("no_disp", "size"))
            .unstack("mes", fill_value=0))

# Reseñas: 24 meses completos anteriores a la extracción (demanda pasada)
meses_rev = pd.period_range(ini - 24, periods=24, freq="M")
rv = pd.read_csv(src / "reviews.csv", usecols=["listing_id", "date"], parse_dates=["date"])
rv = rv.assign(mes=rv["date"].dt.to_period("M"), clave=rv["listing_id"].map(dimension))
rv = rv[rv["mes"].isin(meses_rev)].dropna(subset=["clave"])
rev_cubo = rv.groupby(["clave", "mes"]).size().unstack("mes", fill_value=0).reindex(columns=meses_rev, fill_value=0)

cubos = {}
for clave in dimension.unique():
    nd = cal_cubo["no_disp"].reindex(columns=meses_cal, fill_value=0).loc[clave].tolist() if clave in cal_cubo.index else [0] * 12
    no = cal_cubo["noches"].reindex(columns=meses_cal, fill_value=0).loc[clave].tolist() if clave in cal_cubo.index else [0] * 12
    rr = rev_cubo.loc[clave].tolist() if clave in rev_cubo.index else [0] * 24
    cubos[clave] = [list(map(int, nd)), list(map(int, no)), list(map(int, rr))]

# Cuadre: el total del cubo debe coincidir con el cálculo directo sobre el calendario
directo = cal.dropna(subset=["clave"])["no_disp"].mean() * 100
cubo = sum(sum(v[0]) for v in cubos.values()) / sum(sum(v[1]) for v in cubos.values()) * 100
assert abs(directo - cubo) < 1e-9, (directo, cubo)
assert len(anuncios["m"]) == len(l)

D = {
    "fecha": str(FECHA.date()),
    "municipios": MUNICIPIOS, "tramos": TRAMOS, "capacidad": CAPACIDAD,
    "meses_cal": [str(m) for m in meses_cal], "meses_rev": [str(m) for m in meses_rev],
    "anuncios": anuncios, "cubos": cubos,
    "control": {"anuncios": int(len(l)), "ocupacion_pct": round(cubo, 2), "noches_huerfanas": huerfanos,
                "reseñas_24m": int(rev_cubo.to_numpy().sum())},
}
(out / "dashboard.json").write_text(json.dumps(D, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(json.dumps(D["control"], ensure_ascii=False), f"{(out / 'dashboard.json').stat().st_size // 1024} KB")

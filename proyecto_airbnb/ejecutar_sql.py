"""
Carga los ficheros crudos en SQLite, ejecuta las consultas de sql/ y cuadra
los resultados con pandas antes de darlos por buenos.

Uso:
    python ejecutar_sql.py <carpeta_datos> [carpeta_salida]

Salida: sql_resultados.json (consulta, columnas, filas, tiempo y cuadres)
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent
db = out / "mallorca.db"
db.unlink(missing_ok=True)
con = sqlite3.connect(db)

# ------------------------------------------------------------------ Carga (tablas crudas)
COLS = ["id", "host_id", "neighbourhood_cleansed", "room_type", "property_type", "accommodates",
        "bedrooms", "bathrooms", "price", "number_of_reviews", "number_of_reviews_ltm",
        "estimated_revenue_l365d", "estimated_occupancy_l365d", "calculated_host_listings_count"]
listings = pd.read_csv(src / "listings.csv.gz", usecols=COLS, low_memory=False)
reviews = pd.read_csv(src / "reviews.csv")
calendar = pd.read_csv(src / "calendar.csv.gz", usecols=["listing_id", "date", "available"])

carga = {}
for nombre, df in [("listings", listings), ("reviews", reviews), ("calendar", calendar)]:
    t = time.perf_counter()
    df.to_sql(nombre, con, index=False, chunksize=100_000)
    carga[nombre] = {"filas": int(len(df)), "segundos": round(time.perf_counter() - t, 1)}
con.execute("CREATE INDEX ix_cal_date ON calendar(date)")
con.execute("CREATE INDEX ix_rev_date ON reviews(date)")

# ------------------------------------------------------------------ Consultas
resultados = []
for f in sorted((Path(__file__).parent / "sql").glob("*.sql")):
    sql = f.read_text(encoding="utf-8")
    t = time.perf_counter()
    cur = con.executescript(sql) if "CREATE VIEW" in sql else con.execute(sql)
    filas, columnas = [], []
    if cur.description:
        columnas = [d[0] for d in cur.description]
        filas = cur.fetchall()
    resultados.append({
        "fichero": f.name,
        "sql": sql.strip(),
        "columnas": columnas,
        "filas": [list(r) for r in filas],
        "ms": round((time.perf_counter() - t) * 1000),
    })

# ------------------------------------------------------------------ Cuadre SQL vs pandas
def q(sql):
    return pd.read_sql_query(sql, con)

listings["precio"] = pd.to_numeric(listings["price"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
cuadres = []

sql_med = next(r for r in resultados if r["fichero"].startswith("04"))
med_sql = pd.DataFrame(sql_med["filas"], columns=sql_med["columnas"]).set_index("municipio")["precio_mediano"]
# Se compara sin redondear a entero: al hacerlo, pandas (redondeo al par) y SQLite
# (redondeo hacia arriba) discrepan en medianas acabadas en ,5 (p. ej. 328,5 €).
med_pd = listings.groupby("neighbourhood_cleansed")["precio"].median().dropna()
comunes = med_sql.index.intersection(med_pd.index)
iguales = int(((med_sql[comunes] - med_pd[comunes]).abs() <= 0.0051).sum())  # SQL redondea a 2 decimales: tolerancia de medio céntimo
cuadres.append({"control": "Precio mediano por municipio (SQL con ventanas vs pandas .median())",
                "sql": f"{iguales} de {len(med_sql)} municipios", "pandas": f"{len(med_pd)} municipios",
                "ok": bool(iguales == len(med_sql) == len(med_pd)),
                "nota": "Con redondeo a entero salían 52 de 53: Lloret de Vistalegre (328,5 €) → 328 en pandas y 329 en SQLite."})

perf = next(r for r in resultados if r["fichero"].startswith("02"))
sin_precio_sql = perf["filas"][0][perf["columnas"].index("sin_precio")]
cuadres.append({"control": "Anuncios sin precio", "sql": sin_precio_sql,
                "pandas": int(listings["precio"].isna().sum()),
                "ok": bool(sin_precio_sql == int(listings["precio"].isna().sum()))})

rv = pd.to_datetime(reviews["date"])
n_sql = q("SELECT COUNT(*) n FROM reviews WHERE date >= '2023-01-01' AND date < '2026-01-01'")["n"][0]
n_pd = int(((rv >= "2023-01-01") & (rv < "2026-01-01")).sum())
cuadres.append({"control": "Reseñas 2023–2025", "sql": int(n_sql), "pandas": n_pd, "ok": bool(int(n_sql) == n_pd)})

anf = next(r for r in resultados if r["fichero"].startswith("06"))
pct20_sql = [r for r in anf["filas"] if r[0] == "20+"][0][3]
pct20_pd = round((listings["calculated_host_listings_count"] >= 20).mean() * 100, 1)
cuadres.append({"control": "% de anuncios de anfitriones con 20+", "sql": pct20_sql, "pandas": pct20_pd,
                "ok": bool(pct20_sql == pct20_pd)})

R = {"motor": f"SQLite {sqlite3.sqlite_version}", "carga": carga, "consultas": resultados, "cuadres": cuadres}
(out / "sql_resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
con.close()
for r in resultados:
    print(f"\n== {r['fichero']} ({r['ms']} ms)")
    print(r["columnas"])
    for fila in r["filas"][:13]:
        print(fila)
print("\nCarga:", carga)
print("Cuadres:", json.dumps(cuadres, ensure_ascii=False, indent=1))

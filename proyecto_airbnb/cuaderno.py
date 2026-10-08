"""
Cuaderno de pandas: ejecuta cada celda de verdad y guarda código + salida.

Uso:
    python cuaderno.py <carpeta_datos> [carpeta_salida]

Salidas:
    cuaderno.json   celdas para la web (código, salida en tabla o texto, explicación)
    cuaderno.ipynb  el mismo cuaderno con sus salidas, legible directamente en GitHub
"""
import ast
import contextlib
import io
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent

# (título, qué demuestra, código). Las celdas comparten variables, como en Jupyter.
CELDAS = [
("Cargar solo lo necesario y con el tipo correcto",
 "Leer 12 de 90 columnas y pasar los textos repetidos a category reduce la memoria. En tablas grandes es la diferencia entre que el proceso quepa o no.",
 '''import numpy as np
import pandas as pd

COLS = ["id", "host_id", "neighbourhood_cleansed", "room_type", "accommodates", "bedrooms",
        "bathrooms", "price", "number_of_reviews_ltm", "estimated_revenue_l365d",
        "review_scores_rating", "calculated_host_listings_count"]

completo = pd.read_csv(DATOS / "listings.csv.gz", low_memory=False)
l = pd.read_csv(DATOS / "listings.csv.gz", usecols=COLS)
l_cat = l.astype({"neighbourhood_cleansed": "category", "room_type": "category"})

mb = lambda d: d.memory_usage(deep=True).sum() / 2**20
pd.DataFrame({"columnas": [completo.shape[1], l.shape[1], l_cat.shape[1]],
              "memoria_MB": [mb(completo), mb(l), mb(l_cat)]},
             index=["fichero completo", "12 columnas", "12 columnas + category"]).round(1)'''),

("Perfil de calidad antes de calcular nada",
 "Una función reutilizable que dice, por columna, el tipo, cuántos nulos hay y cuántos valores distintos. Aquí aparece que una cuarta parte de los anuncios no publica precio.",
 '''def perfil(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "tipo": df.dtypes.astype(str),
        "nulos_pct": df.isna().mean().mul(100).round(1),
        "distintos": df.nunique(),
        "ejemplo": df.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else None),
    }).sort_values("nulos_pct", ascending=False)

print(f"{len(l)} filas · {l['id'].duplicated().sum()} ids duplicados · {l.shape[1]} columnas")
perfil(l).head(6)'''),

("Limpieza encadenada y con controles",
 "Method chaining con assign y pipe: cada paso se lee de arriba abajo y no deja variables intermedias. Los assert paran el proceso si algo no tiene sentido.",
 '''def recortar(df, col, q=(0.01, 0.99)):
    lo, hi = df[col].quantile(list(q))
    return df.assign(**{f"{col}_atipico": ~df[col].between(lo, hi) & df[col].notna()})

limpio = (l
    .rename(columns={"neighbourhood_cleansed": "municipio"})
    .assign(
        precio=lambda d: pd.to_numeric(d["price"].str.replace(r"[$,]", "", regex=True), errors="coerce"),
        tramo=lambda d: pd.cut(d["calculated_host_listings_count"], [0, 1, 4, 19, np.inf],
                               labels=["1", "2-4", "5-19", "20+"]),
        ingreso=lambda d: d["estimated_revenue_l365d"].where(d["estimated_revenue_l365d"] > 0),
    )
    .pipe(recortar, "precio")
    .drop(columns=["price", "estimated_revenue_l365d"]))

assert limpio["id"].is_unique
assert limpio["precio"].dropna().gt(0).all()
limpio[["municipio", "accommodates", "precio", "precio_atipico", "tramo", "ingreso"]].head(5)'''),

("Agregar con nombre: un resumen por municipio",
 "groupby con agregaciones con nombre: el resultado sale con columnas legibles y listo para un informe. Las medianas, y no las medias, porque el precio tiene una cola larga.",
 '''resumen = (limpio
    .groupby("municipio", observed=True)
    .agg(anuncios=("id", "size"),
         precio_mediano=("precio", "median"),
         ingreso_mediano=("ingreso", "median"),
         valoracion=("review_scores_rating", "mean"),
         pct_profesional=("tramo", lambda s: s.isin(["5-19", "20+"]).mean() * 100))
    .sort_values("anuncios", ascending=False))

resumen.head(8).round({"precio_mediano": 0, "ingreso_mediano": 0, "valoracion": 2, "pct_profesional": 1})'''),

("Tabla dinámica con totales",
 "pivot_table cruza dos dimensiones como una tabla dinámica de Excel, con la fila y la columna de total (margins).",
 '''capacidad = pd.cut(limpio["accommodates"], [0, 2, 4, 6, np.inf], labels=["1-2", "3-4", "5-6", "7+"])
top5 = resumen.index[:5]

(limpio.assign(capacidad=capacidad)
    .query("municipio in @top5")
    .pivot_table(index="municipio", columns="capacidad", values="precio",
                 aggfunc="median", margins=True, margins_name="Total", observed=True)
    .round(0))'''),

("Cruzar tablas sin perder filas por el camino",
 "Un merge con validate (si la relación no es la esperada, falla) e indicator, que permite encontrar los huérfanos: noches del calendario de anuncios que ya no están en el listado.",
 '''cal = pd.read_csv(DATOS / "calendar.csv.gz", usecols=["listing_id", "date", "available"],
                  parse_dates=["date"])

cruce = cal.merge(limpio[["id", "municipio"]], left_on="listing_id", right_on="id",
                  how="left", validate="many_to_one", indicator=True)

(cruce.groupby("_merge", observed=True)
    .agg(noches=("listing_id", "size"), anuncios=("listing_id", "nunique")))'''),

("Un promedio de promedios no es el total",
 "El error más habitual en un dashboard: promediar los porcentajes o las medianas de cada municipio. Así un pueblo con 10 anuncios pesa lo mismo que uno con 2.000. El dato de Mallorca se calcula sobre los anuncios, no sobre los municipios.",
 '''profesional = limpio["tramo"].isin(["5-19", "20+"])

pd.DataFrame({
    "media_de_municipios": [resumen["pct_profesional"].mean(), resumen["precio_mediano"].mean()],
    "calculo_correcto": [profesional.mean() * 100, limpio["precio"].median()],
}, index=["% anuncios de anfitriones con 5+", "precio mediano por noche (€)"]).assign(
    diferencia=lambda d: d["media_de_municipios"] - d["calculo_correcto"]).round(1)'''),

("Series temporales: mes, media móvil e interanual",
 "resample agrupa por mes, rolling suaviza la estacionalidad y pct_change(12) compara cada mes con el mismo mes del año anterior, que es la comparación justa en turismo.",
 '''rv = pd.read_csv(DATOS / "reviews.csv", usecols=["date"], parse_dates=["date"])

mensual = (rv.set_index("date").resample("MS").size().rename("reseñas")
    .loc["2023-01":"2025-12"].to_frame()
    .rename(index=lambda d: d.strftime("%Y-%m"))
    .assign(media_movil_12m=lambda d: d["reseñas"].rolling(12).mean(),
            interanual_pct=lambda d: d["reseñas"].pct_change(12) * 100))

mensual.tail(6).round(1)'''),

("Concentración: ¿cuánto ingreso hace el 10 % de arriba?",
 "qcut parte en deciles y transform calcula el peso de cada anuncio dentro de su municipio sin perder filas. Es la base de un análisis de Pareto.",
 '''con_ingreso = limpio.dropna(subset=["ingreso"]).copy()
con_ingreso["decil"] = pd.qcut(con_ingreso["ingreso"].rank(method="first", ascending=False),
                               10, labels=[f"D{i}" for i in range(1, 11)])
con_ingreso["peso_en_municipio"] = (con_ingreso["ingreso"]
    / con_ingreso.groupby("municipio", observed=True)["ingreso"].transform("sum"))

(con_ingreso.groupby("decil", observed=True)["ingreso"].sum()
    .div(con_ingreso["ingreso"].sum()).mul(100)
    .to_frame("pct_del_ingreso")
    .assign(acumulado=lambda d: d["pct_del_ingreso"].cumsum())
    .head(4).round(1))'''),

("Vectorizar donde importa, y medirlo",
 "Clasificar cada anuncio en un segmento recorriendo filas con apply(axis=1) frente a hacerlo por columnas con np.select. Mismo resultado, comprobado con assert. Ojo: con textos, apply puede ser igual de rápido; por eso mido antes de optimizar.",
 '''import time

base = limpio.dropna(subset=["precio"])

def fila_a_fila(d):
    def segmento(f):
        if f["precio"] >= 600 and f["accommodates"] >= 7:
            return "lujo grupos"
        if f["precio"] >= 600:
            return "lujo"
        if f["accommodates"] >= 7:
            return "grupos"
        return "estandar"
    return d.apply(segmento, axis=1)

def por_columnas(d):
    caro, grande = d["precio"].ge(600), d["accommodates"].ge(7)
    return pd.Series(np.select([caro & grande, caro, grande], ["lujo grupos", "lujo", "grupos"],
                               default="estandar"), index=d.index)

tiempos = {}
for nombre, f in [("apply(axis=1)", fila_a_fila), ("np.select", por_columnas)]:
    t0 = time.perf_counter()
    resultado = f(base)
    tiempos[nombre] = (time.perf_counter() - t0) * 1000

assert fila_a_fila(base).equals(por_columnas(base))
pd.Series(tiempos, name="milisegundos").to_frame().assign(
    veces_mas_lento=lambda d: d["milisegundos"] / d["milisegundos"].min()).round(1)'''),

("Cuadrar pandas contra SQL",
 "La misma métrica calculada por dos caminos debe dar lo mismo. sqlite3 viene con Python: cargo la tabla, repito el cálculo en SQL y comparo con assert_frame_equal.",
 '''import sqlite3

con = sqlite3.connect(":memory:")
limpio[["municipio", "precio", "ingreso"]].astype({"municipio": str}).to_sql("anuncios", con, index=False)

sql = pd.read_sql("""
    SELECT municipio, COUNT(*) AS anuncios, AVG(precio) AS precio_medio, SUM(ingreso) AS ingreso_total
    FROM anuncios GROUP BY municipio ORDER BY municipio
""", con).set_index("municipio")

pandas_ = (limpio.astype({"municipio": str}).groupby("municipio")
    .agg(anuncios=("id", "size"), precio_medio=("precio", "mean"), ingreso_total=("ingreso", "sum")))

pd.testing.assert_frame_equal(sql, pandas_, check_dtype=False)
print(f"Cuadre correcto en {len(sql)} municipios y 3 métricas")'''),
]


def ejecutar(codigo: str, ns: dict):
    """Ejecuta como una celda de Jupyter: devuelve lo impreso y el valor de la última expresión."""
    arbol = ast.parse(codigo)
    ultima = arbol.body.pop() if arbol.body and isinstance(arbol.body[-1], ast.Expr) else None
    buf = io.StringIO()
    t0 = time.perf_counter()
    with contextlib.redirect_stdout(buf):
        exec(compile(arbol, "<celda>", "exec"), ns)
        valor = eval(compile(ast.Expression(ultima.value), "<celda>", "eval"), ns) if ultima else None
    return buf.getvalue(), valor, time.perf_counter() - t0


def celda_web(v):
    if isinstance(v, pd.Series):
        v = v.to_frame()
    if isinstance(v, pd.DataFrame):
        def f(x):
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return "NaN"
            if isinstance(x, (bool, np.bool_)):
                return str(bool(x))
            if isinstance(x, (int, np.integer)):
                return f"{int(x):,}".replace(",", ".")
            if isinstance(x, (float, np.floating)):
                s = f"{x:,.2f}".rstrip("0").rstrip(".") if abs(x) < 1000 else f"{x:,.0f}"
                return s.replace(",", "_").replace(".", ",").replace("_", ".")
            return str(x)
        return {"index": [str(i) for i in v.index], "nombre_indice": v.index.name or "",
                "columnas": [str(c) for c in v.columns], "filas": [[f(x) for x in fila] for fila in v.itertuples(index=False)]}
    return None


import numpy as np   # noqa: E402  (también para el formateo de la web)

ns = {"DATOS": src, "__name__": "__cuaderno__"}
web, nb_celdas = [], []
for n, (titulo, explicacion, codigo) in enumerate(CELDAS, 1):
    impreso, valor, segundos = ejecutar(codigo, ns)
    web.append({"n": n, "titulo": titulo, "explicacion": explicacion, "codigo": codigo,
                "impreso": impreso.strip(), "tabla": celda_web(valor),
                "texto": None if valor is None or isinstance(valor, (pd.DataFrame, pd.Series)) else repr(valor),
                "segundos": round(segundos, 2)})
    salidas = []
    if impreso:
        salidas.append({"output_type": "stream", "name": "stdout", "text": impreso.splitlines(True)})
    if valor is not None:
        datos = {"text/plain": repr(valor).splitlines(True)}
        if isinstance(valor, (pd.DataFrame, pd.Series)):
            datos["text/html"] = (valor.to_frame() if isinstance(valor, pd.Series) else valor).to_html().splitlines(True)
        salidas.append({"output_type": "execute_result", "execution_count": n, "data": datos, "metadata": {}})
    nb_celdas += [{"cell_type": "markdown", "metadata": {}, "source": [f"## {n}. {titulo}\n", "\n", explicacion]},
                  {"cell_type": "code", "execution_count": n, "metadata": {},
                   "source": codigo.replace("DATOS /", "DATOS /").splitlines(True), "outputs": salidas}]
    print(f"{n:>2}. {titulo}  ({segundos:.1f} s)")

intro = {"cell_type": "markdown", "metadata": {}, "source": [
    "# Cuaderno de pandas · alquiler vacacional en Mallorca\n", "\n",
    "Datos: Inside Airbnb, Mallorca (CC BY 4.0). Generado y ejecutado por `cuaderno.py`; "
    "las salidas son las de la última ejecución.\n"]}
preparar = {"cell_type": "code", "execution_count": 0, "metadata": {}, "outputs": [],
            "source": ["from pathlib import Path\n", "DATOS = Path(\"datos\")   # listings.csv.gz, calendar.csv.gz y reviews.csv de Inside Airbnb\n"]}
nb = {"cells": [intro, preparar] + nb_celdas, "nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python", "version": sys.version.split()[0]}}}

(out / "cuaderno.json").write_text(json.dumps({"pandas": pd.__version__, "numpy": np.__version__,
                                               "python": sys.version.split()[0], "celdas": web},
                                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(out / "cuaderno.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")

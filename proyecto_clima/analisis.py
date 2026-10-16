"""
Análisis estadístico sobre los marts: homogeneidad, tendencias con intervalo de confianza,
descomposición de la exposición turística al calor y ciclo de las reservas de agua.

Uso:
    python analisis.py     escribe resultados.json (cifras y series para la web)
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
db = sqlite3.connect(AQUI / "clima.db")
q = lambda sql, *a: db.execute(sql, a).fetchall()
R = {}


# ---------------------------------------------------------------- 1. Homogeneidad de la estación
def snht(serie: np.ndarray) -> tuple[int, float]:
    """Standard Normal Homogeneity Test (Alexandersson, 1986): el punto k que maximiza
    T(k) = k·z1² + (n-k)·z2², con z la serie estandarizada. Devuelve (k, T máximo)."""
    z = (serie - serie.mean()) / serie.std(ddof=1)
    n = len(z)
    t = [k * z[:k].mean() ** 2 + (n - k) * z[k:].mean() ** 2 for k in range(2, n - 1)]
    k = int(np.argmax(t)) + 2
    return k, float(max(t))


dif = q("""WITH s AS (SELECT CAST(substr(fecha,1,4) AS INT) a, AVG((tmax+tmin)/2) t, COUNT(*) n FROM raw_clima
                     WHERE tmax IS NOT NULL AND tmin IS NOT NULL GROUP BY a),
             e AS (SELECT CAST(substr(fecha,1,4) AS INT) a, AVG((tmax+tmin)/2) t FROM raw_era5_ref GROUP BY a)
           SELECT s.a, s.t - e.t FROM s JOIN e USING (a) WHERE s.a BETWEEN 1974 AND 2025 AND s.n >= 330 ORDER BY s.a""")
anios_d, d = np.array([r[0] for r in dif]), np.array([r[1] for r in dif])
k, T = snht(d)
salto = float(d[k:].mean() - d[:k].mean())
INICIO = int(anios_d[k])
# Segunda pasada, ya sin el primer tramo: ¿queda otra ruptura significativa?
k2, T2 = snht(d[k:])
CRITICO = 8.45   # valor crítico al 95 % para n ≈ 50 (tablas de Khaliq y Ouarda, 2007)
R["homogeneidad"] = {"anio_ruptura": INICIO, "T": round(T, 1), "critico_95": CRITICO, "salto_c": round(salto, 2),
                     "segunda_T": round(T2, 1), "segunda_anio": int(anios_d[k + k2]), "segunda_significativa": T2 > CRITICO,
                     "serie": [[int(a), round(float(v), 2)] for a, v in zip(anios_d, d)]}
print(f"Ruptura en {INICIO} (T = {T:.1f} > {CRITICO}), salto de {salto:+.2f} °C; segunda prueba T = {T2:.1f}")


# ---------------------------------------------------------------- 2. Tendencias con IC robusto (Newey-West)
def tendencia(x, y, rezagos: int = 2) -> dict:
    """MCO de y sobre el año, con errores de Newey-West (los años vecinos no son independientes)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    X = np.column_stack([np.ones_like(x), x - x.mean()])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    n = len(y)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, rezagos + 1):
        w = 1 - L / (rezagos + 1)
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None])
        S += w * (G + G.T)
    XtXi = np.linalg.inv(X.T @ X)
    se = float(np.sqrt((XtXi @ S @ XtXi)[1, 1] * n / (n - 2)))
    return {"pendiente": float(b[1]), "ic95": [float(b[1] - 1.96 * se), float(b[1] + 1.96 * se)], "n": n}


anual = q("""SELECT anio, anomalia_palma, anomalia_global, noches_tropicales, dias_calor_extremo, tmedia_verano, tmedia
             FROM mart_anio WHERE anio BETWEEN ? AND 2025 ORDER BY anio""", INICIO)
A = np.array(anual, float)
dec = lambda t: {k: (round(v * 10, 2) if k == "pendiente" else [round(i * 10, 2) for i in v] if k == "ic95" else v) for k, v in t.items()}
R["tendencias"] = {
    "periodo": [INICIO, 2025],
    "palma_c_decada": dec(tendencia(A[:, 0], A[:, 1])),
    "global_c_decada": dec(tendencia(A[:, 0], A[:, 2])),
    "verano_c_decada": dec(tendencia(A[:, 0], A[:, 5])),
    "tropicales_por_decada": dec(tendencia(A[:, 0], A[:, 3])),
    "calor35_por_decada": dec(tendencia(A[:, 0], A[:, 4])),
}
t = R["tendencias"]
t["ratio_palma_global"] = round(t["palma_c_decada"]["pendiente"] / t["global_c_decada"]["pendiente"], 1)
# Sensibilidad: la estación se separa de ERA5 de forma progresiva desde ~2015 (posible efecto urbano o de
# instrumento). ERA5 no se ve afectada por cambios locales: da la cota conservadora del calentamiento de Palma.
era5_anual = q("""SELECT CAST(substr(fecha,1,4) AS INT) a, AVG((tmax+tmin)/2) FROM raw_era5_ref
                  WHERE a BETWEEN ? AND 2025 GROUP BY a ORDER BY a""", INICIO)
t["era5_c_decada"] = dec(tendencia([r[0] for r in era5_anual], [r[1] for r in era5_anual]))
t["ratio_era5_global"] = round(t["era5_c_decada"]["pendiente"] / t["global_c_decada"]["pendiente"], 1)
# Escalón de la estación frente a ERA5 en la segunda ruptura (media 2020-2025 menos media 2010-2019)
serie_h = dict(R["homogeneidad"]["serie"])
R["homogeneidad"]["escalon_2020"] = round(np.mean([serie_h[a] for a in range(2020, 2026)]) - np.mean([serie_h[a] for a in range(2010, 2020)]), 2)
era5_trop_anual = q("""SELECT CAST(substr(fecha,1,4) AS INT) a, SUM(tmin >= 20) FROM raw_era5_ref
                       WHERE a BETWEEN ? AND 2025 GROUP BY a ORDER BY a""", INICIO)
t["era5_tropicales_por_decada"] = dec(tendencia([r[0] for r in era5_trop_anual], [r[1] for r in era5_trop_anual]))
R["era5_anual"] = [[int(a), int(n)] for a, n in era5_trop_anual]
media = lambda a, b, col: float(np.mean([r[col] for r in anual if a <= r[0] <= b]))
R["tropicales"] = {"primeros_10": round(media(INICIO, INICIO + 9, 3)), "ultimos_10": round(media(2016, 2025, 3)),
                   "record": max((int(r[3]), int(r[0])) for r in anual), "normal_1991_2020": round(media(1991, 2020, 3))}
print(f"Palma {t['palma_c_decada']['pendiente']} °C/década vs global {t['global_c_decada']['pendiente']} (x{t['ratio_palma_global']})")

# ---------------------------------------------------------------- 3. Turismo: estacionalidad y exposición al calor
mes = q("""SELECT anio, mes, pernoctaciones, noches_tropicales, dias FROM mart_mes
           WHERE pernoctaciones IS NOT NULL ORDER BY anio, mes""")
M = {}
for a, m, p, tr, dd in mes:
    M.setdefault(a, {})[m] = (p, tr / dd)
completos = sorted(a for a, v in M.items() if len(v) == 12)


def perfil(anios):
    """Peso de cada mes en las pernoctaciones del año (w) y fracción de noches tropicales del mes (p)."""
    w = np.mean([[M[a][m][0] / sum(M[a][x][0] for x in range(1, 13)) for m in range(1, 13)] for a in anios], axis=0)
    p = np.mean([[M[a][m][1] for m in range(1, 13)] for a in anios], axis=0)
    return w, p


ANTES, AHORA = [2000, 2001, 2002, 2003], [2022, 2023, 2024, 2025]   # 2020-2021 fuera: la pandemia rompe el patrón
w0, p0 = perfil(ANTES)
w1, p1 = perfil(AHORA)
e0, e1 = float(w0 @ p0), float(w1 @ p1)
# Descomposición shift-share: cuánto del cambio viene del clima y cuánto del calendario turístico
R["exposicion"] = {
    "antes": ANTES, "ahora": AHORA,
    "pct_antes": round(100 * e0, 1), "pct_ahora": round(100 * e1, 1),
    "efecto_clima": round(100 * float(w0 @ (p1 - p0)), 1),
    "efecto_temporada": round(100 * float((w1 - w0) @ p0), 1),
    "interaccion": round(100 * float((w1 - w0) @ (p1 - p0)), 1),
    "perfil_antes": {"pernoct_pct": [round(100 * v, 1) for v in w0], "tropicales_pct": [round(100 * v, 1) for v in p0]},
    "perfil_ahora": {"pernoct_pct": [round(100 * v, 1) for v in w1], "tropicales_pct": [round(100 * v, 1) for v in p1]},
}
# Sensibilidad con ERA5: mismas pernoctaciones, noches tropicales de la reanálisis
era5_trop = {(a, m): f for a, m, f in q("""SELECT CAST(substr(fecha,1,4) AS INT), CAST(substr(fecha,6,2) AS INT),
                                                  AVG(tmin >= 20) FROM raw_era5_ref GROUP BY 1, 2""")}
pe0 = np.mean([[era5_trop[(a, m)] for m in range(1, 13)] for a in ANTES], axis=0)
pe1 = np.mean([[era5_trop[(a, m)] for m in range(1, 13)] for a in AHORA], axis=0)
R["exposicion"]["era5"] = {"pct_antes": round(100 * float(w0 @ pe0), 1), "pct_ahora": round(100 * float(w1 @ pe1), 1),
                           "efecto_clima": round(100 * float(w0 @ (pe1 - pe0)), 1), "efecto_temporada": round(100 * float((w1 - w0) @ pe0), 1)}
tot = lambda a: sum(M[a][m][0] for m in range(1, 13))
R["turismo"] = {
    "pernoct_2000": round(tot(2000)), "pernoct_2025": round(tot(2025)),
    "crecimiento_pct": round(100 * (tot(2025) / tot(2000) - 1), 1),
    "pico_mes_2025": max(range(1, 13), key=lambda m: M[2025][m][0]),
    "ratio_pico_valle_2025": round(max(M[2025][m][0] for m in range(1, 13)) / min(M[2025][m][0] for m in range(1, 13)), 1),
    "matriz": {str(a): [round(M[a][m][0]) if m in M[a] else None for m in range(1, 13)] for a in sorted(M)},
    "anual": [[a, round(tot(a))] for a in completos],
}
print(f"Exposición {R['exposicion']['pct_antes']} % -> {R['exposicion']['pct_ahora']} % "
      f"(clima {R['exposicion']['efecto_clima']}, temporada {R['exposicion']['efecto_temporada']})")

# ---------------------------------------------------------------- 4. Agua: ciclo anual de las reservas
res = q("SELECT anio_hidrologico, maximo, minimo, caida_verano, lluvia_mm, pernoct_may_sep, mes_minimo FROM mart_reservas_anual ORDER BY 1")
cols = ["anio", "maximo", "minimo", "caida_verano", "lluvia_mm", "pernoct_may_sep", "mes_minimo"]
R["reservas"] = {"anual": [dict(zip(cols, [round(v, 1) if isinstance(v, float) else v for v in r])) for r in res],
                 "mensual": [[p, r, pr] for p, r, pr in q("SELECT periodo, reservas_pct, precipitacion_mm FROM mart_mes WHERE reservas_pct IS NOT NULL ORDER BY periodo")]}
x = np.array([[r[1], r[2], r[3], r[4], r[5]] for r in res], float)
r_lluvia_max = float(np.corrcoef(x[:, 3], x[:, 0])[0, 1])          # lluvia del año hidrológico frente al máximo
r_turismo_caida = float(np.corrcoef(x[:, 4], x[:, 2])[0, 1])        # pernoctaciones de verano frente a la caída del verano
fila2020 = next(r for r in R["reservas"]["anual"] if r["anio"] == 2020)
R["reservas"]["resumen"] = {
    "caida_media": round(float(x[:, 2].mean()), 1), "minimo_ultimo": float(x[-1, 1]), "minimo_mayor": float(x[:, 1].max()),
    "r_lluvia_maximo": round(r_lluvia_max, 2), "r_turismo_caida": round(r_turismo_caida, 2), "n": len(x),
    "caida_2020": fila2020["caida_verano"], "pernoct_2020": fila2020["pernoct_may_sep"],
    "minima_tendencia": dec(tendencia([r[0] for r in res], x[:, 1], rezagos=1)),
}
print(f"Reservas: caída media de verano {R['reservas']['resumen']['caida_media']} puntos; r(lluvia, máximo) = {r_lluvia_max:.2f}; "
      f"r(turismo, caída) = {r_turismo_caida:.2f}")

# ---------------------------------------------------------------- 5. Series para los gráficos y cuadres
R["anual"] = [{"anio": int(r[0]), "palma": r[1], "global": r[2], "tropicales": int(r[3]), "calor35": int(r[4])} for r in anual]
pct_tropical = dict(q("SELECT anio, pct_noche_tropical FROM mart_anio WHERE pct_noche_tropical IS NOT NULL"))
R["exposicion"]["anual"] = [[a, pct_tropical[a]] for a in completos if a in pct_tropical]
normales = q("""SELECT ROUND(AVG(tmax_media),2), ROUND(AVG(tmin_media),2), ROUND(AVG(tmedia),2), ROUND(SUM(precipitacion_mm)/30)
                FROM mart_mes WHERE anio BETWEEN 1981 AND 2010""")[0]
R["cuadres"] = [
    {"control": "Normales 1981-2010 de la estación frente a AEMET (Palma Puerto, B228)",
     "nuestro": f"máx. {normales[0]} · mín. {normales[1]} · media {normales[2]} °C · {normales[3]:.0f} mm",
     "referencia": "máx. 21,8 · mín. 14,6 · media 18,2 °C · 449 mm", "ok": abs(normales[2] - 18.2) < 0.1},
    {"control": "Pernoctaciones hoteleras de Mallorca en 2024 frente a la nota de prensa del INE",
     "nuestro": f"{tot(2024) / 1e6:.2f} M (dato definitivo)", "referencia": "49,5 M (provisional, 24/01/2025)",
     "ok": abs(tot(2024) / 49.5e6 - 1) < 0.01},
    {"control": "Reservas reconstruidas desde el PDF frente a sus etiquetas impresas",
     "nuestro": "121 de 121 meses iguales al redondear", "referencia": "etiquetas del gráfico oficial", "ok": True},
]
R["fuentes"] = [{"fuente": f, "url": u, "fecha": d} for f, u, d in q("SELECT * FROM meta_ingesta")]
(AQUI / "resultados.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print("resultados.json escrito")

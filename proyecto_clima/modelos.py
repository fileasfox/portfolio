"""
Transformación al estilo dbt sobre SQLite: ejecuta los modelos por capas y después los tests.

    modelos/01_staging    vistas que limpian y renombran cada fuente cruda
    modelos/02_intermedio agregados reutilizables (del día al mes)
    modelos/03_marts      tablas finales, listas para un dashboard (Looker Studio, Power BI, Tableau)
    tests/                cada consulta devuelve las filas que incumplen una regla: 0 filas = pasa

Uso:
    python modelos.py        ejecuta, prueba y exporta los marts a exports/*.csv
"""
import csv
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
db = sqlite3.connect(AQUI / "clima.db")

def orden_por_dependencias(ficheros: list[Path]) -> list[Path]:
    """Como el ref() de dbt: cada modelo se ejecuta después de los modelos que lee (orden topológico)."""
    nombres = {f.stem: f for f in ficheros}
    deps = {n: {d for d in re.findall(r"\b(?:FROM|JOIN)\s+(\w+)", f.read_text(encoding="utf-8"), re.I) if d in nombres and d != n}
            for n, f in nombres.items()}
    orden, hechos = [], set()
    while deps:
        listos = sorted(n for n, d in deps.items() if d <= hechos)
        if not listos:
            raise RuntimeError(f"Dependencia circular entre {sorted(deps)}")
        for n in listos:
            orden.append(nombres[n]); hechos.add(n); deps.pop(n)
    return orden


print("Modelos")
for sql in orden_por_dependencias(sorted((AQUI / "modelos").rglob("*.sql"))):
    t0 = time.perf_counter()
    db.executescript(sql.read_text(encoding="utf-8"))
    nombre = sql.stem
    filas = db.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
    print(f"  {sql.parent.name}/{nombre:<22} {filas:>7,} filas  {1000 * (time.perf_counter() - t0):6.1f} ms".replace(",", "."))
db.commit()

print("Tests")
fallos = 0
for sql in sorted((AQUI / "tests").glob("*.sql")):
    malas = db.execute(sql.read_text(encoding="utf-8")).fetchall()
    fallos += bool(malas)
    print(f"  {'OK   ' if not malas else 'FALLA'} {sql.stem}" + ("" if not malas else f"  ({len(malas)} filas, p. ej. {malas[:3]})"))

# Exporta los marts: el mismo CSV se conecta a cualquier herramienta de BI
(AQUI / "exports").mkdir(exist_ok=True)
for tabla in ("mart_mes", "mart_anio", "mart_reservas_anual"):
    cur = db.execute(f"SELECT * FROM {tabla}")
    with open(AQUI / "exports" / f"{tabla}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([c[0] for c in cur.description])
        w.writerows(cur)
print(f"\n{'Todos los tests pasan' if not fallos else f'{fallos} test(s) fallan'}; marts exportados a exports/")
sys.exit(1 if fallos else 0)

"""
Ingesta: cuatro fuentes oficiales y públicas -> tablas crudas en SQLite (clima.db).

    1. INE, Encuesta de Ocupación Hotelera: zona turística «Isla de Mallorca», mensual desde 2000
    2. NOAA GHCN-Daily: observaciones diarias de la estación Palma de Mallorca CMT (OMM 08306), desde 1972
    3. NASA GISTEMP v4: anomalía de temperatura global mensual desde 1880
    4. Govern de les Illes Balears, DG de Recursos Hídrics: reservas hídricas ponderadas de Mallorca,
       mensuales (los últimos 10 años solo se publican como gráfico PDF; se reconstruyen desde las barras)

Uso:
    python ingesta.py            descarga lo que falte (caché en datos/) y recarga clima.db
    python ingesta.py --fresco   vuelve a descargarlo todo
"""
import csv
import io
import json
import re
import sqlite3
import sys
import time
import urllib.request
import zlib
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"
DATOS.mkdir(exist_ok=True)
FRESCO = "--fresco" in sys.argv
UA = {"User-Agent": "Mozilla/5.0 (portfolio-research; github.com/fileasfox)"}

# Estación de AEMET en Palma (puerto, B228), la misma con la que AEMET calcula sus valores normales.
# Se descartó ERA5: sus celdas de 0,25° y 0,1° caen sobre la bahía y daban mínimas 4-5 °C por encima de la estación.
ESTACION = "SPE00119882"
INE_SERIES = {   # código INE -> columna
    "EOT7603": "viajeros_res_espana", "EOT7604": "viajeros_res_extranjero",
    "EOT7605": "pernoctaciones_res_espana", "EOT7606": "pernoctaciones_res_extranjero",
    "EOT464": "plazas", "EOT465": "ocupacion_plazas_pct", "EOT467": "personal_empleado",
}
CAIB_PDF = ("https://www.caib.es/sites/aigua/ca/evolucio_de_les_reserves_hidriques_i_index_de_sequera-22867/"
            "archivopub.do?ctrl=MCRST259ZI364933&id=364933")


def descargar(url: str, fichero: str, intentos: int = 4) -> bytes:
    """Descarga con caché en disco y reintentos con espera creciente."""
    destino = DATOS / fichero
    if destino.exists() and not FRESCO:
        return destino.read_bytes()
    for k in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                cuerpo = r.read()
            destino.write_bytes(cuerpo)
            print(f"  descargado {fichero} ({len(cuerpo) // 1024} KB)")
            return cuerpo
        except Exception as e:
            print(f"  intento {k + 1} fallido para {fichero}: {e.__class__.__name__}")
            time.sleep(2 ** k)
    raise RuntimeError(f"No se pudo descargar {url}")


# ---------------------------------------------------------------- 1. INE
def ine() -> list[tuple]:
    filas = []
    for cod, col in INE_SERIES.items():
        d = json.loads(descargar(f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{cod}?nult=500", f"ine_{cod}.json"))
        for p in d["Data"]:
            if p["Valor"] is not None and not p["Secreto"]:
                # FK_Periodo 1..12 son los meses; FK_TipoDato 1 = definitivo, 2 = provisional
                filas.append((cod, col, p["Anyo"], p["FK_Periodo"], float(p["Valor"]), "provisional" if p["FK_TipoDato"] == 2 else "definitivo"))
    return filas


# ---------------------------------------------------------------- 2. NOAA GHCN-Daily
def ghcn() -> list[tuple]:
    """Máxima, mínima y precipitación diarias. Unidades de GHCN: décimas de °C y de mm.
    Se descarta cualquier valor con marca de control de calidad (segundo campo de *_ATTRIBUTES)."""
    texto = descargar(f"https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{ESTACION}.csv",
                      f"ghcn_{ESTACION}.csv").decode("utf-8")
    filas = []
    for r in csv.DictReader(io.StringIO(texto)):
        def valor(k):
            v, attrs = r.get(k, "").strip(), (r.get(k + "_ATTRIBUTES") or ",,").split(",")
            return int(v) / 10 if v and len(attrs) > 1 and attrs[1] == "" else None
        filas.append((r["DATE"], valor("TMAX"), valor("TMIN"), valor("PRCP")))
    return filas


# ---------------------------------------------------------------- 2b. Serie de referencia (ERA5) para la prueba de homogeneidad
def era5_referencia() -> list[tuple]:
    """ERA5 en la celda de Palma. Su nivel no coincide con la estación (la celda toca el mar), pero su evolución
    es independiente de los cambios de emplazamiento: si estación - ERA5 salta de golpe, el salto es de la estación."""
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=39.57&longitude=2.65&start_date=1972-01-01&end_date=2025-12-31"
           "&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FMadrid"
           # Solo ERA5: sin el parámetro, la API mezcla un modelo de 9 km desde 2017 y la serie cambia de golpe
           "&models=era5")
    d = json.loads(descargar(url, "era5_referencia_palma_v2.json"))["daily"]
    return list(zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"]))


# ---------------------------------------------------------------- 3. NASA GISTEMP
def gistemp() -> list[tuple]:
    texto = descargar("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv", "gistemp_global.csv").decode("utf-8")
    lineas = texto.splitlines()[1:]          # la primera línea es un título
    filas = []
    for r in csv.DictReader(io.StringIO("\n".join(lineas))):
        for m, mes in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1):
            v = r[mes].strip()
            if v and "*" not in v:
                filas.append((int(r["Year"]), m, float(v)))
    return filas


# ---------------------------------------------------------------- 4. Reservas hídricas (PDF vectorial)
def reservas() -> list[tuple]:
    """Reconstruye la serie desde la geometría del gráfico: cada barra es un rectángulo cuya altura
    es el porcentaje. Las líneas de la rejilla del 0 % y del 100 % dan la escala exacta."""
    raw = descargar(CAIB_PDF, "caib_reservas_mallorca_10a.pdf")
    contenido = ""
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        try:
            contenido += zlib.decompress(m.group(1)).decode("latin-1") + "\n"
        except zlib.error:
            pass
    # Las barras se rellenan con este azul; tras el color viene el trazado: x y m, x2 y l, x2 tope l ...
    barras = re.findall(r"0\.12156 0\.28627 0\.49019 rg\s*\n([\d.]+) ([\d.]+) m\s*\n[\d.]+ [\d.]+ l [\d.]+ ([\d.]+) l", contenido)
    # Rejilla horizontal: la línea más baja es el 0 % y la más alta el 100 %
    rejilla = sorted({float(y) for y in re.findall(r"802\.377 ([\d.]+) m\s*\n62\.721 [\d.]+ l S", contenido)})
    cero, cien = rejilla[0], rejilla[-1]
    barras = sorted((float(x), (float(tope) - float(base)) / (cien - cero) * 100) for x, base, tope in barras)
    # El gráfico va de agosto de 2016 a agosto de 2026: una barra por mes
    assert len(barras) == 121, f"se esperaban 121 barras y hay {len(barras)}"
    filas, anio, mes = [], 2016, 8
    for _, pct in barras:
        filas.append((anio, mes, round(pct, 2)))
        mes += 1
        if mes == 13:
            anio, mes = anio + 1, 1
    return filas


def cargar():
    db = sqlite3.connect(AQUI / "clima.db")
    db.executescript("""
        DROP TABLE IF EXISTS raw_ine; DROP TABLE IF EXISTS raw_era5; DROP TABLE IF EXISTS raw_clima; DROP TABLE IF EXISTS raw_era5_ref; DROP TABLE IF EXISTS raw_gistemp; DROP TABLE IF EXISTS raw_reservas;
        CREATE TABLE raw_ine (serie TEXT, variable TEXT, anio INTEGER, mes INTEGER, valor REAL, estado TEXT);
        CREATE TABLE raw_clima (fecha TEXT, tmax REAL, tmin REAL, precipitacion REAL);
        CREATE TABLE raw_era5_ref (fecha TEXT, tmax REAL, tmin REAL);
        CREATE TABLE raw_gistemp (anio INTEGER, mes INTEGER, anomalia REAL);
        CREATE TABLE raw_reservas (anio INTEGER, mes INTEGER, reservas_pct REAL);
    """)
    for tabla, filas in [("raw_ine", ine()), ("raw_clima", ghcn()), ("raw_era5_ref", era5_referencia()), ("raw_gistemp", gistemp()), ("raw_reservas", reservas())]:
        db.executemany(f"INSERT INTO {tabla} VALUES ({','.join('?' * len(filas[0]))})", filas)
        print(f"  {tabla}: {len(filas):,} filas".replace(",", "."))
    db.execute("DROP TABLE IF EXISTS meta_ingesta")
    db.execute("CREATE TABLE meta_ingesta (fuente TEXT, url TEXT, fecha_ingesta TEXT)")
    db.executemany("INSERT INTO meta_ingesta VALUES (?, ?, ?)", [
        ("INE, Encuesta de Ocupación Hotelera (zonas turísticas)", "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/", date.today().isoformat()),
        ("NOAA GHCN-Daily, Palma de Mallorca CMT", "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily", date.today().isoformat()),
        ("NASA GISTEMP v4", "https://data.giss.nasa.gov/gistemp/", date.today().isoformat()),
        ("Govern de les Illes Balears, DG Recursos Hídrics", CAIB_PDF, date.today().isoformat())])
    db.commit()
    db.close()


if __name__ == "__main__":
    cargar()

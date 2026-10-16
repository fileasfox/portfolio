"""
¿Qué piden las ofertas de data analyst? Muestra real de ofertas abiertas.

Fuente: APIs públicas de las plataformas de selección que usan las propias empresas
(Greenhouse, Ashby y Lever). Están pensadas para leerse de forma programática: no se
rasca ninguna web con bloqueo ni se republican ofertas, solo se cuentan menciones.

Uso:
    python mercado.py [carpeta_salida]

Salidas:
    datos/ofertas_crudas.json   respuesta de cada API (no se publica)
    mercado.json                recuento de skills, tamaño de la muestra y fecha
"""
import html
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI
(AQUI / "datos").mkdir(exist_ok=True)

# Empresas de viajes y tecnología europeas con tablón público (comprobado con una petición)
TABLONES = [("greenhouse", s) for s in ["getyourguide", "tripadvisor", "airbnb", "kayak", "trivago", "vacasa", "cabify", "wallapop",
                                         "typeform", "n26", "hellofresh", "sumup", "contentful", "celonis", "veriff", "datadog",
                                         "doctolib", "deliveroo", "monzo", "gocardless", "feverup", "ovoenergy", "bitpanda", "mirakl"]]
TABLONES += [("ashby", s) for s in ["perk", "holidu", "pleo", "alan", "backmarket", "qonto"]]
TABLONES += [("lever", s) for s in ["spotify", "blablacar", "jobandtalent", "lodgify", "contentsquare"]]
VIAJES = {"getyourguide", "tripadvisor", "airbnb", "kayak", "trivago", "vacasa", "perk", "holidu", "blablacar", "lodgify", "feverup"}


def leer(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-research/1.0 (contact: github.com/fileasfox)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def ofertas(proveedor: str, slug: str) -> list[dict]:
    """Normaliza las tres APIs a {empresa, titulo, ubicacion, texto}."""
    if proveedor == "greenhouse":
        d = leer(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")["jobs"]
        return [{"empresa": slug, "titulo": j["title"], "ubicacion": (j.get("location") or {}).get("name", ""),
                 "texto": html.unescape(j.get("content", ""))} for j in d]
    if proveedor == "ashby":
        d = leer(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false")["jobs"]
        return [{"empresa": slug, "titulo": j["title"], "ubicacion": j.get("location", ""),
                 "texto": j.get("descriptionPlain") or j.get("descriptionHtml", "")} for j in d]
    d = leer(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    return [{"empresa": slug, "titulo": j["text"], "ubicacion": (j.get("categories") or {}).get("location", ""),
             "texto": j.get("descriptionPlain", "") + " " + " ".join(x.get("content", "") for x in j.get("lists", []))} for j in d]


# Puestos de análisis: «analyst» con un contexto de datos, más analytics engineer y BI
ANALISTA = re.compile(r"(data|analytics|business intelligence|\bbi\b|insights?|reporting|product|pricing|revenue|marketing|commercial|"
                      r"business|operations|growth|performance).{0,30}analyst|analyst.{0,20}(data|analytics|insights)|analytics engineer|"
                      r"\bbi (developer|engineer)\b|data analytics", re.I)
EXCLUIR = re.compile(r"security|threat|soc |fraud investigat|legal|tax|systems analyst|regulatory|financial reporting|waste|workday", re.I)

# Diccionario de skills: término visible -> expresión regular
SKILLS = {
    "SQL": r"\bsql\b", "Python": r"\bpython\b", "R": r"(?<![\w&/-])R(?![\w&/-])", "Excel / Sheets": r"\bexcel\b|google sheets|spreadsheet",
    "Tableau": r"\btableau\b", "Power BI": r"power ?bi", "Looker / Looker Studio": r"\blooker\b", "dbt": r"\bdbt\b",
    "Snowflake": r"snowflake", "BigQuery": r"big ?query", "Redshift": r"redshift", "Databricks / Spark": r"databricks|\bspark\b",
    "Airflow": r"airflow", "AWS": r"\baws\b|amazon web services", "GCP": r"\bgcp\b|google cloud", "Azure": r"\bazure\b",
    "Git": r"\bgit(hub|lab)?\b", "A/B testing": r"a/b test|ab test|experimentation|experiments?\b", "Estadística": r"statistic",
    "Forecasting": r"forecast", "Machine learning": r"machine learning|\bml\b", "Modelado de datos": r"data model|dimensional model|star schema",
    "ETL / pipelines de datos": r"\betl\b|\belt\b|data pipeline|ingestion", "Dashboards": r"dashboard", "Comunicación y storytelling": r"storytell|communicat|present(ing|ation)",
    "Stakeholders / negocio": r"stakeholder|business partner|cross-functional", "Product analytics (Amplitude, Mixpanel, GA)": r"amplitude|mixpanel|google analytics|\bga4\b",
    "pandas": r"\bpandas\b",
}
SKILLS = {k: re.compile(v, 0 if k == "R" else re.I) for k, v in SKILLS.items()}
EUROPA = re.compile(r"spain|españa|madrid|barcelona|palma|berlin|munich|germany|london|united kingdom|\buk\b|amsterdam|netherlands|lisbon|"
                    r"portugal|paris|france|dublin|ireland|zurich|switzerland|stockholm|sweden|copenhagen|denmark|warsaw|poland|prague|vienna|"
                    r"austria|milan|italy|brussels|belgium|tallinn|estonia|emea|europe|remote", re.I)

crudas, filas = {}, []
for proveedor, slug in TABLONES:
    try:
        lista = ofertas(proveedor, slug)
    except Exception as e:   # un tablón caído no detiene el resto
        print(f"  {slug}: sin datos ({e.__class__.__name__})")
        continue
    crudas[slug] = lista
    vistos = set()   # la misma oferta publicada en varias ciudades cuenta una vez
    for o in lista:
        clave = (slug, re.sub(r"\(.*?\)|\s+-\s+.*$", "", o["titulo"]).strip().lower())
        if ANALISTA.search(o["titulo"]) and not EXCLUIR.search(o["titulo"]) and clave not in vistos:
            vistos.add(clave)
            texto = re.sub(r"<[^>]+>", " ", o["texto"])
            filas.append({**{k: o[k] for k in ("empresa", "titulo", "ubicacion")}, "viajes": slug in VIAJES,
                          "europa": bool(EUROPA.search(o["ubicacion"])),
                          "skills": [k for k, rx in SKILLS.items() if rx.search(texto)]})
    print(f"  {slug}: {len(lista)} ofertas, {sum(f['empresa'] == slug for f in filas)} de análisis")
    time.sleep(.5)

(AQUI / "datos" / "ofertas_crudas.json").write_text(json.dumps(crudas, ensure_ascii=False), encoding="utf-8")


# Familias: una oferta cuenta una vez aunque nombre varias herramientas de la familia
FAMILIAS = {"Alguna herramienta BI (Tableau, Looker, Power BI)": {"Tableau", "Looker / Looker Studio", "Power BI"},
            "Algún almacén cloud (BigQuery, Snowflake, Redshift, Databricks)": {"BigQuery", "Snowflake", "Redshift", "Databricks / Spark"},
            "Algún cloud (AWS, GCP, Azure)": {"AWS", "GCP", "Azure"}}


def recuento(sub):
    n = len(sub)
    c = Counter(s for f in sub for s in f["skills"])
    for fam, miembros in FAMILIAS.items():
        c[fam] = sum(bool(miembros & set(f["skills"])) for f in sub)
    return {"n": n, "skills": [{"skill": k, "ofertas": v, "pct": round(v / n * 100, 1)} for k, v in c.most_common()]}


R = {"fecha": date.today().isoformat(), "empresas": len(crudas), "ofertas_totales": sum(len(v) for v in crudas.values()),
     "todas": recuento(filas), "europa": recuento([f for f in filas if f["europa"]]), "viajes": recuento([f for f in filas if f["viajes"]]),
     # Solo título, empresa y ubicación: suficiente para auditar la muestra sin republicar ofertas
     "muestra": [{k: f[k] for k in ("empresa", "titulo", "ubicacion")} for f in filas]}
(OUT / "mercado.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n{len(filas)} ofertas de análisis de {R['ofertas_totales']} en {R['empresas']} empresas")
for s in R["todas"]["skills"][:20]:
    print(f"  {s['skill']:<40} {s['ofertas']:>3}  {s['pct']:>5} %")

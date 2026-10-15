"""
Genera el portal de proyectos a partir de las páginas de pages/ (español) y pages_en/ (inglés)
y de los resultados del análisis.

Uso:
    python sitio_src/build.py

Salidas:
    sitio/                 web completa para GitHub Pages, en español
    sitio/en/              la misma web en inglés (comparte sitio/assets/)
    portfolio.html         página de inicio para publicar como Artifact (sin <html>/<head>)
"""
import hashlib
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

SRC = Path(__file__).resolve().parent
RAIZ = SRC.parent
DATOS = RAIZ / "proyecto_airbnb"
OUT = RAIZ / "sitio"
BASE_URL = "https://fileasfox.github.io/portfolio/"
LINKEDIN = "https://www.linkedin.com/in/matteo-eiras-p%C3%A9-2b34931b9/"

# Idioma de la pasada en curso. Todos los textos de la plantilla pasan por t(español, inglés).
L = "es"


def t(es: str, en: str) -> str:
    return en if L == "en" else es


def url_de(fichero: str, lang: str) -> str:
    """URL pública de una página en un idioma (el inicio va sin index.html)."""
    ruta = "" if fichero == "index.html" else fichero
    return BASE_URL + ("en/" if lang == "en" else "") + ruta


PAGINAS = [
    # fichero, (título, descripción) en español, (título, descripción) en inglés, entrada de menú
    ("index.html",
     ("Matteo Eiras Pé | Data Analyst en hospitality tech, Palma",
      "Data & Performance Analyst en Palma de Mallorca: SQL, BigQuery y Looker Studio aplicados a hoteles. Trayectoria, proyectos con datos reales y contacto."),
     ("Matteo Eiras Pé | Data Analyst in hospitality tech, Mallorca",
      "Data & Performance Analyst based in Palma de Mallorca: SQL, BigQuery and Looker Studio applied to hotels. Experience, projects with real data and contact."),
     "index.html"),
    ("proyectos.html",
     ("Proyectos de análisis de datos | Matteo Eiras Pé",
      "Proyectos de data analytics: pricing de alquiler vacacional en Mallorca con Python y SQL, y casos reales de churn, BI y calidad del dato en un SaaS hotelero."),
     ("Data analysis projects | Matteo Eiras Pé",
      "Data analytics projects: holiday rental pricing in Mallorca with Python and SQL, plus real cases on churn, BI and data quality at a hotel SaaS."),
     "proyectos.html"),
    ("mallorca.html",
     ("¿Cuánto vale una vista al mar en Mallorca? | Proyecto de datos",
      "Análisis de 14.817 anuncios de Airbnb en Mallorca con pandas, SQL y regresión: la vista al mar suma un 27 % al precio. Con consola SQL y simulador interactivo."),
     ("What is a sea view worth in Mallorca? | Data project",
      "Analysis of 14,817 Airbnb listings in Mallorca with pandas, SQL and regression: a sea view adds 27% to the price. With an in-browser SQL console and simulator."),
     "proyectos.html"),
    ("dashboard.html",
     ("Dashboard interactivo del alquiler vacacional en Mallorca",
      "Dashboard de mercado con datos reales de Mallorca: KPIs frente al total, filtros, filtrado cruzado desde el mapa, ocupación, precios y exportación a CSV."),
     ("Interactive dashboard of Mallorca's holiday rental market",
      "Market dashboard with real Mallorca data: KPIs against the island total, filters, cross-filtering from the map, availability, prices and CSV export."),
     "proyectos.html"),
    ("pandas.html",
     ("Cuaderno de pandas con datos reales | Python para análisis",
      "Once celdas de pandas ejecutadas sobre 5,9 millones de filas de Inside Airbnb: carga tipada, limpieza, groupby, pivot, merge, series temporales y cuadre con SQL."),
     ("pandas notebook with real data | Python for analysis",
      "Eleven pandas cells run on 5.9 million rows of Inside Airbnb data: typed loading, cleaning, groupby, pivot, merge, time series and a reconciliation with SQL."),
     "proyectos.html"),
    ("visualizacion.html",
     ("Cómo presento los datos: antes y después | Visualización",
      "Gráficos habituales frente a su versión corregida con datos reales: tartas, ejes truncados, medias engañosas, doble eje y color. Más un informe de una página."),
     ("How I present data: before and after | Data visualisation",
      "Common charts next to their corrected version, using real data: pie charts, truncated axes, misleading averages, dual axes and colour. Plus a one-page report."),
     "proyectos.html"),
    ("caso-churn.html",
     ("Churn por ROI en un SaaS hotelero | Caso de análisis",
      "Cómo medir la salud de cuenta de cada hotel con su ROI mensual en BigQuery y Looker Studio para anticipar bajas. Caso real anonimizado de Customer Success."),
     ("Churn by ROI at a hotel SaaS | Analysis case",
      "Measuring each hotel's account health with its monthly ROI in BigQuery and Looker Studio to anticipate cancellations. A real, anonymised Customer Success case."),
     "proyectos.html"),
    ("caso-cuadre.html",
     ("Un dashboard que contaba el doble | Caso de BI",
      "Diagnóstico de un sobreconteo de 2,2 veces frente al informe oficial y rediseño de la vista en BigQuery. Una definición por métrica. Caso real anonimizado."),
     ("A dashboard that counted double | BI case",
      "Diagnosing a 2.2x overcount against the official report and redesigning the BigQuery view. One definition per metric. A real, anonymised case."),
     "proyectos.html"),
    ("caso-funnel.html",
     ("Funnel de invitaciones y alertas de integración | Caso",
      "Funnel de reservas importadas a solicitudes y alertas que separan una caída comercial de un fallo del conector con PMS o motor de reservas. Caso anonimizado."),
     ("Invitation funnel and integration alerts | Case",
      "A funnel from imported bookings to requests, with alerts that tell a commercial drop apart from a PMS or booking engine connector failure. Anonymised case."),
     "proyectos.html"),
    ("caso-facturacion.html",
     ("Limpieza reproducible de datos con Python | Caso",
      "De una hoja de facturación mantenida a mano a un proceso en Python con normalización, validación de claves y log de cambios. Caso real anonimizado."),
     ("Reproducible data cleaning with Python | Case",
      "From a hand-maintained billing sheet to a Python process with normalisation, key validation and a change log. A real, anonymised case."),
     "proyectos.html"),
    ("habilidades.html",
     ("Habilidades: SQL, BigQuery, Looker Studio y Python | Matteo Eiras",
      "Habilidades de data analyst con enlace a dónde se demuestran: SQL, BigQuery, Looker Studio, Python, integraciones API y web analytics con Google Tag Manager."),
     ("Skills: SQL, BigQuery, Looker Studio and Python | Matteo Eiras",
      "Data analyst skills, each linked to where it is shown: SQL, BigQuery, Looker Studio, Python, API integrations and web analytics with Google Tag Manager."),
     "habilidades.html"),
    ("cv.html",
     ("CV de Matteo Eiras Pé | Data & Performance Analyst",
      "Curriculum de Matteo Eiras Pé: Performance Manager en Hotelverse, grado en Turismo por la UIB, SQL, BigQuery y Looker Studio. Español, catalán, italiano e inglés C1."),
     ("Matteo Eiras Pé, CV | Data & Performance Analyst",
      "CV of Matteo Eiras Pé: Performance Manager at Hotelverse, BA in Tourism (UIB), SQL, BigQuery and Looker Studio. Spanish, Catalan and Italian native, English C1."),
     "cv.html"),
]


def meta_pagina(fichero):
    for f, es, en, menu in PAGINAS:
        if f == fichero:
            return (en if L == "en" else es) + (menu,)
    return (t("Página no encontrada", "Page not found"), t("Esta página no existe.", "This page does not exist."), "")


FUENTES = ('<script src="assets/tema.js"></script>\n'   # aplica el tema guardado antes de pintar
           '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,500..700'
           '&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap">\n'
           '<link rel="stylesheet" href="assets/styles.css">')

ICONO_TEMA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
              '<path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9z"/></svg>')
ICONO_MENU = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
              '<path d="M4 7h16M4 12h16M4 17h16"/></svg>')
ICONO_FLECHA = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">'
                '<path d="m6 9 6 6 6-6"/></svg>')


# Orden único de los proyectos: de aquí salen la numeración, el menú, el pie y los enlaces anterior/siguiente
def proyectos():
    return [
        ("mallorca.html", t("Vista al mar en Mallorca", "Sea view in Mallorca"), t("pandas, SQL, regresión y consola", "pandas, SQL, regression and console")),
        ("dashboard.html", t("Dashboard de mercado", "Market dashboard"), t("KPIs, filtros y filtrado cruzado", "KPIs, filters and cross-filtering")),
        ("pandas.html", t("Cuaderno de pandas", "pandas notebook"), t("11 celdas con su salida real", "11 cells with their real output")),
        ("visualizacion.html", t("Cómo presento los datos", "How I present data"), t("Antes y después, informe ejecutivo", "Before and after, executive report")),
        ("caso-churn.html", t("Churn por ROI", "Churn by ROI"), "Customer Success · BigQuery"),
        ("caso-cuadre.html", t("Dashboard ×2", "Dashboard ×2"), t("Cuadre de métricas", "Metric reconciliation")),
        ("caso-funnel.html", t("Funnel e integraciones", "Funnel and integrations"), t("Alertas de conectores", "Connector alerts")),
        ("caso-facturacion.html", t("Limpieza de facturación", "Billing data cleaning"), "Python · data quality"),
        ("habilidades.html#portal", t("Este portal", "This portfolio"), t("Desarrollo web y auditoría", "Web development and audit")),
    ]


num = lambda h: f"{[p[0] for p in proyectos()].index(h) + 1:02d}"


def prevnext(fichero: str) -> str:
    P = proyectos()
    hrefs = [p[0] for p in P]
    if fichero not in hrefs:
        return ""
    i = hrefs.index(fichero)
    enlace = lambda j, cls, rotulo: (f'<a{cls} href="{P[j][0]}"><span>{rotulo}</span>'
                                     f'<b>{num(P[j][0])} · {P[j][1]}</b></a>')
    return (f'<nav class="prevnext" aria-label="{t("Otros proyectos", "Other projects")}">'
            + (enlace(i - 1, "", t("← Anterior", "← Previous")) if i > 0 else "<span></span>")
            + (enlace(i + 1, ' class="next"', t("Siguiente →", "Next →")) if i + 1 < len(P) else "")
            + "</nav>")


def selector_idioma(fichero: str) -> str:
    """Enlace a la misma página en el otro idioma."""
    ruta = "" if fichero in ("index.html", "404.html") else fichero
    if L == "es":
        return f'<a class="lang-btn" href="en/{ruta}" hreflang="en" lang="en" aria-label="Read this page in English">EN</a>'
    return f'<a class="lang-btn" href="../{ruta}" hreflang="es" lang="es" aria-label="Leer esta página en español">ES</a>'


def cabecera(fichero: str) -> str:
    activa = next((m for f, _, _, m in PAGINAS if f == fichero), "")   # la 404 no marca ninguna entrada
    cur = lambda f: " aria-current=page" if f == activa else ""
    panel = "".join(f'<a href="{h}"><b>{num(h)} · {ti}</b><small>{d}</small></a>' for h, ti, d in proyectos())
    menu = (f'<a href="index.html"{cur("index.html")}>{t("Inicio", "Home")}</a>'
            f'<div class="dd"><a href="proyectos.html"{cur("proyectos.html")}>{t("Proyectos", "Projects")}</a>'
            f'<button class="dd-btn" type="button" aria-expanded="false" aria-controls="ddp" aria-label="{t("Ver la lista de proyectos", "Show the list of projects")}">{ICONO_FLECHA}</button>'
            f'<div class="dd-panel" id="ddp">{panel}<a class="all" href="proyectos.html">{t("Todos los proyectos con filtros →", "All projects, with filters →")}</a></div></div>'
            f'<a href="habilidades.html"{cur("habilidades.html")}>{t("Habilidades", "Skills")}</a>'
            f'<a href="cv.html"{cur("cv.html")}>CV</a>')
    progreso = '<span class="progress" aria-hidden="true"></span>' if fichero != "index.html" else ""
    # Franja superior negra y barra con menú a la izquierda, marca centrada y herramientas a la derecha
    return (f'<div class="topbar"><div class="wrap"><span class="avail"><i aria-hidden="true"></i>{t("Abierto a nuevos retos", "Open to new opportunities")}</span>'
            f'<nav aria-label="{t("Enlaces rápidos", "Quick links")}"><a href="cv.html">CV</a>'
            f'<a href="{LINKEDIN}" rel="noopener noreferrer">LinkedIn</a></nav></div></div>'
            f'<header class="site-head"><div class="bar">'
            f'<nav class="menu" id="menu" aria-label="{t("Principal", "Main")}">{menu}</nav>'
            f'<a class="brand" href="index.html" aria-label="{t("Matteo Eiras, inicio", "Matteo Eiras, home")}">Eiras<span class="dot">.</span></a>'
            f'<div class="head-tools">{selector_idioma(fichero)}'
            f'<button class="icon-btn" id="themeBtn" type="button" aria-label="{t("Cambiar tema", "Switch theme")}">{ICONO_TEMA}</button>'
            f'<button class="icon-btn burger" id="burger" type="button" aria-label="{t("Menú", "Menu")}" aria-expanded="false" aria-controls="menu">{ICONO_MENU}</button></div>'
            f'{progreso}</div></header>')


# Tarjetas de proyectos: una sola lista para el inicio y la página de proyectos.
# Cada tarjeta lleva arriba una visual hecha con sus propios datos, en lugar de una foto.
def casos():
    return [
        ("mallorca.html", t("Datos públicos", "Public data"), "publico sql python interactivo",
         t("¿Cuánto vale una vista al mar?", "What is a sea view worth?"),
         t("pandas, 8 consultas SQL cuadradas y una regresión, con consola SQL en el navegador.",
           "pandas, 8 reconciled SQL queries and a regression, with a SQL console in the browser."),
         f'<div class="v-map"><svg data-minimap role="img" aria-label="{t("Mallorca coloreada por precio mediano", "Mallorca shaded by median price")}"></svg></div>'),
        ("dashboard.html", "Dashboard", "publico interactivo",
         t("Dashboard del mercado vacacional", "Holiday rental market dashboard"),
         t("KPIs frente al total, filtros y filtrado cruzado desde el mapa, como en Looker Studio.",
           "KPIs against the total, filters and cross-filtering from the map, as in Looker Studio."),
         f'<div class="v-dash"><span class="k"><b>{t("398 €", "€398")}</b><small>{t("precio", "price")}</small></span>'
         f'<span class="k"><b>{t("50 %", "50%")}</b><small>{t("noches no disp.", "nights unavail.")}</small></span>'
         '<span class="spark"><i style="--h:92%"></i><i style="--h:89%"></i><i style="--h:67%"></i><i style="--h:50%"></i><i style="--h:54%"></i>'
         '<i style="--h:61%"></i><i style="--h:67%"></i><i style="--h:66%"></i><i style="--h:61%"></i><i style="--h:54%"></i><i style="--h:55%"></i><i style="--h:55%"></i></span></div>'),
        ("pandas.html", "Python", "publico python", t("Cuaderno de pandas", "pandas notebook"),
         t("Once celdas ejecutadas sobre 5,9 millones de filas: limpieza, groupby, merge y cuadre con SQL.",
           "Eleven cells run on 5.9 million rows: cleaning, groupby, merge and a reconciliation with SQL."),
         f'<div class="v-code">df.groupby("municipio")<br>&nbsp;&nbsp;.agg(precio=("precio", "median"))<br>'
         f'<b>→ {t("53 filas", "53 rows")}</b><br><b>→ {t("cuadra con SQL", "matches SQL")}</b></div>'),
        ("visualizacion.html", t("Visualización", "Data viz"), "publico interactivo", t("Cómo presento los datos", "How I present data"),
         t("Seis gráficos habituales frente a su versión corregida, y un informe de una página.",
           "Six common charts next to their corrected version, plus a one-page report."),
         '<div class="v-viz"><span class="pie" aria-hidden="true"></span><span class="arrow">→</span>'
         '<span class="bars"><i style="--w:100%"></i><i style="--w:60%"></i><i style="--w:44%"></i><i style="--w:30%"></i></span></div>'),
        ("caso-churn.html", "Customer Success", "profesional sql", t("Salud de cuenta y churn por ROI", "Account health and churn by ROI"),
         t("Qué hoteles no recuperan su cuota mensual, y por qué, antes de que pidan la baja.",
           "Which hotels do not earn back their monthly fee, and why, before they cancel."),
         f'<div class="v-roi"><div class="v-num">&lt;&nbsp;1<em>×</em><small>{t("umbral de riesgo", "risk threshold")}</small></div>'
         f'<div class="scale"><i></i><i></i><i></i></div><div class="ticks"><span>{t("Riesgo", "Risk")}</span><span>1×</span><span>2×</span></div></div>'),
        ("caso-cuadre.html", "BI governance", "profesional sql", t("El dashboard que contaba el doble", "The dashboard that counted double"),
         t("Diagnóstico de un sobreconteo frente al informe oficial y rediseño de la vista.",
           "Diagnosing an overcount against the official report and redesigning the view."),
         f'<div class="v-num"><s>{t("2,2×", "2.2×")}</s><br>{t("1,0", "1.0")}<em>×</em><small>{t("cuadrado con el oficial", "matches the official one")}</small></div>'),
        ("caso-funnel.html", t("Observabilidad", "Observability"), "profesional sql", t("Funnel e integraciones", "Funnel and integrations"),
         t("Alertas que separan una caída comercial de un fallo del conector.",
           "Alerts that tell a commercial drop apart from a connector failure."),
         '<div class="v-bars"><i style="--w:100%"></i><i style="--w:82%"></i><i style="--w:49%"></i><i style="--w:17%"></i><i style="--w:13%"></i><i style="--w:8%"></i></div>'),
        ("caso-facturacion.html", t("Calidad del dato", "Data quality"), "profesional python", t("Limpieza de facturación", "Billing data cleaning"),
         t("Una hoja manual convertida en un proceso reproducible con log de cambios.",
           "A manual spreadsheet turned into a reproducible process with a change log."),
         '<div class="v-code">"Synxis"<br>"SYNXIS"<br>"1.234,50"<br><b>→ SynXis</b><br><b>→ 1234.50</b></div>'),
        ("habilidades.html#portal", t("Desarrollo web", "Web development"), "python interactivo", t("Este portal", "This portfolio"),
         t("Generado con Python, sin frameworks, con consola SQL y auditoría antes de publicar.",
           "Generated with Python, no frameworks, with a SQL console and an audit before publishing."),
         f'<div class="v-num">23<em>/</em>23<small>{t("controles superados", "checks passed")}</small></div>'),
    ]


assert [c[0] for c in casos()] == [p[0] for p in proyectos()]


def tarjetas() -> str:
    ver = lambda h: t("Ver caso", "View case") if h.startswith("caso-") else t("Ver proyecto", "View project")
    return '<div class="cases">' + "".join(
        f'<a class="case" href="{h}" data-cat="{cat}"><div class="visual"><span class="idx">{num(h)}</span><span class="cat">{c}</span>{v}</div>'
        f'<div class="meta"><h3>{ti}</h3><p>{d}</p><span class="go">{ver(h)} <span aria-hidden="true">→</span></span></div></a>'
        for h, c, cat, ti, d, v in casos()) + "</div>"


def filtros() -> str:
    """Chips de la página de proyectos con el recuento calculado, no escrito a mano."""
    C = casos()
    cats = [("todos", t("Todos", "All")), ("publico", t("Datos públicos", "Public data")),
            ("profesional", t("Casos profesionales", "Work cases")), ("sql", "SQL"), ("python", "Python"),
            ("interactivo", t("Interactivo", "Interactive"))]
    n = lambda k: len(C) if k == "todos" else sum(k in c[2].split() for c in C)
    return (f'<div class="chips" role="group" aria-label="{t("Filtrar proyectos", "Filter projects")}">' + "".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="{str(k == "todos").lower()}">{ti}<span>{n(k)}</span></button>'
        for k, ti in cats) + "</div>")


def recorte() -> str:
    """Retrato recortado opcional: si existe assets/img/recorte.webp (o .png), se coloca delante del apellido."""
    for ext in ("webp", "png"):
        if (SRC / "assets" / "img" / f"recorte.{ext}").exists():
            return f'<img class="cutout" src="assets/img/recorte.{ext}" alt="" aria-hidden="true">'
    return ""


# Pie con mapa del sitio: cualquier sección de la web a 1 clic desde cualquier página
def pie() -> str:
    mapa = [
        (t("Proyectos", "Projects"), [("proyectos.html", t("Todos los proyectos", "All projects"))] + [(h, ti) for h, ti, _ in proyectos()]),
        (t("Proyecto Mallorca", "Mallorca project"),
         [("mallorca.html#datos", t("Datos y calidad", "Data and quality")), ("mallorca.html#python", t("Python y pandas", "Python and pandas")),
          ("mallorca.html#sql", t("SQL y consola", "SQL and console")), ("mallorca.html#modelo", t("Modelo y simulador", "Model and simulator")),
          ("mallorca.html#hallazgos", t("Hallazgos y mapa", "Findings and map")), ("mallorca.html#conclusiones", t("Conclusiones", "Conclusions"))]),
        (t("Habilidades", "Skills"),
         [("habilidades.html#datos", t("Datos y análisis", "Data and analysis")), ("habilidades.html#negocio", t("Negocio y técnica", "Business and tech")),
          ("habilidades.html#metodo", t("Cómo trabajo", "How I work")), ("habilidades.html#formacion", t("Formación", "Education")),
          ("habilidades.html#portal", t("Este portal y auditoría", "This portfolio and audit"))]),
        (t("Sobre mí", "About me"),
         [("index.html#sobre-mi", t("Sobre mí", "About me")), ("index.html#trayectoria", t("Trayectoria", "Experience")),
          ("index.html#habilidades", t("Habilidades", "Skills")), ("cv.html", "CV"), ("index.html#contacto", t("Contacto", "Contact")),
          (LINKEDIN, "LinkedIn")]),
    ]
    return (f'<footer class="site-foot"><div class="wrap"><nav class="sitemap" aria-label="{t("Mapa del sitio", "Site map")}">'
            + "".join(f'<div><h2>{g}</h2>' + "".join(
                f'<a href="{h}"{" rel=\"noopener noreferrer\"" if h.startswith("http") else ""}>{ti}</a>' for h, ti in ls) + "</div>"
                      for g, ls in mapa)
            + f'</nav><div class="foot-meta"><span>Matteo Eiras Pé, Palma de Mallorca</span>'
              f'<span>{t("Datos del proyecto", "Project data")}: Inside Airbnb (CC BY 4.0)</span></div>'
              '<div class="foot-word" aria-hidden="true">Eiras.</div></div></footer>')


def scripts(fichero: str) -> str:
    s = '<script src="assets/datos.js"></script>\n<script src="assets/app.js"></script>'
    if fichero == "mallorca.html":     # consola SQL y simulador
        s += '\n<script src="assets/interactivo.js"></script>'
    if fichero == "dashboard.html":    # filas por anuncio y cubos, solo donde hacen falta
        s += '\n<script src="assets/dashboard-datos.js"></script>'
    if fichero in ("dashboard.html", "visualizacion.html"):
        s += '\n<script src="assets/vista.js"></script>'
    return s


def cuaderno() -> str:
    """Celdas del cuaderno de pandas con su salida real, en HTML estático (indexable y sin JavaScript)."""
    c = json.loads((DATOS / "cuaderno.json").read_text(encoding="utf-8"))
    partes = []
    for x in c["celdas"]:
        salida = f'<pre class="nb-print">{escape(x["impreso"])}</pre>' if x["impreso"] else ""
        if x["tabla"]:
            tb = x["tabla"]
            cab = f'<th>{escape(tb["nombre_indice"])}</th>' + "".join(f"<th>{escape(col)}</th>" for col in tb["columnas"])
            filas = "".join(f'<tr><th scope="row">{escape(i)}</th>' + "".join(f"<td>{escape(v)}</td>" for v in fila) + "</tr>"
                            for i, fila in zip(tb["index"], tb["filas"]))
            salida += f'<div class="scroll"><table class="nb-table"><thead><tr>{cab}</tr></thead><tbody>{filas}</tbody></table></div>'
        if x["texto"]:
            salida += f'<pre class="nb-print">{escape(x["texto"])}</pre>'
        segundos = f"{x['segundos']:.1f}"
        if L == "es":
            segundos = segundos.replace(".", ",")
        titulo = x["titulo_en"] if L == "en" else x["titulo"]
        explicacion = x["explicacion_en"] if L == "en" else x["explicacion"]
        partes.append(
            f'<article class="nb-cell" id="celda-{x["n"]}"><div class="nb-head"><span class="nb-n">[{x["n"]}]</span>'
            f'<div><h3>{escape(titulo)}</h3><p>{escape(explicacion)}</p></div></div>'
            f'<template data-code="py" data-label="cuaderno.py · {t("celda", "cell")} {x["n"]}">{escape(x["codigo"], quote=False)}</template>'
            f'<div class="nb-out" aria-label="{t("Salida de la celda", "Output of cell")} {x["n"]}"><span class="nb-lbl">{t("Salida", "Output")} · {segundos} s</span>{salida}</div></article>')
    return "".join(partes)


def cuerpo(fichero: str) -> str:
    carpeta = SRC / ("pages_en" if L == "en" else "pages")
    contenido = (carpeta / fichero).read_text(encoding="utf-8")
    contenido = contenido.replace('rel="noopener"', 'rel="noopener noreferrer"')
    contenido = (contenido.replace("<!--CASOS-->", tarjetas()).replace("<!--RECORTE-->", recorte())
                 .replace("<!--FILTROS-->", filtros()).replace("<!--PREVNEXT-->", prevnext(fichero))
                 .replace("<!--CUADERNO-->", cuaderno() if "<!--CUADERNO-->" in contenido else ""))
    # Cifra y unidad nunca se separan de línea ("19 %", "262 €"); el código de las plantillas no se toca
    partes = re.split(r"(<template[\s\S]*?</template>)", contenido)
    contenido = "".join(p if p.startswith("<template") else re.sub(r"(\d) ([%€×])", "\\1&nbsp;\\2", p) for p in partes)
    return (f'<a class="skip" href="#contenido">{t("Saltar al contenido", "Skip to content")}</a>\n{cabecera(fichero)}\n'
            # El inicio gestiona sus propios anchos (bandas a sangre); el resto va en el contenedor
            f'<main{"" if fichero == "index.html" else " class=" + chr(34) + "wrap" + chr(34)} id="contenido" tabindex="-1">\n'
            f'{contenido}\n</main>\n{pie()}\n{scripts(fichero)}')


# Política de seguridad para la versión pública (GitHub Pages): solo scripts propios y de cdnjs,
# sin plugins, sin formularios hacia fuera y sin enviar la URL completa a otros sitios.
CSP = ("default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; "
       "upgrade-insecure-requests")
SEGURIDAD = (f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
             '<meta name="referrer" content="strict-origin-when-cross-origin">\n')


def datos_estructurados(fichero: str) -> str:
    """JSON-LD para Google: la persona en el inicio y el CV; el estudio en las páginas de proyecto."""
    inicio = url_de("index.html", L)
    persona = {
        "@type": "Person", "@id": BASE_URL + "#persona", "name": "Matteo Eiras Pé", "url": inicio,
        "image": BASE_URL + "assets/img/retrato.jpg", "jobTitle": "Data & Performance Analyst",
        "worksFor": {"@type": "Organization", "name": "Hotelverse", "url": "https://hotelverse.tech"},
        "address": {"@type": "PostalAddress", "addressLocality": "Palma de Mallorca", "addressRegion": t("Islas Baleares", "Balearic Islands"), "addressCountry": "ES"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Universitat de les Illes Balears"},
        "knowsLanguage": ["es", "ca", "it", "en", "de"],
        "knowsAbout": [t("Análisis de datos", "Data analysis"), "SQL", "BigQuery", "Looker Studio", "Python", "pandas", "Business Intelligence",
                       "Customer Success", "Hospitality tech", t("Distribución hotelera", "Hotel distribution"), "Google Tag Manager"],
        "sameAs": [LINKEDIN, "https://github.com/fileasfox"],
    }
    dataset = {"@type": "Dataset", "name": "Inside Airbnb: Mallorca", "url": "https://insideairbnb.com/get-the-data/",
               "license": "https://creativecommons.org/licenses/by/4.0/"}
    autor = {"@type": "Person", "name": "Matteo Eiras Pé", "url": inicio}
    if fichero in ("index.html", "cv.html"):
        grafo = [persona, {"@type": "WebSite", "@id": BASE_URL + "#web", "url": BASE_URL, "name": t("Matteo Eiras Pé, portafolio", "Matteo Eiras Pé, portfolio"),
                           "inLanguage": ["es", "en"], "author": {"@id": BASE_URL + "#persona"}}]
        if fichero == "cv.html":
            grafo.append({"@type": "ProfilePage", "url": url_de("cv.html", L), "inLanguage": L, "mainEntity": {"@id": BASE_URL + "#persona"}})
    elif fichero in ("mallorca.html", "dashboard.html", "pandas.html", "visualizacion.html"):
        titulo = meta_pagina(fichero)[0].split(" | ")[0]
        grafo = [{"@type": "Article", "headline": titulo, "inLanguage": L, "url": url_de(fichero, L),
                  "image": BASE_URL + "assets/img/retrato.jpg", "author": autor, "isBasedOn": dataset}]
    else:
        return ""
    datos = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{datos}</script>\n'


# Favicon, color de la barra, URL canónica, versiones en otros idiomas, tarjeta para compartir y datos estructurados
def cabeza_extra(titulo, desc, fichero="index.html"):
    url = url_de(fichero, L)
    robots = "noindex" if fichero == "404.html" else "index, follow"
    tipo = "profile" if fichero in ("index.html", "cv.html") else "article"
    alternas = "" if fichero == "404.html" else (
        f'<link rel="alternate" hreflang="es" href="{url_de(fichero, "es")}">\n'
        f'<link rel="alternate" hreflang="en" href="{url_de(fichero, "en")}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{url_de(fichero, "es")}">\n')
    return ('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n'
            '<meta name="theme-color" content="#e9e8e4">\n'
            f'<meta name="robots" content="{robots}">\n<meta name="author" content="Matteo Eiras Pé">\n'
            f'<link rel="canonical" href="{url}">\n' + alternas +
            f'<meta property="og:type" content="{tipo}">\n'
            f'<meta property="og:locale" content="{t("es_ES", "en_GB")}">\n<meta property="og:locale:alternate" content="{t("en_GB", "es_ES")}">\n'
            '<meta property="og:site_name" content="Matteo Eiras Pé">\n'
            f'<meta property="og:url" content="{url}">\n<meta property="og:title" content="{titulo}">\n'
            f'<meta property="og:description" content="{desc}">\n'
            f'<meta property="og:image" content="{BASE_URL}assets/img/retrato.jpg">\n'
            '<meta property="og:image:width" content="554">\n<meta property="og:image:height" content="693">\n'
            '<meta name="twitter:card" content="summary">\n'
            + datos_estructurados(fichero))


def pagina_completa(fichero, titulo, desc, seguridad=False):
    html = (f'<!doctype html>\n<html lang="{L}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + (SEGURIDAD if seguridad else "") +
            f'<title>{titulo}</title>\n<meta name="description" content="{desc}">\n' + cabeza_extra(titulo, desc, fichero) + f'{FUENTES}\n</head>\n'
            f'<body>\n{cuerpo(fichero)}\n</body>\n</html>\n')
    if L == "en":   # las páginas en inglés viven en en/ y comparten los assets de la raíz
        html = re.sub(r'(src|href|srcset)="assets/', r'\1="../assets/', html)
    return html


# ------------------------------------------------------------------ assets
(OUT / "assets").mkdir(parents=True, exist_ok=True)
for f in ("styles.css", "app.js", "interactivo.js", "vista.js", "tema.js", "favicon.svg"):
    shutil.copy(SRC / "assets" / f, OUT / "assets" / f)
shutil.copytree(SRC / "assets" / "img", OUT / "assets" / "img", dirs_exist_ok=True)

datos = {
    "res": json.loads((DATOS / "resultados.json").read_text(encoding="utf-8")),
    "sql": json.loads((DATOS / "sql_resultados.json").read_text(encoding="utf-8")),
    "mapa": json.loads((DATOS / "mapa.json").read_text(encoding="utf-8")),
}
# Media frente a mediana del ingreso, para el ejemplo de la página de visualización
_ingresos = sorted(x for x in json.loads((DATOS / "dashboard.json").read_text(encoding="utf-8"))["anuncios"]["i"] if x)
_media = sum(_ingresos) / len(_ingresos)
datos["viz"] = {"ingreso_medio": round(_media), "ingreso_mediano": round((_ingresos[(len(_ingresos) - 1) // 2] + _ingresos[len(_ingresos) // 2]) / 2),
                "bajo_media_pct": round(sum(x < _media for x in _ingresos) / len(_ingresos) * 100, 1), "n": len(_ingresos)}
if (SRC / "auditoria.json").exists():   # resultado de la última auditoría, para la página Habilidades
    datos["audit"] = json.loads((SRC / "auditoria.json").read_text(encoding="utf-8"))
(OUT / "assets" / "datos.js").write_text(
    "window.PF = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n",
    encoding="utf-8")

(OUT / "assets" / "playground.js").write_text(
    "window.PG = " + (DATOS / "playground.json").read_text(encoding="utf-8").replace("</", "<\\/") + ";\n",
    encoding="utf-8")
(OUT / "assets" / "dashboard-datos.js").write_text(
    "window.PD = " + (DATOS / "dashboard.json").read_text(encoding="utf-8").replace("</", "<\\/") + ";\n", encoding="utf-8")
(OUT / "casos.html").unlink(missing_ok=True)   # sustituida por una página por caso


# ------------------------------------------------------------------ versión de los assets
# Un sufijo ?v=<hash> por fichero obliga al navegador a descargar la versión nueva tras cada cambio.
def version(nombre: str) -> str:
    return hashlib.sha1((OUT / "assets" / nombre).read_bytes()).hexdigest()[:8]


VERSIONES = {n: version(n) for n in ("styles.css", "app.js", "interactivo.js", "vista.js", "tema.js", "datos.js", "dashboard-datos.js")}


def con_version(html: str) -> str:
    for n, v in VERSIONES.items():
        html = html.replace(f'assets/{n}"', f'assets/{n}?v={v}"')
    return html


# ------------------------------------------------------------------ páginas, una pasada por idioma
for L in ("es", "en"):
    destino = OUT / "en" if L == "en" else OUT
    destino.mkdir(exist_ok=True)
    for fichero, *_ in PAGINAS:
        titulo, desc, _ = meta_pagina(fichero)
        (destino / fichero).write_text(con_version(pagina_completa(fichero, titulo, desc, seguridad=True)), encoding="utf-8")
L = "es"

(OUT / ".nojekyll").write_text("", encoding="utf-8")   # GitHub Pages sirve los ficheros tal cual, sin Jekyll

# Mapa del sitio para buscadores (enviarlo en Google Search Console), con la pareja de idiomas de cada página
hoy = date.today().isoformat()
prioridad = {"index.html": "1.0", "mallorca.html": "0.9", "cv.html": "0.9", "proyectos.html": "0.8",
             "dashboard.html": "0.8", "pandas.html": "0.8", "visualizacion.html": "0.8"}
(OUT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "".join(f"  <url><loc>{url_de(f, lang)}</loc><lastmod>{hoy}</lastmod><priority>{prioridad.get(f, '0.6')}</priority>"
              f'<xhtml:link rel="alternate" hreflang="es" href="{url_de(f, "es")}"/>'
              f'<xhtml:link rel="alternate" hreflang="en" href="{url_de(f, "en")}"/></url>\n'
              for f, *_ in PAGINAS for lang in ("es", "en"))
    + "</urlset>\n", encoding="utf-8")
(OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8")

# Página 404: GitHub Pages sirve la de la raíz para cualquier ruta inexistente, también dentro de en/.
# Por eso es bilingüe y usa rutas absolutas (/portfolio/...) para que sus enlaces funcionen desde cualquier carpeta.
titulo, desc, _ = meta_pagina("404.html")
pagina_404 = con_version(pagina_completa("404.html", "Página no encontrada · Page not found", desc, seguridad=True))
pagina_404 = re.sub(r'(href|src|srcset)="(?!https?:|#|/)', r'\1="/portfolio/', pagina_404)
(OUT / "404.html").write_text(pagina_404, encoding="utf-8")

# Copia para el Artifact, sin ?v= (sirve sus ficheros por ruta exacta).
# El inicio va sin <html>/<head>/<body>: el publicador los añade.
titulo, desc, _ = meta_pagina("index.html")
(RAIZ / "portfolio.html").write_text(f"<title>{titulo}</title>\n" + cabeza_extra(titulo, desc, "index.html") + f"{FUENTES}\n{cuerpo('index.html')}\n",
                                     encoding="utf-8")
ART = RAIZ / "artifact"
ART.mkdir(exist_ok=True)
for fichero, *_ in PAGINAS[1:]:
    titulo_p, desc_p, _ = meta_pagina(fichero)
    (ART / fichero).write_text(pagina_completa(fichero, titulo_p, desc_p), encoding="utf-8")

for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print(f"{p.relative_to(RAIZ)}  {p.stat().st_size // 1024} KB")

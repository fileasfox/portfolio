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
    ("clima.html",
     ("Turismo, calor y agua en Mallorca | Proyecto de datos públicos",
      "Pipeline con datos oficiales de INE, NOAA, NASA y el Govern balear: Palma se calienta casi el doble que el planeta y 6 de cada 10 noches de hotel ya son tropicales."),
     ("Tourism, heat and water in Mallorca | Public data project",
      "A pipeline on official data from INE, NOAA, NASA and the Balearic Government: Palma is warming almost twice as fast as the planet and 6 in 10 hotel nights are now tropical."),
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
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800'
           '&family=Geist+Mono:wght@400;500&display=swap">\n'
           # Iconos Phosphor (MIT), versión fija y con Subresource Integrity
           '<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" '
           'integrity="sha384-6p9AefaqUhEVheRlj1mpAkbngHXy9mbYMrIdcIt4Jlc9lOLIablJq3bBsLOjGwZ7" crossorigin="anonymous">\n'
           '<link rel="stylesheet" href="assets/styles.css">')

# Orden único de los proyectos: de aquí salen la numeración, el menú, el pie y los enlaces anterior/siguiente
def proyectos():
    return [
        ("clima.html", t("Turismo, calor y agua", "Tourism, heat and water"), t("Pipeline, SQL por capas y estadística", "Pipeline, layered SQL and statistics")),
        ("mallorca.html", t("Vista al mar en Mallorca", "Sea view in Mallorca"), t("pandas, SQL, regresión y consola", "pandas, SQL, regression and console")),
        ("dashboard.html", t("Dashboard de mercado", "Market dashboard"), t("KPIs, filtros y filtrado cruzado", "KPIs, filters and cross-filtering")),
        ("caso-churn.html", t("Churn por ROI", "Churn by ROI"), "Customer Success · BigQuery"),
        ("caso-cuadre.html", t("Dashboard ×2", "Dashboard ×2"), t("Gobierno y calidad del dato", "Data governance and quality")),
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
        return f'<a class="lang-btn" href="en/{ruta}" hreflang="en" lang="en" aria-label="Read this page in English"><i class="ph ph-translate" aria-hidden="true"></i>EN</a>'
    return f'<a class="lang-btn" href="../{ruta}" hreflang="es" lang="es" aria-label="Leer esta página en español"><i class="ph ph-translate" aria-hidden="true"></i>ES</a>'


def cabecera(fichero: str) -> str:
    activa = next((m for f, _, _, m in PAGINAS if f == fichero), "")   # la 404 no marca ninguna entrada
    cur = lambda f: " aria-current=page" if f == activa else ""
    panel = "".join(f'<a href="{h}"><b>{num(h)} · {ti}</b><small>{d}</small></a>' for h, ti, d in proyectos())
    menu = (f'<a href="index.html"{cur("index.html")}>{t("Inicio", "Home")}</a>'
            f'<div class="dd"><a href="proyectos.html"{cur("proyectos.html")}>{t("Proyectos", "Projects")}</a>'
            f'<button class="dd-btn" type="button" aria-expanded="false" aria-controls="ddp" aria-label="{t("Ver la lista de proyectos", "Show the list of projects")}"><i class="ph ph-caret-down" aria-hidden="true"></i></button>'
            f'<div class="dd-panel" id="ddp">{panel}<a class="all" href="proyectos.html">{t("Todos los proyectos, con filtros", "All projects, with filters")}<i class="ph ph-arrow-right" aria-hidden="true"></i></a></div></div>'
            f'<a href="habilidades.html"{cur("habilidades.html")}>{t("Habilidades", "Skills")}</a>'
            f'<a href="cv.html"{cur("cv.html")}>CV</a>')
    progreso = '<span class="progress" aria-hidden="true"></span>' if fichero != "index.html" else ""
    return (f'<header class="site-head"><div class="bar">'
            f'<a class="brand" href="index.html" aria-label="{t("Matteo Eiras, inicio", "Matteo Eiras, home")}"><b>Matteo Eiras</b><span>Data &amp; Performance Analyst</span></a>'
            f'<nav class="menu" id="menu" aria-label="{t("Principal", "Main")}">{menu}</nav>'
            f'<div class="head-tools">{selector_idioma(fichero)}'
            f'<button class="icon-btn" id="themeBtn" type="button" aria-label="{t("Cambiar tema", "Switch theme")}"><i class="ph ph-moon theme-moon" aria-hidden="true"></i><i class="ph ph-sun theme-sun" aria-hidden="true"></i></button>'
            f'<a class="btn sm head-cta" href="index.html#contacto">{t("Contactar", "Contact")}</a>'
            f'<button class="icon-btn burger" id="burger" type="button" aria-label="{t("Menú", "Menu")}" aria-expanded="false" aria-controls="menu"><i class="ph ph-list" aria-hidden="true"></i></button></div>'
            f'{progreso}</div></header>')


# Tarjetas de proyectos: una sola lista para el inicio y la página de proyectos.
# Cada tarjeta lleva una captura real de la propia página (assets/img/proy/, una por idioma).
def casos():
    return [
        ("clima.html", t("Datos públicos · pipeline", "Public data · pipeline"), "publico sql python interactivo",
         t("Turismo, calor y agua en Mallorca", "Tourism, heat and water in Mallorca"),
         t("Cuatro fuentes oficiales, SQL por capas con tests y una prueba de homogeneidad: Palma se calienta casi el doble que el planeta.",
           "Four official sources, layered SQL with tests and a homogeneity test: Palma is warming almost twice as fast as the planet.")),
        ("mallorca.html", t("Python · SQL · regresión", "Python · SQL · regression"), "publico sql python interactivo",
         t("¿Cuánto vale una vista al mar?", "What is a sea view worth?"),
         t("14.817 anuncios reales, 8 consultas SQL cuadradas y consola SQL en el navegador.",
           "14,817 real listings, 8 reconciled SQL queries and a SQL console in the browser.")),
        ("dashboard.html", t("Dashboard · BI", "Dashboard · BI"), "publico interactivo",
         t("Mercado vacacional de Mallorca", "Mallorca holiday rental market"),
         t("KPIs frente al total, filtrado cruzado desde el mapa y exportación a CSV, como en Looker Studio.",
           "KPIs against the total, cross-filtering from the map and CSV export, as in Looker Studio.")),
        ("caso-churn.html", "BigQuery · Customer Success", "profesional sql", t("Churn por ROI", "Churn by ROI"),
         t("Qué hoteles no recuperan su cuota mensual, y por qué, antes de que pidan la baja.",
           "Which hotels do not earn back their monthly fee, and why, before they cancel.")),
        ("caso-cuadre.html", "BigQuery · BI", "profesional sql", t("El dashboard que contaba el doble", "The dashboard that counted double"),
         t("Diagnóstico de un sobreconteo frente al informe oficial y una definición por métrica.",
           "Diagnosing an overcount against the official report, with one definition per metric.")),
    ]


assert [c[0] for c in casos()] == [p[0] for p in proyectos()]
DESTACADOS = ["clima.html", "mallorca.html", "dashboard.html", "caso-churn.html", "caso-cuadre.html"]   # bento del inicio
TINTES = {"mallorca.html": " tint-a", "dashboard.html": " tint-b", "caso-cuadre.html": " tint-a"}


def captura(h: str) -> str:
    nombre = h.replace(".html", "") + ".jpg"
    return "assets/img/proy/" + ("en-" if L == "en" else "") + nombre


def tarjetas(destacados: bool = False) -> str:
    lista = casos()
    if destacados:
        lista = [next(c for c in lista if c[0] == h) for h in DESTACADOS]
    return f'<div class="cases{" bento" if destacados else ""}">' + "".join(
        f'<a class="case{TINTES.get(h, "")}" href="{h}" data-cat="{cat}" data-reveal style="--i:{i % 3}">'
        f'<div class="shot"><img src="{captura(h)}" alt="" loading="lazy" decoding="async" width="1280" height="800"></div>'
        f'<div class="meta"><span class="cat">{num(h)} · {c}</span><h3>{ti}</h3><p>{d}</p>'
        f'<span class="go" aria-hidden="true"><i class="ph ph-arrow-right"></i></span></div></a>'
        for i, (h, c, cat, ti, d) in enumerate(lista)) + "</div>"


def filtros() -> str:
    """Chips de la página de proyectos con el recuento calculado, no escrito a mano."""
    C = casos()
    cats = [("todos", t("Todos", "All")), ("publico", t("Datos públicos", "Public data")),
            ("profesional", t("Casos profesionales", "Work cases")), ("sql", "SQL"), ("python", "Python"),
            ("interactivo", t("Interactivo", "Interactive"))]
    n = lambda k: len(C) if k == "todos" else sum(k in c[2].split() for c in C)
    return (f'<div class="chips seg has-pill" role="group" aria-label="{t("Filtrar proyectos", "Filter projects")}"><span class="seg-pill" aria-hidden="true"></span>' + "".join(
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
        (t("Turismo, calor y agua", "Tourism, heat and water"),
         [("clima.html#resumen", t("Resumen", "Summary")), ("clima.html#datos", t("Datos y pipeline", "Data and pipeline")),
          ("clima.html#sql", t("SQL por capas", "Layered SQL")), ("clima.html#calor", t("Calor", "Heat")),
          ("clima.html#turismo", t("Turismo", "Tourism")), ("clima.html#agua", t("Agua", "Water")),
          ("clima.html#explorar", t("Explorar por año", "Explore by year"))]),
        (t("Proyecto vista al mar", "Sea view project"),
         [("mallorca.html#datos", t("Datos y calidad", "Data and quality")), ("mallorca.html#python", t("Python y pandas", "Python and pandas")),
          ("mallorca.html#sql", t("SQL y consola", "SQL and console")), ("mallorca.html#modelo", t("Modelo y simulador", "Model and simulator")),
          ("mallorca.html#hallazgos", t("Hallazgos y mapa", "Findings and map")), ("mallorca.html#conclusiones", t("Conclusiones", "Conclusions"))]),
        (t("Habilidades", "Skills"),
         [("habilidades.html#datos", t("Datos y análisis", "Data and analysis")), ("habilidades.html#negocio", t("Negocio y técnica", "Business and tech")),
          ("habilidades.html#mercado", t("Lo que pide el mercado", "What the market asks for")),
          ("habilidades.html#metodo", t("Cómo trabajo", "How I work")), ("habilidades.html#formacion", t("Formación", "Education")),
          ("habilidades.html#portal", t("Este portal y auditoría", "This portfolio and audit"))]),
        (t("Sobre mí", "About me"),
         [("index.html#sobre-mi", t("Sobre mí", "About me")), ("index.html#trayectoria", t("Trayectoria", "Experience")),
          ("index.html#habilidades", t("Habilidades", "Skills")), ("cv.html", "CV"), ("index.html#contacto", t("Contacto", "Contact")), ("cv.html#contacto", "Email"),
          (LINKEDIN, "LinkedIn")]),
    ]
    return (f'<footer class="site-foot"><div class="wrap"><nav class="sitemap" aria-label="{t("Mapa del sitio", "Site map")}">'
            + "".join(f'<div><h2>{g}</h2>' + "".join(
                f'<a href="{h}"{" rel=\"noopener noreferrer\"" if h.startswith("http") else ""}>{ti}</a>' for h, ti in ls) + "</div>"
                      for g, ls in mapa)
            + f'</nav><div class="foot-meta"><span>Matteo Eiras Pé, Palma de Mallorca</span>'
              f'<span>{t("Datos del proyecto", "Project data")}: Inside Airbnb (CC BY 4.0)</span></div>'
              '</div></footer>')


def scripts(fichero: str) -> str:
    s = '<script src="assets/datos.js"></script>\n<script src="assets/app.js"></script>'
    if fichero == "mallorca.html":     # consola SQL y simulador
        s += '\n<script src="assets/interactivo.js"></script>'
    if fichero == "dashboard.html":    # filas por anuncio y cubos, solo donde hacen falta
        s += '\n<script src="assets/dashboard-datos.js"></script>'
    if fichero == "dashboard.html":
        s += '\n<script src="assets/vista.js"></script>'
    if fichero in ("clima.html", "habilidades.html"):   # gráficos del proyecto de clima y del mercado
        s += '\n<script src="assets/clima.js"></script>'
    return s


def mercado() -> str:
    """Skills más pedidas en la muestra de ofertas y dónde se demuestran en el portafolio."""
    m = json.loads((RAIZ / "proyecto_mercado" / "mercado.json").read_text(encoding="utf-8"))
    donde = {
        "SQL": [("clima.html#sql", t("SQL por capas", "Layered SQL")), ("mallorca.html#sql", t("8 consultas", "8 queries"))],
        "Comunicación y storytelling": [("clima.html#resumen", t("Resumen ejecutivo", "Executive summary"))],
        "Stakeholders / negocio": [("caso-churn.html", "Churn por ROI" if L == "es" else "Churn by ROI")],
        "Alguna herramienta BI (Tableau, Looker, Power BI)": [("cv.html", t("Looker Studio a diario", "Looker Studio daily")), ("dashboard.html", "Dashboard")],
        "Python": [("clima.html#datos", t("Pipeline de ingesta", "Ingestion pipeline")), ("mallorca.html#python", "pandas")],
        "Dashboards": [("dashboard.html", t("Dashboard de mercado", "Market dashboard")), ("clima.html#explorar", t("Explorador", "Explorer"))],
        "Algún almacén cloud (BigQuery, Snowflake, Redshift, Databricks)": [("caso-cuadre.html", t("BigQuery a diario", "BigQuery daily"))],
        "A/B testing": [],
        "Excel / Sheets": [("cv.html", t("Uso diario", "Daily use"))],
        "Estadística": [("clima.html#calor", t("Tendencias e IC", "Trends and CIs")), ("mallorca.html#modelo", t("Regresión", "Regression"))],
        "Modelado de datos": [("clima.html#sql", t("Staging, intermedio y marts", "Staging, intermediate and marts"))],
        "dbt": [("clima.html#sql", t("Mismo patrón, en SQLite", "Same pattern, in SQLite"))],
    }
    nombres_en = {"Comunicación y storytelling": "Communication and storytelling", "Stakeholders / negocio": "Stakeholders / business",
                  "Alguna herramienta BI (Tableau, Looker, Power BI)": "Any BI tool (Tableau, Looker, Power BI)",
                  "Algún almacén cloud (BigQuery, Snowflake, Redshift, Databricks)": "Any cloud warehouse (BigQuery, Snowflake, Redshift, Databricks)",
                  "Estadística": "Statistics", "Modelado de datos": "Data modelling"}
    filas = [s for s in m["todas"]["skills"] if s["skill"] in donde][:12]
    cuerpo_t = "".join(
        f'<tr><th scope="row">{nombres_en.get(s["skill"], s["skill"]) if L == "en" else s["skill"]}</th>'
        f'<td class="num"><span class="inbar" style="--w:{s["pct"]:.0f}%" aria-hidden="true"></span>{s["pct"]:.0f}{"%" if L == "en" else " %"}</td>'
        f'<td>{" · ".join(f"<a href=\"{h}\">{x}</a>" for h, x in donde[s["skill"]]) or "<span class=\"muted\">" + t("Aún no está en el portafolio", "Not in the portfolio yet") + "</span>"}</td></tr>'
        for s in filas)
    return (f'<div class="scroll"><table class="vz-nice mercado"><thead><tr><th scope="col">Skill</th><th scope="col" class="num">'
            f'{t("Ofertas que la piden", "Postings asking for it")}</th><th scope="col">{t("Dónde la demuestro", "Where I show it")}</th></tr></thead>'
            f'<tbody>{cuerpo_t}</tbody></table></div>'
            f'<p class="muted small">{t("Muestra", "Sample")}: {m["todas"]["n"]} {t("puestos de análisis distintos entre", "distinct analysis roles out of")} '
            f'{m["ofertas_totales"]:,} {t("ofertas abiertas de", "open postings at")} {m["empresas"]} '
            f'{t("empresas europeas de viajes y tecnología, leídas el", "European travel and tech companies, read on")} {m["fecha"]} '
            f'{t("desde sus APIs públicas de empleo (Greenhouse, Ashby y Lever).", "from their public job APIs (Greenhouse, Ashby and Lever).")}</p>'
            ).replace(f"{m['ofertas_totales']:,}", f"{m['ofertas_totales']:,}".replace(",", "." if L == "es" else ","))


def cuerpo(fichero: str) -> str:
    carpeta = SRC / ("pages_en" if L == "en" else "pages")
    contenido = (carpeta / fichero).read_text(encoding="utf-8")
    contenido = contenido.replace('rel="noopener"', 'rel="noopener noreferrer"')
    contenido = (contenido.replace("<!--CASOS_INICIO-->", tarjetas(destacados=True)).replace("<!--CASOS-->", tarjetas())
                 .replace("<!--RECORTE-->", recorte())
                 .replace("<!--FILTROS-->", filtros()).replace("<!--PREVNEXT-->", prevnext(fichero))
                 .replace("<!--MERCADO-->", mercado() if "<!--MERCADO-->" in contenido else ""))
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
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com; font-src https://fonts.gstatic.com https://unpkg.com; "
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
    elif fichero in ("clima.html", "mallorca.html", "dashboard.html"):
        titulo = meta_pagina(fichero)[0].split(" | ")[0]
        base = dataset if fichero != "clima.html" else [
            {"@type": "Dataset", "name": "INE, Encuesta de Ocupación Hotelera", "url": "https://www.ine.es/"},
            {"@type": "Dataset", "name": "NOAA GHCN-Daily", "url": "https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily"},
            {"@type": "Dataset", "name": "NASA GISTEMP v4", "url": "https://data.giss.nasa.gov/gistemp/"},
            {"@type": "Dataset", "name": "Govern de les Illes Balears, reserves hídriques", "url": "https://www.caib.es/sites/aigua/"}]
        grafo = [{"@type": "Article", "headline": titulo, "inLanguage": L, "url": url_de(fichero, L),
                  "image": BASE_URL + "assets/img/retrato.jpg", "author": autor, "isBasedOn": base}]
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
            '<meta name="theme-color" content="#ffffff">\n'
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
for f in ("styles.css", "app.js", "interactivo.js", "vista.js", "clima.js", "tema.js", "favicon.svg"):
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
datos["clima"] = json.loads((RAIZ / "proyecto_clima" / "resultados.json").read_text(encoding="utf-8"))
datos["mercado"] = {k: v for k, v in json.loads((RAIZ / "proyecto_mercado" / "mercado.json").read_text(encoding="utf-8")).items() if k != "muestra"}
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
for viejo in ("casos.html", "pandas.html", "visualizacion.html", "caso-funnel.html", "caso-facturacion.html"):   # retiradas
    (OUT / viejo).unlink(missing_ok=True)
    (OUT / "en" / viejo).unlink(missing_ok=True)


# ------------------------------------------------------------------ versión de los assets
# Un sufijo ?v=<hash> por fichero obliga al navegador a descargar la versión nueva tras cada cambio.
def version(nombre: str) -> str:
    return hashlib.sha1((OUT / "assets" / nombre).read_bytes()).hexdigest()[:8]


VERSIONES = {n: version(n) for n in ("styles.css", "app.js", "interactivo.js", "vista.js", "clima.js", "tema.js", "datos.js", "dashboard-datos.js")}


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
prioridad = {"index.html": "1.0", "clima.html": "0.9", "mallorca.html": "0.9", "cv.html": "0.9", "proyectos.html": "0.8", "dashboard.html": "0.8"}
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

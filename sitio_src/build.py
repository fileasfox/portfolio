"""
Genera el portal de proyectos a partir de las páginas de pages/ y los resultados del análisis.

Uso:
    python sitio_src/build.py

Salidas:
    sitio/                 web completa para GitHub Pages (4 páginas + assets/)
    portfolio.html         página de inicio para publicar como Artifact (sin <html>/<head>)
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent
RAIZ = SRC.parent
DATOS = RAIZ / "proyecto_airbnb"
OUT = RAIZ / "sitio"

PAGINAS = [
    # fichero, título (unos 60 caracteres), descripción para buscadores (unos 150), entrada de menú
    ("index.html", "Matteo Eiras Pé | Data Analyst en hospitality tech, Palma",
     "Data & Performance Analyst en Palma de Mallorca: SQL, BigQuery y Looker Studio aplicados a hoteles. Trayectoria, proyectos con datos reales y contacto.", "index.html"),
    ("proyectos.html", "Proyectos de análisis de datos | Matteo Eiras Pé",
     "Proyectos de data analytics: pricing de alquiler vacacional en Mallorca con Python y SQL, y casos reales de churn, BI y calidad del dato en un SaaS hotelero.", "proyectos.html"),
    ("mallorca.html", "¿Cuánto vale una vista al mar en Mallorca? | Proyecto de datos",
     "Análisis de 14.817 anuncios de Airbnb en Mallorca con pandas, SQL y regresión: la vista al mar suma un 27 % al precio. Con consola SQL y simulador interactivo.", "proyectos.html"),
    ("dashboard.html", "Dashboard interactivo del alquiler vacacional en Mallorca",
     "Dashboard de mercado con datos reales de Mallorca: KPIs frente al total, filtros, filtrado cruzado desde el mapa, ocupación, precios y exportación a CSV.", "proyectos.html"),
    ("pandas.html", "Cuaderno de pandas con datos reales | Python para análisis",
     "Once celdas de pandas ejecutadas sobre 5,9 millones de filas de Inside Airbnb: carga tipada, limpieza, groupby, pivot, merge, series temporales y cuadre con SQL.", "proyectos.html"),
    ("visualizacion.html", "Cómo presento los datos: antes y después | Visualización",
     "Gráficos habituales frente a su versión corregida con datos reales: tartas, ejes truncados, medias engañosas, doble eje y color. Más un informe de una página.", "proyectos.html"),
    ("caso-churn.html", "Churn por ROI en un SaaS hotelero | Caso de análisis",
     "Cómo medir la salud de cuenta de cada hotel con su ROI mensual en BigQuery y Looker Studio para anticipar bajas. Caso real anonimizado de Customer Success.", "proyectos.html"),
    ("caso-cuadre.html", "Un dashboard que contaba el doble | Caso de BI",
     "Diagnóstico de un sobreconteo de 2,2 veces frente al informe oficial y rediseño de la vista en BigQuery. Una definición por métrica. Caso real anonimizado.", "proyectos.html"),
    ("caso-funnel.html", "Funnel de invitaciones y alertas de integración | Caso",
     "Funnel de reservas importadas a solicitudes y alertas que separan una caída comercial de un fallo del conector con PMS o motor de reservas. Caso anonimizado.", "proyectos.html"),
    ("caso-facturacion.html", "Limpieza reproducible de datos con Python | Caso",
     "De una hoja de facturación mantenida a mano a un proceso en Python con normalización, validación de claves y log de cambios. Caso real anonimizado.", "proyectos.html"),
    ("habilidades.html", "Habilidades: SQL, BigQuery, Looker Studio y Python | Matteo Eiras",
     "Habilidades de data analyst con enlace a dónde se demuestran: SQL, BigQuery, Looker Studio, Python, integraciones API y web analytics con Google Tag Manager.", "habilidades.html"),
    ("cv.html", "CV de Matteo Eiras Pé | Data & Performance Analyst",
     "Curriculum de Matteo Eiras Pé: Performance Manager en Hotelverse, grado en Turismo por la UIB, SQL, BigQuery y Looker Studio. Español, catalán, italiano e inglés C1.", "cv.html"),
]
MENU = [("index.html", "Inicio"), ("proyectos.html", "Proyectos"), ("habilidades.html", "Habilidades"), ("cv.html", "CV")]

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

# Desplegable de Proyectos: cualquier proyecto a 1 clic (o al pasar el cursor) desde cualquier página
# Orden único de los proyectos: de aquí salen la numeración, el menú, el pie y los enlaces anterior/siguiente
PROYECTOS = [
    ("mallorca.html", "Vista al mar en Mallorca", "pandas, SQL, regresión y consola"),
    ("dashboard.html", "Dashboard de mercado", "KPIs, filtros y filtrado cruzado"),
    ("pandas.html", "Cuaderno de pandas", "11 celdas con su salida real"),
    ("visualizacion.html", "Cómo presento los datos", "Antes y después, informe ejecutivo"),
    ("caso-churn.html", "Churn por ROI", "Customer Success · BigQuery"),
    ("caso-cuadre.html", "Dashboard ×2", "Cuadre de métricas"),
    ("caso-funnel.html", "Funnel e integraciones", "Alertas de conectores"),
    ("caso-facturacion.html", "Limpieza de facturación", "Python · data quality"),
    ("habilidades.html#portal", "Este portal", "Desarrollo web y auditoría"),
]
num = lambda h: f"{[p[0] for p in PROYECTOS].index(h) + 1:02d}"
PROYECTOS_MENU = [(h, f"{num(h)} · {t}", d) for h, t, d in PROYECTOS]


def prevnext(fichero: str) -> str:
    hrefs = [p[0] for p in PROYECTOS]
    if fichero not in hrefs:
        return ""
    i = hrefs.index(fichero)
    enlace = lambda j, cls, rotulo: (f'<a{cls} href="{PROYECTOS[j][0]}"><span>{rotulo}</span>'
                                     f'<b>{num(PROYECTOS[j][0])} · {PROYECTOS[j][1]}</b></a>')
    return ('<nav class="prevnext" aria-label="Otros proyectos">'
            + (enlace(i - 1, "", "← Anterior") if i > 0 else "<span></span>")
            + (enlace(i + 1, ' class="next"', "Siguiente →") if i + 1 < len(PROYECTOS) else "")
            + "</nav>")


def cabecera(fichero: str) -> str:
    activa = next((m for f, _, _, m in PAGINAS if f == fichero), "")   # la 404 no marca ninguna entrada
    cur = lambda f: " aria-current=page" if f == activa else ""
    panel = "".join(f'<a href="{h}"><b>{t}</b><small>{d}</small></a>' for h, t, d in PROYECTOS_MENU)
    menu = (f'<a href="index.html"{cur("index.html")}>Inicio</a>'
            f'<div class="dd"><a href="proyectos.html"{cur("proyectos.html")}>Proyectos</a>'
            f'<button class="dd-btn" type="button" aria-expanded="false" aria-controls="ddp" aria-label="Ver la lista de proyectos">{ICONO_FLECHA}</button>'
            f'<div class="dd-panel" id="ddp">{panel}<a class="all" href="proyectos.html">Todos los proyectos con filtros →</a></div></div>'
            f'<a href="habilidades.html"{cur("habilidades.html")}>Habilidades</a>'
            f'<a href="cv.html"{cur("cv.html")}>CV</a>')
    progreso = '<span class="progress" aria-hidden="true"></span>' if fichero != "index.html" else ""
    # Franja superior negra (referencia GAZU) y barra con menú a la izquierda, marca centrada y herramientas a la derecha
    return ('<div class="topbar"><div class="wrap"><span class="avail"><i aria-hidden="true"></i>Abierto a nuevos retos</span>'
            '<nav aria-label="Enlaces rápidos"><a href="cv.html">CV</a>'
            '<a href="https://www.linkedin.com/in/matteo-eiras-p%C3%A9-2b34931b9/" rel="noopener noreferrer">LinkedIn</a></nav></div></div>'
            f'<header class="site-head"><div class="bar">'
            f'<nav class="menu" id="menu" aria-label="Principal">{menu}</nav>'
            f'<a class="brand" href="index.html" aria-label="Matteo Eiras, inicio">Eiras<span class="dot">.</span></a>'
            f'<div class="head-tools"><button class="icon-btn" id="themeBtn" type="button" aria-label="Cambiar tema">{ICONO_TEMA}</button>'
            f'<button class="icon-btn burger" id="burger" type="button" aria-label="Menú" aria-expanded="false" aria-controls="menu">{ICONO_MENU}</button></div>'
            f'{progreso}</div></header>')


# Tarjetas de proyectos: una sola lista para el inicio y la página de proyectos.
# Cada tarjeta lleva arriba una visual hecha con sus propios datos, en lugar de una foto.
CASOS = [
    ("mallorca.html", "Datos públicos", "publico sql python interactivo", "¿Cuánto vale una vista al mar?",
     "pandas, 8 consultas SQL cuadradas y una regresión, con consola SQL en el navegador.",
     '<div class="v-map"><svg data-minimap role="img" aria-label="Mallorca coloreada por precio mediano"></svg></div>'),
    ("dashboard.html", "Dashboard", "publico interactivo", "Dashboard del mercado vacacional",
     "KPIs frente al total, filtros y filtrado cruzado desde el mapa, como en Looker Studio.",
     '<div class="v-dash"><span class="k"><b>398 €</b><small>precio</small></span><span class="k"><b>50 %</b><small>noches no disp.</small></span>'
     '<span class="spark"><i style="--h:92%"></i><i style="--h:89%"></i><i style="--h:67%"></i><i style="--h:50%"></i><i style="--h:54%"></i>'
     '<i style="--h:61%"></i><i style="--h:67%"></i><i style="--h:66%"></i><i style="--h:61%"></i><i style="--h:54%"></i><i style="--h:55%"></i><i style="--h:55%"></i></span></div>'),
    ("pandas.html", "Python", "publico python", "Cuaderno de pandas",
     "Once celdas ejecutadas sobre 5,9 millones de filas: limpieza, groupby, merge y cuadre con SQL.",
     '<div class="v-code">df.groupby("municipio")<br>&nbsp;&nbsp;.agg(precio=("precio", "median"))<br><b>→ 53 filas</b><br><b>→ cuadra con SQL</b></div>'),
    ("visualizacion.html", "Visualización", "publico interactivo", "Cómo presento los datos",
     "Seis gráficos habituales frente a su versión corregida, y un informe de una página.",
     '<div class="v-viz"><span class="pie" aria-hidden="true"></span><span class="arrow">→</span>'
     '<span class="bars"><i style="--w:100%"></i><i style="--w:60%"></i><i style="--w:44%"></i><i style="--w:30%"></i></span></div>'),
    ("caso-churn.html", "Customer Success", "profesional sql", "Salud de cuenta y churn por ROI",
     "Qué hoteles no recuperan su cuota mensual, y por qué, antes de que pidan la baja.",
     '<div class="v-roi"><div class="v-num">&lt;&nbsp;1<em>×</em><small>umbral de riesgo</small></div>'
     '<div class="scale"><i></i><i></i><i></i></div><div class="ticks"><span>Riesgo</span><span>1×</span><span>2×</span></div></div>'),
    ("caso-cuadre.html", "BI governance", "profesional sql", "El dashboard que contaba el doble",
     "Diagnóstico de un sobreconteo frente al informe oficial y rediseño de la vista.",
     '<div class="v-num"><s>2,2×</s><br>1,0<em>×</em><small>cuadrado con el oficial</small></div>'),
    ("caso-funnel.html", "Observabilidad", "profesional sql", "Funnel e integraciones",
     "Alertas que separan una caída comercial de un fallo del conector.",
     '<div class="v-bars"><i style="--w:100%"></i><i style="--w:82%"></i><i style="--w:49%"></i><i style="--w:17%"></i><i style="--w:13%"></i><i style="--w:8%"></i></div>'),
    ("caso-facturacion.html", "Calidad del dato", "profesional python", "Limpieza de facturación",
     "Una hoja manual convertida en un proceso reproducible con log de cambios.",
     '<div class="v-code">"Synxis"<br>"SYNXIS"<br>"1.234,50"<br><b>→ SynXis</b><br><b>→ 1234.50</b></div>'),
    ("habilidades.html#portal", "Desarrollo web", "python interactivo", "Este portal",
     "Generado con Python, sin frameworks, con consola SQL y auditoría antes de publicar.",
     '<div class="v-num">23<em>/</em>23<small>controles superados</small></div>'),
]
assert [c[0] for c in CASOS] == [p[0] for p in PROYECTOS]


def tarjetas() -> str:
    return '<div class="cases">' + "".join(
        f'<a class="case" href="{h}" data-cat="{cat}"><div class="visual"><span class="idx">{num(h)}</span><span class="cat">{c}</span>{v}</div>'
        f'<div class="meta"><h3>{t}</h3><p>{d}</p><span class="go">Ver {"caso" if h.startswith("caso-") else "proyecto"} <span aria-hidden="true">→</span></span></div></a>'
        for h, c, cat, t, d, v in CASOS) + "</div>"


def filtros() -> str:
    """Chips de la página de proyectos con el recuento calculado, no escrito a mano."""
    cats = [("todos", "Todos"), ("publico", "Datos públicos"), ("profesional", "Casos profesionales"),
            ("sql", "SQL"), ("python", "Python"), ("interactivo", "Interactivo")]
    n = lambda k: len(CASOS) if k == "todos" else sum(k in c[2].split() for c in CASOS)
    return ('<div class="chips" role="group" aria-label="Filtrar proyectos">' + "".join(
        f'<button class="chip" type="button" data-filter="{k}" aria-pressed="{str(k == "todos").lower()}">{t}<span>{n(k)}</span></button>'
        for k, t in cats) + "</div>")


def recorte() -> str:
    """Retrato recortado opcional: si existe assets/img/recorte.webp (o .png), se coloca delante del apellido."""
    for ext in ("webp", "png"):
        if (SRC / "assets" / "img" / f"recorte.{ext}").exists():
            return f'<img class="cutout" src="assets/img/recorte.{ext}" alt="" aria-hidden="true">'
    return ""


# Pie con mapa del sitio: cualquier sección de la web a 1 clic desde cualquier página
SITEMAP = [
    ("Proyectos", [("proyectos.html", "Todos los proyectos")] + [(h, t.split(" · ", 1)[1]) for h, t, _ in PROYECTOS_MENU]),
    ("Proyecto Mallorca", [("mallorca.html#datos", "Datos y calidad"), ("mallorca.html#python", "Python y pandas"),
                           ("mallorca.html#sql", "SQL y consola"), ("mallorca.html#modelo", "Modelo y simulador"),
                           ("mallorca.html#hallazgos", "Hallazgos y mapa"), ("mallorca.html#conclusiones", "Conclusiones")]),
    ("Habilidades", [("habilidades.html#datos", "Datos y análisis"), ("habilidades.html#negocio", "Negocio y técnica"),
                     ("habilidades.html#metodo", "Cómo trabajo"), ("habilidades.html#formacion", "Formación"),
                     ("habilidades.html#portal", "Este portal y auditoría")]),
    ("Sobre mí", [("index.html#sobre-mi", "Sobre mí"), ("index.html#trayectoria", "Trayectoria"), ("index.html#habilidades", "Habilidades"), ("cv.html", "CV"), ("index.html#contacto", "Contacto"),
                  ("https://www.linkedin.com/in/matteo-eiras-p%C3%A9-2b34931b9/", "LinkedIn")]),
]
PIE = ('<footer class="site-foot"><div class="wrap"><nav class="sitemap" aria-label="Mapa del sitio">'
       + "".join(f'<div><h2>{g}</h2>' + "".join(
           f'<a href="{h}"{" rel=\"noopener noreferrer\"" if h.startswith("http") else ""}>{t}</a>' for h, t in ls) + "</div>"
                 for g, ls in SITEMAP)
       + '</nav><div class="foot-meta"><span>Matteo Eiras Pé, Palma de Mallorca</span>'
         '<span>Datos del proyecto: Inside Airbnb (CC BY 4.0)</span></div>'
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
    from html import escape
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
        segundos = f"{x['segundos']:.1f}".replace(".", ",")
        partes.append(
            f'<article class="nb-cell" id="celda-{x["n"]}"><div class="nb-head"><span class="nb-n">[{x["n"]}]</span>'
            f'<div><h3>{escape(x["titulo"])}</h3><p>{escape(x["explicacion"])}</p></div></div>'
            f'<template data-code="py" data-label="cuaderno.py · celda {x["n"]}">{escape(x["codigo"], quote=False)}</template>'
            f'<div class="nb-out" aria-label="Salida de la celda {x["n"]}"><span class="nb-lbl">Salida · {segundos} s</span>{salida}</div></article>')
    return "".join(partes)


def cuerpo(fichero: str) -> str:
    contenido = (SRC / "pages" / fichero).read_text(encoding="utf-8")
    contenido = contenido.replace('rel="noopener"', 'rel="noopener noreferrer"')
    contenido = (contenido.replace("<!--CASOS-->", tarjetas()).replace("<!--RECORTE-->", recorte())
                 .replace("<!--FILTROS-->", filtros()).replace("<!--PREVNEXT-->", prevnext(fichero))
                 .replace("<!--CUADERNO-->", cuaderno() if "<!--CUADERNO-->" in contenido else ""))
    # Cifra y unidad nunca se separan de línea ("19 %", "262 €"); el código de las plantillas no se toca
    partes = re.split(r"(<template[\s\S]*?</template>)", contenido)
    contenido = "".join(p if p.startswith("<template") else re.sub(r"(\d) ([%€×])", "\\1&nbsp;\\2", p) for p in partes)
    return (f'<a class="skip" href="#contenido">Saltar al contenido</a>\n{cabecera(fichero)}\n'
            # El inicio gestiona sus propios anchos (bandas a sangre); el resto va en el contenedor
            f'<main{"" if fichero == "index.html" else " class=" + chr(34) + "wrap" + chr(34)} id="contenido" tabindex="-1">\n'
            f'{contenido}\n</main>\n{PIE}\n{scripts(fichero)}')


# Política de seguridad para la versión pública (GitHub Pages): solo scripts propios y de cdnjs,
# sin plugins, sin formularios hacia fuera y sin enviar la URL completa a otros sitios.
CSP = ("default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; "
       "upgrade-insecure-requests")
SEGURIDAD = (f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
             '<meta name="referrer" content="strict-origin-when-cross-origin">\n')


# Favicon, color de la barra del navegador y tarjeta para compartir en redes
BASE_URL = "https://fileasfox.github.io/portfolio/"
LINKEDIN = "https://www.linkedin.com/in/matteo-eiras-p%C3%A9-2b34931b9/"


def datos_estructurados(fichero: str) -> str:
    """JSON-LD para Google: la persona en el inicio y el CV; el estudio en la página del proyecto."""
    persona = {
        "@type": "Person", "@id": BASE_URL + "#persona", "name": "Matteo Eiras Pé", "url": BASE_URL,
        "image": BASE_URL + "assets/img/retrato.jpg", "jobTitle": "Data & Performance Analyst",
        "worksFor": {"@type": "Organization", "name": "Hotelverse", "url": "https://hotelverse.tech"},
        "address": {"@type": "PostalAddress", "addressLocality": "Palma de Mallorca", "addressRegion": "Islas Baleares", "addressCountry": "ES"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "Universitat de les Illes Balears"},
        "knowsLanguage": ["es", "ca", "it", "en", "de"],
        "knowsAbout": ["Análisis de datos", "SQL", "BigQuery", "Looker Studio", "Python", "pandas", "Business Intelligence",
                       "Customer Success", "Hospitality tech", "Distribución hotelera", "Google Tag Manager"],
        "sameAs": [LINKEDIN, "https://github.com/fileasfox"],
    }
    if fichero in ("index.html", "cv.html"):
        grafo = [persona, {"@type": "WebSite", "@id": BASE_URL + "#web", "url": BASE_URL, "name": "Matteo Eiras Pé, portafolio",
                           "inLanguage": "es", "author": {"@id": BASE_URL + "#persona"}}]
        if fichero == "cv.html":
            grafo.append({"@type": "ProfilePage", "url": BASE_URL + "cv.html", "mainEntity": {"@id": BASE_URL + "#persona"}})
    elif fichero == "mallorca.html":
        grafo = [{"@type": "Article", "headline": "¿Cuánto vale una vista al mar en Mallorca?", "inLanguage": "es",
                  "url": BASE_URL + "mallorca.html", "image": BASE_URL + "assets/img/retrato.jpg",
                  "author": {"@type": "Person", "name": "Matteo Eiras Pé", "url": BASE_URL},
                  "about": ["Alquiler vacacional", "Pricing", "Regresión hedónica", "Mallorca"],
                  "isBasedOn": {"@type": "Dataset", "name": "Inside Airbnb: Mallorca", "url": "https://insideairbnb.com/get-the-data/",
                                "license": "https://creativecommons.org/licenses/by/4.0/"}}]
    elif fichero in ("dashboard.html", "pandas.html", "visualizacion.html"):
        titulo = next(t for f, t, *_ in PAGINAS if f == fichero).split(" | ")[0]
        grafo = [{"@type": "Article", "headline": titulo, "inLanguage": "es", "url": BASE_URL + fichero,
                  "image": BASE_URL + "assets/img/retrato.jpg",
                  "author": {"@type": "Person", "name": "Matteo Eiras Pé", "url": BASE_URL},
                  "isBasedOn": {"@type": "Dataset", "name": "Inside Airbnb: Mallorca", "url": "https://insideairbnb.com/get-the-data/",
                                "license": "https://creativecommons.org/licenses/by/4.0/"}}]
    else:
        return ""
    datos = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{datos}</script>\n'


# Favicon, color de la barra, URL canónica, tarjeta para compartir y datos estructurados
def cabeza_extra(titulo, desc, fichero="index.html"):
    url = BASE_URL if fichero == "index.html" else BASE_URL + fichero
    robots = "noindex" if fichero == "404.html" else "index, follow"
    tipo = "profile" if fichero in ("index.html", "cv.html") else "article"
    return ('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n'
            '<meta name="theme-color" content="#e9e8e4">\n'
            f'<meta name="robots" content="{robots}">\n<meta name="author" content="Matteo Eiras Pé">\n'
            f'<link rel="canonical" href="{url}">\n'
            f'<meta property="og:type" content="{tipo}">\n'
            '<meta property="og:locale" content="es_ES">\n<meta property="og:site_name" content="Matteo Eiras Pé">\n'
            f'<meta property="og:url" content="{url}">\n<meta property="og:title" content="{titulo}">\n'
            f'<meta property="og:description" content="{desc}">\n'
            f'<meta property="og:image" content="{BASE_URL}assets/img/retrato.jpg">\n'
            '<meta property="og:image:width" content="554">\n<meta property="og:image:height" content="693">\n'
            '<meta name="twitter:card" content="summary">\n'
            + datos_estructurados(fichero))


def pagina_completa(fichero, titulo, desc, seguridad=False):
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + (SEGURIDAD if seguridad else "") +
            f'<title>{titulo}</title>\n<meta name="description" content="{desc}">\n' + cabeza_extra(titulo, desc, fichero) + f'{FUENTES}\n</head>\n'
            f'<body>\n{cuerpo(fichero)}\n</body>\n</html>\n')


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


# ------------------------------------------------------------------ páginas
for fichero, titulo, desc, _ in PAGINAS:
    (OUT / fichero).write_text(con_version(pagina_completa(fichero, titulo, desc, seguridad=True)), encoding="utf-8")

(OUT / ".nojekyll").write_text("", encoding="utf-8")   # GitHub Pages sirve los ficheros tal cual, sin Jekyll

# Mapa del sitio para buscadores (enviarlo en Google Search Console) y robots.txt
from datetime import date
hoy = date.today().isoformat()
prioridad = {"index.html": "1.0", "mallorca.html": "0.9", "cv.html": "0.9", "proyectos.html": "0.8",
             "dashboard.html": "0.8", "pandas.html": "0.8", "visualizacion.html": "0.8"}
(OUT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{BASE_URL if f == 'index.html' else BASE_URL + f}</loc><lastmod>{hoy}</lastmod>"
              f"<priority>{prioridad.get(f, '0.6')}</priority></url>\n" for f, *_ in PAGINAS)
    + "</urlset>\n", encoding="utf-8")
(OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8")

# Página 404: GitHub Pages la sirve sola para cualquier ruta inexistente; no entra en el menú
(OUT / "404.html").write_text(con_version(pagina_completa("404.html", "Página no encontrada", "Esta página no existe.", seguridad=True)),
                              encoding="utf-8")

# Copia para el Artifact, sin ?v= (sirve sus ficheros por ruta exacta).
# El inicio va sin <html>/<head>/<body>: el publicador los añade.
_, titulo, desc, _ = PAGINAS[0]
(RAIZ / "portfolio.html").write_text(f"<title>{titulo}</title>\n" + cabeza_extra(titulo, desc, "index.html") +f"{FUENTES}\n{cuerpo('index.html')}\n",
                                     encoding="utf-8")
ART = RAIZ / "artifact"
ART.mkdir(exist_ok=True)
for fichero, titulo_p, desc_p, _ in PAGINAS[1:]:
    (ART / fichero).write_text(pagina_completa(fichero, titulo_p, desc_p), encoding="utf-8")

for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print(f"{p.relative_to(RAIZ)}  {p.stat().st_size // 1024} KB")

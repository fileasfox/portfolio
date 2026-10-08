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
    # fichero, título de la pestaña, descripción, entrada de menú a la que pertenece
    ("index.html", "Matteo Eiras · Data Analyst", "Portafolio de Matteo Eiras, data analyst en hospitality tech.", "index.html"),
    ("proyectos.html", "Proyectos · Matteo Eiras", "Proyectos de datos: pricing en Mallorca y casos reales de un SaaS hotelero.", "proyectos.html"),
    ("mallorca.html", "Vista al mar · Mallorca", "Cuánto vale cada atributo de un alojamiento en Mallorca: pandas, SQL interactivo y regresión con datos reales.", "proyectos.html"),
    ("caso-churn.html", "Churn por ROI", "Caso: salud de cuenta y riesgo de churn por ROI en un SaaS hotelero.", "proyectos.html"),
    ("caso-cuadre.html", "Dashboard ×2", "Caso: un dashboard que contaba el doble y cómo se cuadró con el informe oficial.", "proyectos.html"),
    ("caso-funnel.html", "Funnel e integraciones", "Caso: funnel de invitaciones y alertas de integración con PMS y motores de reservas.", "proyectos.html"),
    ("caso-facturacion.html", "Limpieza de facturación", "Caso: limpieza reproducible de datos de facturación con Python.", "proyectos.html"),
    ("habilidades.html", "Habilidades · Matteo Eiras", "Habilidades de Matteo Eiras con enlaces a dónde se demuestran.", "habilidades.html"),
    ("cv.html", "CV · Matteo Eiras", "Curriculum vitae de Matteo Eiras Pé.", "cv.html"),
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
PROYECTOS_MENU = [
    ("mallorca.html", "01 · Vista al mar en Mallorca", "pandas, SQL, regresión y consola"),
    ("caso-churn.html", "02 · Churn por ROI", "Customer Success · BigQuery"),
    ("caso-cuadre.html", "03 · Dashboard ×2", "Cuadre de métricas"),
    ("caso-funnel.html", "04 · Funnel e integraciones", "Alertas de conectores"),
    ("caso-facturacion.html", "05 · Limpieza de facturación", "Python · data quality"),
    ("habilidades.html#portal", "06 · Este portal", "Desarrollo web y auditoría"),
]


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
    ("mallorca.html", "01", "Datos públicos", "publico sql python interactivo", "¿Cuánto vale una vista al mar?",
     "pandas, 8 consultas SQL cuadradas y una regresión, con consola SQL en el navegador.",
     '<div class="v-map"><svg data-minimap role="img" aria-label="Mallorca coloreada por precio mediano"></svg></div>'),
    ("caso-churn.html", "02", "Customer Success", "profesional sql", "Salud de cuenta y churn por ROI",
     "Qué hoteles no recuperan su cuota mensual, y por qué, antes de que pidan la baja.",
     '<div class="v-roi"><div class="v-num">&lt;&nbsp;1<em>×</em><small>umbral de riesgo</small></div>'
     '<div class="scale"><i></i><i></i><i></i></div><div class="ticks"><span>Riesgo</span><span>1×</span><span>2×</span></div></div>'),
    ("caso-cuadre.html", "03", "BI governance", "profesional sql", "El dashboard que contaba el doble",
     "Diagnóstico de un sobreconteo frente al informe oficial y rediseño de la vista.",
     '<div class="v-num"><s>2,2×</s><br>1,0<em>×</em><small>cuadrado con el oficial</small></div>'),
    ("caso-funnel.html", "04", "Observabilidad", "profesional sql", "Funnel e integraciones",
     "Alertas que separan una caída comercial de un fallo del conector.",
     '<div class="v-bars"><i style="--w:100%"></i><i style="--w:82%"></i><i style="--w:49%"></i><i style="--w:17%"></i><i style="--w:13%"></i><i style="--w:8%"></i></div>'),
    ("caso-facturacion.html", "05", "Calidad del dato", "profesional python", "Limpieza de facturación",
     "Una hoja manual convertida en un proceso reproducible con log de cambios.",
     '<div class="v-code">"Synxis"<br>"SYNXIS"<br>"1.234,50"<br><b>→ SynXis</b><br><b>→ 1234.50</b></div>'),
    ("habilidades.html#portal", "06", "Desarrollo web", "python interactivo", "Este portal",
     "Generado con Python, sin frameworks, con consola SQL y auditoría antes de publicar.",
     '<div class="v-num">23<em>/</em>23<small>controles superados</small></div>'),
]


def tarjetas() -> str:
    return '<div class="cases">' + "".join(
        f'<a class="case" href="{h}" data-cat="{cat}"><div class="visual"><span class="idx">{n}</span><span class="cat">{c}</span>{v}</div>'
        f'<div class="meta"><h3>{t}</h3><p>{d}</p><span class="go">Ver {"proyecto" if n in ("01", "06") else "caso"} <span aria-hidden="true">→</span></span></div></a>'
        for h, n, c, cat, t, d, v in CASOS) + "</div>"


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
    ("Sobre mí", [("index.html", "Inicio"), ("cv.html", "CV"), ("cv.html#contacto", "Contacto"),
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
    if fichero == "index.html":        # hero interactivo
        s += '\n<script src="assets/hero.js"></script>'
    return s


def cuerpo(fichero: str) -> str:
    contenido = (SRC / "pages" / fichero).read_text(encoding="utf-8")
    contenido = contenido.replace('rel="noopener"', 'rel="noopener noreferrer"')
    contenido = contenido.replace("<!--CASOS-->", tarjetas()).replace("<!--RECORTE-->", recorte())
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
def cabeza_extra(titulo, desc):
    return ('<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">\n'
            '<meta name="theme-color" content="#f3f6fa" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#0b1724" media="(prefers-color-scheme: dark)">\n'
            f'<meta property="og:type" content="website">\n<meta property="og:title" content="{titulo}">\n'
            f'<meta property="og:description" content="{desc}">\n'
            '<meta property="og:image" content="assets/img/retrato-720.jpg">\n<meta name="twitter:card" content="summary">\n')


def pagina_completa(fichero, titulo, desc, seguridad=False):
    return ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + (SEGURIDAD if seguridad else "") +
            f'<title>{titulo}</title>\n<meta name="description" content="{desc}">\n' + cabeza_extra(titulo, desc) + f'{FUENTES}\n</head>\n'
            f'<body>\n{cuerpo(fichero)}\n</body>\n</html>\n')


# ------------------------------------------------------------------ assets
(OUT / "assets").mkdir(parents=True, exist_ok=True)
for f in ("styles.css", "app.js", "interactivo.js", "hero.js", "tema.js", "favicon.svg"):
    shutil.copy(SRC / "assets" / f, OUT / "assets" / f)
shutil.copytree(SRC / "assets" / "img", OUT / "assets" / "img", dirs_exist_ok=True)

datos = {
    "res": json.loads((DATOS / "resultados.json").read_text(encoding="utf-8")),
    "sql": json.loads((DATOS / "sql_resultados.json").read_text(encoding="utf-8")),
    "mapa": json.loads((DATOS / "mapa.json").read_text(encoding="utf-8")),
}
if (SRC / "auditoria.json").exists():   # resultado de la última auditoría, para la página Habilidades
    datos["audit"] = json.loads((SRC / "auditoria.json").read_text(encoding="utf-8"))
(OUT / "assets" / "datos.js").write_text(
    "window.PF = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n",
    encoding="utf-8")

(OUT / "assets" / "playground.js").write_text(
    "window.PG = " + (DATOS / "playground.json").read_text(encoding="utf-8").replace("</", "<\\/") + ";\n",
    encoding="utf-8")
(OUT / "casos.html").unlink(missing_ok=True)   # sustituida por una página por caso

# ------------------------------------------------------------------ versión de los assets
# Un sufijo ?v=<hash> por fichero obliga al navegador a descargar la versión nueva tras cada cambio.
def version(nombre: str) -> str:
    return hashlib.sha1((OUT / "assets" / nombre).read_bytes()).hexdigest()[:8]


VERSIONES = {n: version(n) for n in ("styles.css", "app.js", "interactivo.js", "hero.js", "tema.js", "datos.js")}


def con_version(html: str) -> str:
    for n, v in VERSIONES.items():
        html = html.replace(f'assets/{n}"', f'assets/{n}?v={v}"')
    return html


# ------------------------------------------------------------------ páginas
for fichero, titulo, desc, _ in PAGINAS:
    (OUT / fichero).write_text(con_version(pagina_completa(fichero, titulo, desc, seguridad=True)), encoding="utf-8")

(OUT / ".nojekyll").write_text("", encoding="utf-8")   # GitHub Pages sirve los ficheros tal cual, sin Jekyll

# Página 404: GitHub Pages la sirve sola para cualquier ruta inexistente; no entra en el menú
(OUT / "404.html").write_text(con_version(pagina_completa("404.html", "Página no encontrada", "Esta página no existe.", seguridad=True)),
                              encoding="utf-8")

# Copia para el Artifact, sin ?v= (sirve sus ficheros por ruta exacta).
# El inicio va sin <html>/<head>/<body>: el publicador los añade.
_, titulo, desc, _ = PAGINAS[0]
(RAIZ / "portfolio.html").write_text(f"<title>{titulo}</title>\n" + cabeza_extra(titulo, desc) + f"{FUENTES}\n{cuerpo('index.html')}\n",
                                     encoding="utf-8")
ART = RAIZ / "artifact"
ART.mkdir(exist_ok=True)
for fichero, titulo_p, desc_p, _ in PAGINAS[1:]:
    (ART / fichero).write_text(pagina_completa(fichero, titulo_p, desc_p), encoding="utf-8")

for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print(f"{p.relative_to(RAIZ)}  {p.stat().st_size // 1024} KB")

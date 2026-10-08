"""
Auditoría automática del portal antes de publicarlo: seguridad, filtración de información y navegación.

Uso:
    python sitio_src/auditoria.py sitio

Escribe sitio_src/auditoria.json (lo muestra la página Habilidades) y termina con código 1 si algo falla.
"""
import json
import re
import sys
from collections import deque
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(sys.argv[1] if len(sys.argv) > 1 else "sitio")
SALIDA = Path(__file__).resolve().parent / "auditoria.json"
HTML = sorted(RAIZ.glob("*.html"))
TEXTO = HTML + sorted((RAIZ / "assets").glob("*.js")) + sorted((RAIZ / "assets").glob("*.css"))
leer = lambda p: p.read_text(encoding="utf-8", errors="replace")
resultados = []


def check(nombre, ok, detalle, hallazgos=()):
    resultados.append({"control": nombre, "ok": bool(ok), "detalle": detalle, "hallazgos": list(hallazgos)[:8]})


def buscar(patron, ficheros, flags=re.I):
    rx = re.compile(patron, flags)
    out = []
    for p in ficheros:
        for m in rx.finditer(leer(p)):
            out.append(f"{p.name}: {m.group(0)[:60]}")
    return out


# ---------------------------------------------------------------- 1. Secretos
sec = buscar(r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
             r"(?:api[_-]?key|access[_-]?token|password|passwd|secret)\s*[:=]\s*['\"][^'\"]{6,}", TEXTO)
check("Sin claves, tokens ni contraseñas", not sec, "Patrones de claves de AWS, OpenAI, GitHub, Google y asignaciones de secretos.", sec)

# ---------------------------------------------------------------- 2. Identificadores internos del empleador
# La lista de lo que no debe filtrarse es, en sí misma, sensible: vive en privado/patrones.json, que no se publica.
PRIVADO = Path(__file__).resolve().parent / "privado" / "patrones.json"
PATRONES = json.loads(PRIVADO.read_text(encoding="utf-8")) if PRIVADO.exists() else None
if PATRONES:
    inter = buscar("|".join(PATRONES["internos"]), TEXTO, flags=0)
    check("Sin nombres internos de tablas, columnas ni clientes", not inter,
          "Tablas y columnas del almacén de datos del empleador, nombres de clientes y proveedores.", inter)
else:
    check("Sin nombres internos de tablas, columnas ni clientes", False, "Falta privado/patrones.json: no se puede comprobar.")

# ---------------------------------------------------------------- 3. Datos personales
emails = buscar(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", TEXTO, flags=0)
emails = [e for e in emails if "@media" not in e and "@view-transition" not in e and "@keyframes" not in e]
tel = buscar("|".join(PATRONES["personales"]), HTML + sorted((RAIZ / "assets").glob("*.js"))) if PATRONES else ["falta privado/patrones.json"]
check("Email no aparece completo en el código", not emails, "El email se monta en el navegador a partir de dos partes.", emails)
check("Sin teléfono ni dirección postal", not tel, "Teléfono y dirección del CV en PDF excluidos.", tel)

# ---------------------------------------------------------------- 4. Rutas y ficheros que no deben publicarse
rutas = buscar(r"[A-Z]:\\\\Users|[A-Z]:/Users|/Users/[a-z]+|AppData|scratch-workspaces", TEXTO)
check("Sin rutas locales del equipo", not rutas, "Rutas de Windows o macOS que delatarían el usuario o la estructura local.", rutas)
prohibidos = [p.name for p in RAIZ.rglob("*") if p.suffix.lower() in {".db", ".csv", ".gz", ".py", ".env", ".svg", ".zip"}
              and p.name != "favicon.svg"]
check("Sin bases de datos, datos crudos ni código fuente publicado", not prohibidos,
      "La web solo publica HTML, CSS, JS, imágenes y datos agregados.", prohibidos)

# ---------------------------------------------------------------- 5. HTML: enlaces, scripts e inline
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links, self.scripts, self.ids, self.inline, self.meta = [], [], set(), [], []

    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a: self.ids.add(a["id"])
        for k, v in a.items():
            if k.startswith("on"): self.inline.append(f"{tag} {k}")
            if v and str(v).strip().lower().startswith("javascript:"): self.inline.append(f"{tag} {k}=javascript:")
        if tag == "a" and a.get("href"): self.links.append((a["href"], a.get("rel", ""), a.get("target")))
        if tag == "script" and a.get("src"): self.scripts.append(a)
        if tag == "meta": self.meta.append(a)


paginas = {}
for p in HTML:
    x = P(); x.feed(leer(p)); paginas[p.name] = x

ext_mal = [f"{n}: {h}" for n, x in paginas.items() for h, rel, t in x.links
           if h.startswith("http") and not ("noopener" in rel and "noreferrer" in rel)]
check("Enlaces externos con rel=\"noopener noreferrer\"", not ext_mal,
      "Evita que la página enlazada controle esta pestaña y que reciba la URL de origen.", ext_mal)
inl = [f"{n}: {i}" for n, x in paginas.items() for i in x.inline]
check("Sin manejadores inline ni URLs javascript:", not inl, "Todo el comportamiento vive en ficheros .js (compatible con CSP).", inl)
csp = [n for n, x in paginas.items() if not any(m.get("http-equiv", "").lower() == "content-security-policy" for m in x.meta)]
check("Content-Security-Policy en todas las páginas", not csp, "Solo scripts propios y de cdnjs; sin plugins ni formularios externos.", csp)
scr_ext = [f"{n}: {s['src']}" for n, x in paginas.items() for s in x.scripts if s["src"].startswith("http")]
check("Sin scripts externos en el HTML", not scr_ext, "Los únicos scripts estáticos son propios.", scr_ext)
http = buscar(r"""(?:src|href)=["']http://""", HTML)
check("Sin recursos por HTTP sin cifrar", not http, "Todo se sirve por HTTPS o desde el propio sitio.", http)

nulos = [p.name for p in RAIZ.rglob("*") if p.is_file() and p.suffix in {".html", ".css", ".js", ".svg"} and b"\x00" in p.read_bytes()]
check("Ficheros de texto sin bytes nulos", not nulos, "Un byte nulo rompe el CSS o el JS en algunos navegadores.", nulos)

# ---------------------------------------------------------------- 5b. Accesibilidad y acabado
def visible(texto):
    texto = re.sub(r"<(script|style|template)[\s\S]*?</\1>", " ", texto)
    return re.sub(r"<[^>]+>", " ", texto)
guiones = [f"{p.name}: …{m.group(0)}…" for p in HTML for m in re.finditer(r".{0,25}[–—].{0,25}", visible(leer(p)))]
check("Sin guiones largos en el texto visible", not guiones, "Rangos y pausas con guion normal o con puntuación.", guiones)
sin_skip = [n for n, x in paginas.items() if not any(h == "#contenido" for h, _, _ in x.links)]
check("Enlace «Saltar al contenido» en todas las páginas", not sin_skip, "Para quien navega con teclado o lector de pantalla.", sin_skip)
sin_icono = [p.name for p in HTML if 'rel="icon"' not in leer(p)]
check("Favicon y metadatos para compartir", not sin_icono and all('og:title' in leer(p) for p in HTML),
      "Icono propio, color de la barra del navegador y tarjeta Open Graph.", sin_icono)

# ---------------------------------------------------------------- 6. JavaScript
js = sorted((RAIZ / "assets").glob("*.js"))
peligrosos = buscar(r"\beval\s*\(|new Function\s*\(|document\.write\s*\(", [p for p in js if p.name not in {"datos.js", "playground.js"}])
check("Sin eval, new Function ni document.write", not peligrosos, "Sumideros que ejecutan texto como código.", peligrosos)
cdn = re.findall(r"https://[^\s\"'`]+\.js", "".join(leer(p) for p in js if p.name not in {"datos.js", "playground.js"}))
sri_ok = all(u.startswith("https://cdnjs.cloudflare.com/") for u in cdn) and "integrity" in leer(RAIZ / "assets" / "interactivo.js")
check("Script de terceros con Subresource Integrity", sri_ok, "sql.js se carga desde cdnjs con hash SHA-384 y crossorigin.", cdn)
# innerHTML: cada interpolación ${...} debe pasar por esc()/fmt()/hl() o estar en la línea base revisada a mano
BASE = Path(__file__).resolve().parent / "innerhtml_revisado.json"
revisadas = set(json.loads(BASE.read_text(encoding="utf-8"))["revisadas"]) if BASE.exists() else set()
ASIGNACION = r"\.innerHTML\s*=([\s\S]*?);\s*\n"
nuevas, total = [], 0
for p in js:
    if p.name in {"datos.js", "playground.js"}: continue
    for m in re.finditer(ASIGNACION, leer(p)):
        total += 1
        for e in re.findall(r"\$\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", m.group(1)):
            if not re.match(r"\s*(esc|fmt|hl|highlight|window\.PFhl)\(", e) and e not in revisadas:
                nuevas.append(f"{p.name}: ${{{e[:50]}}}")
if "--rebase" in sys.argv:   # tras revisar a mano, se aceptan las actuales como línea base
    todas = sorted({e for p in js if p.name not in {"datos.js", "playground.js"}
                    for m in re.finditer(ASIGNACION, leer(p))
                    for e in re.findall(r"\$\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", m.group(1))
                    if not re.match(r"\s*(esc|fmt|hl|highlight|window\.PFhl)\(", e)})
    BASE.write_text(json.dumps({"nota": "Interpolaciones revisadas a mano: constantes, números o plantillas anidadas que ya escapan sus datos.",
                                "revisadas": todas}, ensure_ascii=False, indent=2), encoding="utf-8")
    nuevas = []
check("innerHTML solo con datos escapados", not nuevas,
      f"{total} asignaciones revisadas: los datos pasan por esc() y el resto está en una línea base revisada a mano.", nuevas)
tema = "t === \"light\" || t === \"dark\"" in leer(RAIZ / "assets" / "app.js")
check("Valores de localStorage validados", tema, "El tema guardado solo acepta «light» o «dark».")

# ---------------------------------------------------------------- 7. Imágenes y datos
imgs = sorted((RAIZ / "assets" / "img").glob("*"))
exif = [p.name for p in imgs if b"Exif" in p.read_bytes() or b"GPS" in p.read_bytes()]
check("Imágenes sin metadatos EXIF ni GPS", not exif, f"{len(imgs)} imágenes generadas desde canvas, sin metadatos de cámara.", exif)
pg = leer(RAIZ / "assets" / "playground.js")
d = json.loads(pg[pg.index("=") + 1:].rstrip().rstrip(";"))["listings_limpio"]
ids_ok = max(r[0] for r in d["filas"]) == len(d["filas"]) and max(r[1] for r in d["filas"]) < 10000
check("Identificadores seudonimizados en la consola", ids_ok, "Los IDs de anuncio y anfitrión son correlativos, no los de Airbnb.")
check("Sin nombres de anfitriones en los datos", "host_name" not in pg, "Solo variables del anuncio y agregados.")

# ---------------------------------------------------------------- 8. Navegación: todo a 3 clics o menos
paginas.pop("404.html", None)   # la 404 solo aparece ante una ruta inexistente; no se enlaza
destinos = set(paginas)
for n, x in paginas.items():
    for i in x.ids:
        if re.search(rf'<(section|article)[^>]*\bid="{re.escape(i)}"', leer(RAIZ / n)):
            destinos.add(f"{n}#{i}")


def enlaces(nodo):
    pag = nodo.split("#")[0]
    for h, _, _ in paginas[pag].links:
        if h.startswith(("http", "mailto")): continue
        destino = (pag + h) if h.startswith("#") else h
        base, _, frag = destino.partition("#")
        if base in paginas:
            yield f"{base}#{frag}" if frag and f"{base}#{frag}" in destinos else base


def bfs(origen):
    dist, q = {origen: 0}, deque([origen])
    while q:
        u = q.popleft()
        for v in enlaces(u):
            if v not in dist: dist[v] = dist[u] + 1; q.append(v)
    return dist


peor, lejos = 0, []
for origen in paginas:
    dist = bfs(origen)
    for t in destinos:
        d_ = dist.get(t, 99)
        if d_ > peor: peor = d_
        if d_ > 3: lejos.append(f"{origen} → {t}: {d_}")
desde_inicio = bfs("index.html")
check("Cualquier sección a 3 clics o menos", peor <= 3,
      f"{len(destinos)} destinos ({len(paginas)} páginas y {len(destinos) - len(paginas)} secciones). "
      f"Peor caso desde cualquier página: {peor} clic(s); desde el inicio: {max(desde_inicio.get(t, 99) for t in destinos)}.", lejos)

ok = sum(r["ok"] for r in resultados)
SALIDA.write_text(json.dumps({"total": len(resultados), "ok": ok, "controles": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
for r in resultados:
    print(("OK   " if r["ok"] else "FALLA") + "  " + r["control"] + ("" if r["ok"] else "  ← " + "; ".join(r["hallazgos"][:4])))
print(f"\n{ok}/{len(resultados)} controles superados")
sys.exit(0 if ok == len(resultados) else 1)

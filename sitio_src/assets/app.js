/* Portal de proyectos · comportamiento compartido por todas las páginas.
   Cada bloque solo actúa si su elemento existe en la página. */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };
  // Idioma de la página: las de en/ llevan <html lang="en">. Textos, números, euros y porcentajes se adaptan.
  const EN = document.documentElement.lang === "en";
  const tr = (es, en) => EN ? en : es;   // no se llama T: T es el margen superior en los gráficos
  // Separador de miles siempre (en español, Intl omite el punto en números de 4 cifras: "9000" frente a "12.000")
  const fmt = (n, d = 0) => n == null ? "-" : Number(n).toLocaleString(EN ? "en-GB" : "es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: "always" });
  const eur = (n, d = 0) => n == null ? "-" : EN ? "€" + fmt(n, d) : fmt(n, d) + " €";
  const pc = (n, d = 0) => n == null ? "-" : fmt(n, d) + (EN ? "%" : " %");
  // Etiquetas que llegan en español dentro de los datos
  const DATA_EN = {
    "Piscina": "Pool", "Vista al mar": "Sea view", "Acceso a playa": "Beach access", "Aire acondicionado": "Air conditioning",
    "Jacuzzi": "Hot tub", "Parking gratuito": "Free parking", "Barbacoa": "Barbecue", "Cargador VE": "EV charger", "Gimnasio": "Gym",
    "Apartamento": "Apartment", "Casa / otros": "House / other", "Villa / finca": "Villa / country house",
    "Precio mediano por municipio (SQL con ventanas vs pandas .median())": "Median price per municipality (SQL window functions vs pandas .median())",
    "Anuncios sin precio": "Listings without a price", "Reseñas 2023–2025": "Reviews 2023-2025",
    "% de anuncios de anfitriones con 20+": "% of listings from hosts with 20+",
    "53 de 53 municipios": "53 of 53 municipalities", "53 municipios": "53 municipalities",
    "Con redondeo a entero salían 52 de 53: Lloret de Vistalegre (328,5 €) → 328 en pandas y 329 en SQLite.":
      "Rounded to whole euros it was 52 of 53: Lloret de Vistalegre (€328.5) → 328 in pandas and 329 in SQLite.",
  };
  const tl = s => (EN && DATA_EN[s]) || s;
  window.PFi18n = { EN, T: tr, fmt, eur, pc, tl };
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const PF = window.PF || {};

  /* ---------- Tema claro / oscuro ---------- */
  const root = document.documentElement;
  // tema.js ya ha aplicado la elección guardada en <head>; aquí solo se alterna
  try { const t = localStorage.getItem("tema"); if (t === "light" || t === "dark") root.dataset.theme = t; } catch (e) {}
  const tbtn = $("#themeBtn");
  if (tbtn) tbtn.addEventListener("click", () => {
    const dark = root.dataset.theme === "dark";
    root.dataset.theme = dark ? "light" : "dark";
    tbtn.setAttribute("aria-label", dark ? tr("Activar tema oscuro", "Switch to dark theme") : tr("Activar tema claro", "Switch to light theme"));
    try { localStorage.setItem("tema", root.dataset.theme); } catch (e) {}
  });

  /* ---------- Menú móvil y barra de progreso de lectura ---------- */
  const head = $(".site-head"), burger = $("#burger");
  if (burger) {
    burger.addEventListener("click", () => {
      const open = head.dataset.open !== "true";
      head.dataset.open = open; burger.setAttribute("aria-expanded", open);
    });
    document.addEventListener("click", e => { if (!head.contains(e.target)) { head.dataset.open = "false"; burger.setAttribute("aria-expanded", "false"); } });
    document.addEventListener("keydown", e => { if (e.key === "Escape") { head.dataset.open = "false"; burger.setAttribute("aria-expanded", "false"); } });
  }

  /* ---------- Email ensamblado en el navegador (no aparece entero en el HTML) ---------- */
  $$("[data-u][data-d]").forEach(e => { e.textContent = e.dataset.u + "@" + e.dataset.d; });

  /* ---------- Desplegable de Proyectos ---------- */
  $$(".dd").forEach(dd => {
    const b = $(".dd-btn", dd);
    const set = open => { dd.dataset.open = open; b.setAttribute("aria-expanded", open); };
    b.addEventListener("click", e => { e.stopPropagation(); set(dd.dataset.open !== "true"); });
    document.addEventListener("click", e => { if (!dd.contains(e.target)) set(false); });
    dd.addEventListener("keydown", e => { if (e.key === "Escape") { set(false); b.focus(); } });
  });

  /* ---------- Copiar email ---------- */
  $$("[data-copy]").forEach(b => b.addEventListener("click", () => {
    const t = $(b.dataset.copy);
    const select = () => { const r = document.createRange(); r.selectNodeContents(t); const s = getSelection(); s.removeAllRanges(); s.addRange(r); };
    const hueco = $("[data-copy-label]", b) || b, antes = [...hueco.childNodes];
    const done = m => { hueco.textContent = m; setTimeout(() => hueco.replaceChildren(...antes), 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(t.textContent.trim()).then(() => done(tr("Copiado", "Copied")), () => { select(); done(tr("Seleccionado", "Selected")); });
    else { select(); done(tr("Seleccionado", "Selected")); }
  }));

  /* ---------- Filtros de proyectos ---------- */
  const chips = $$(".chip[data-filter]");
  const pildora = () => $$(".seg.has-pill").forEach(seg => {
    const b = $(".chip[aria-pressed='true']", seg), p = $(".seg-pill", seg);
    if (b && p) { p.style.width = b.offsetWidth + "px"; p.style.transform = `translate(${b.offsetLeft}px, ${b.offsetTop - 4}px)`; }
  });
  pildora(); addEventListener("resize", pildora);
  if (document.fonts) document.fonts.ready.then(pildora);
  chips.forEach(c => c.addEventListener("click", () => {
    chips.forEach(x => x.setAttribute("aria-pressed", x === c ? "true" : "false"));
    pildora();
    const f = c.dataset.filter;
    $$("[data-cat]").forEach(card => { card.hidden = f !== "todos" && !card.dataset.cat.split(" ").includes(f); });
  }));

  /* ---------- Resaltado de código ---------- */
  const KW = {
    sql: /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|WITH|AS|CASE|WHEN|THEN|ELSE|END|AND|OR|NOT|IN|IS|NULL|OVER|PARTITION BY|ROW_NUMBER|COUNT|SUM|AVG|MIN|MAX|ROUND|CAST|REPLACE|NULLIF|NTILE|LAG|DISTINCT|DESC|ASC|LIMIT|CREATE|VIEW|DROP|IF|EXISTS|REAL|INTEGER|strftime|JOIN|LEFT|ON|USING|QUALIFY|DATE_TRUNC|IFNULL|SAFE_DIVIDE|REGEXP_CONTAINS|LOWER|CONCAT)\b/g,
    py: /\b(import|from|as|def|return|for|in|if|else|elif|None|True|False|lambda|and|or|not|with|try|except)\b/g,
  };
  function highlight(code, lang) {
    const comment = lang === "sql" ? /--.*$/ : /#.*$/;
    return code.split("\n").map(line => {
      const m = line.match(comment);
      let body = m ? line.slice(0, m.index) : line, tail = m ? m[0] : "";
      const parts = body.split(/("[^"]*"|'[^']*')/g);
      body = parts.map((p, i) => i % 2 ? '<span class="s">' + esc(p) + "</span>"
        : esc(p).replace(KW[lang] || /$^/, '<span class="k">$1</span>').replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="n">$1</span>')).join("");
      return body + (tail ? '<span class="c">' + esc(tail) + "</span>" : "");
    }).join("\n");
  }
  window.PFhl = highlight;
  function codeBlock(code, lang, label) {
    const w = document.createElement("div"); w.className = "code";
    w.innerHTML = '<div class="code-bar"><span>' + esc(label || lang.toUpperCase()) + '</span><button type="button">' + tr("Copiar", "Copy") + '</button></div><pre><code></code></pre>';
    $("code", w).innerHTML = highlight(code, lang);
    const b = $("button", w);
    b.addEventListener("click", () => {
      const ok = () => { b.textContent = tr("Copiado", "Copied"); setTimeout(() => (b.textContent = tr("Copiar", "Copy")), 1800); };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(ok, () => { b.textContent = tr("Selecciona y copia", "Select and copy"); });
    });
    return w;
  }
  $$("template[data-code]").forEach(t => {
    const lang = t.dataset.code, code = t.innerHTML.replace(/^\n/, "").replace(/\s+$/, "")
      .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
    t.replaceWith(codeBlock(code, lang, t.dataset.label));
  });

  /* ---------- Pestañas ---------- */
  $$(".tabset").forEach(set => {
    const btns = $$(".tabs button", set), panels = $$(".tabpanel", set);
    const show = i => { btns.forEach((b, j) => { b.setAttribute("aria-selected", i === j); b.tabIndex = i === j ? 0 : -1; }); panels.forEach((p, j) => (p.hidden = i !== j)); };
    btns.forEach((b, i) => {
      b.addEventListener("click", () => show(i));
      b.addEventListener("keydown", e => { if (e.key === "ArrowRight" || e.key === "ArrowLeft") { const n = (i + (e.key === "ArrowRight" ? 1 : -1) + btns.length) % btns.length; show(n); btns[n].focus(); } });
    });
    show(0);
  });

  /* ---------- Índice con scrollspy ---------- */
  const toc = $$(".toc a[href^='#']");
  if (toc.length && "IntersectionObserver" in window) {
    const map = new Map(toc.map(a => [a.getAttribute("href").slice(1), a]));
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { toc.forEach(a => a.classList.remove("on")); const a = map.get(e.target.id); if (a) { a.classList.add("on"); a.scrollIntoView({ block: "nearest", inline: "nearest" }); } }
    }), { rootMargin: "-30% 0px -60% 0px" });
    map.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
  }

  /* ---------- Movimiento: aparición al entrar en pantalla, titular por palabras, cabecera y profundidad ---------- */
  const quieto = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Titular palabra a palabra (el texto queda igual para lectores de pantalla)
  $$("h1.split").forEach(h => {
    h.setAttribute("aria-label", h.textContent.trim());
    let i = 0;
    const partir = n => [...n.childNodes].forEach(c => {
      if (c.nodeType !== 3) return partir(c);
      const frag = document.createDocumentFragment();
      c.textContent.split(/(\s+)/).forEach(w => {
        if (!w.trim()) return frag.append(w);
        const caja = document.createElement("span"), pal = document.createElement("span");
        caja.className = "w"; caja.setAttribute("aria-hidden", "true"); pal.textContent = w; pal.style.setProperty("--i", i++);
        caja.append(pal); frag.append(caja);
      });
      c.replaceWith(frag);
    });
    partir(h);
  });
  // En páginas interiores, los bloques principales también aparecen al bajar
  $$(".p-hero > *, .chapter, .case-block, .finding, .mrow, .job, .card, .sql-card, .nb-cell, .panel, .prevnext a, .cv-box, .grid-cards > *, .op-kpis > div, .checklist li")
    .forEach((n, k) => { if (!n.hasAttribute("data-reveal")) { n.setAttribute("data-reveal", ""); n.style.setProperty("--i", k % 4); } });
  if ("IntersectionObserver" in window) {
    const aparece = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.classList.add("in"); aparece.unobserve(e.target);
    }), { threshold: .12, rootMargin: "0px 0px -6% 0px" });
    $$("[data-reveal], h1.split, .hero-photo").forEach(n => aparece.observe(n));
  } else $$("[data-reveal], h1.split, .hero-photo").forEach(n => n.classList.add("in"));

  // Cabecera translúcida en cuanto la página se desplaza (centinela, sin escuchar el scroll)
  if (head && "IntersectionObserver" in window) {
    const cent = document.createElement("div");
    cent.setAttribute("aria-hidden", "true"); cent.style.cssText = "position:absolute;top:0;left:0;width:1px;height:8px;pointer-events:none";
    document.body.prepend(cent);
    new IntersectionObserver(([e]) => head.classList.toggle("stuck", !e.isIntersecting)).observe(cent);
  }

  // Fichas sobre la foto con profundidad al mover el puntero
  const foto = $(".hero-photo");
  if (foto && !quieto && matchMedia("(hover: hover)").matches) {
    foto.addEventListener("pointermove", e => {
      const r = foto.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      $$("[data-depth]", foto).forEach(c => { const d = +c.dataset.depth; c.style.transform = `translate(${(x * d).toFixed(1)}px, ${(y * d).toFixed(1)}px)`; });
    });
    foto.addEventListener("pointerleave", () => $$("[data-depth]", foto).forEach(c => (c.style.transform = "")));
  }

  /* ---------- Cifras que cuentan al entrar en pantalla (una vez; nada si se pide menos movimiento) ---------- */
  if (!quieto && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      const b = e.target, n = +b.dataset.n, suf = b.dataset.suf || "", t0 = performance.now();
      const paso = t => { const k = Math.min(1, (t - t0) / 1300); b.textContent = fmt(Math.round(n * (1 - Math.pow(1 - k, 3)))) + suf; if (k < 1) requestAnimationFrame(paso); };
      requestAnimationFrame(paso);
    }), { threshold: .6 });
    $$("[data-n]").forEach(b => io.observe(b));
  }

  /* ================= Gráficos (proyecto Mallorca) =================
     Cada gráfico se dibuja al ancho real de su contenedor (el texto mantiene su tamaño en móvil)
     y se redibuja si ese ancho cambia. Todos comparten un tooltip que se abre al pasar el cursor,
     al tocar o al enfocar con el teclado; el texto va siempre con textContent. */
  const R = PF.res, S = PF.sql, M = PF.mapa;

  const tip = document.createElement("div");
  tip.className = "chart-tip"; tip.setAttribute("aria-hidden", "true"); document.body.append(tip);
  function tipShow(text, x, y) {
    tip.textContent = text; tip.dataset.on = "true";
    const r = tip.getBoundingClientRect(), pad = 14;
    let left = x + pad, top = y + pad;
    if (left + r.width > innerWidth - 8) left = x - r.width - pad;
    if (top + r.height > innerHeight - 8) top = y - r.height - pad;
    tip.style.transform = `translate(${Math.max(8, left)}px, ${Math.max(8, top)}px)`;
  }
  const tipHide = () => { tip.dataset.on = "false"; };
  // Cualquier marca con data-tip abre el tooltip; con teclado se ancla a la propia marca
  function conTip(node, text) {
    node.dataset.tip = text; node.setAttribute("tabindex", "0"); node.setAttribute("aria-label", text.replace(/\n/g, ". "));
    node.addEventListener("pointermove", e => tipShow(text, e.clientX, e.clientY));
    node.addEventListener("pointerleave", tipHide);
    node.addEventListener("focus", () => { const b = node.getBoundingClientRect(); tipShow(text, b.left + b.width / 2, b.top); });
    node.addEventListener("blur", tipHide);
    return node;
  }
  window.PFtip = { conTip, show: tipShow, hide: tipHide };
  addEventListener("scroll", tipHide, { passive: true });

  function responsivo(svg, dibujar) {
    let ancho = 0;
    const pintar = () => {
      const w = Math.round(svg.getBoundingClientRect().width) || 640;
      if (Math.abs(w - ancho) < 8) return;
      ancho = w; svg.replaceChildren(); dibujar(svg, Math.max(300, w));
    };
    pintar();
    if ("ResizeObserver" in window) { let t; new ResizeObserver(() => { clearTimeout(t); t = setTimeout(pintar, 120); }).observe(svg); }
  }
  const eje = (svg, x1, x2, y, dash) => svg.append(el("line", { x1, x2, y1: y, y2: y, stroke: "var(--line)", "stroke-dasharray": dash ? "3 4" : "0" }));

  // 1 · Prima por atributo: punto + intervalo de confianza, una fila por atributo
  function prima(svg, W, compact) {
    const A = R.hedonico.atributos.filter(a => !compact || a.ic95[0] > 0 || a.ic95[1] < 0);
    const estrecho = W < 520, L = estrecho ? 112 : 160, Rr = W - (estrecho ? 58 : 76), min = compact ? 0 : -15, max = 35;
    const rowH = compact ? 38 : 34, top = 10, H = top + A.length * rowH + 30;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H);
    const X = v => L + (v - min) / (max - min) * (Rr - L);
    (compact ? [0, 10, 20, 30] : [-10, 0, 10, 20, 30]).forEach(t => {
      svg.append(el("line", { x1: X(t), x2: X(t), y1: top - 4, y2: top + A.length * rowH, stroke: t === 0 ? "var(--ink)" : "var(--line)", "stroke-dasharray": t === 0 ? "0" : "3 4" }));
      if (!estrecho || t % 20 === 0) svg.append(el("text", { x: X(t), y: H - 6, "text-anchor": "middle" }, (t > 0 ? "+" : "") + pc(t)));
    });
    A.forEach((a, i) => {
      const y = top + i * rowH + rowH / 2, sig = a.ic95[0] > 0 || a.ic95[1] < 0, c = sig ? "var(--accent-mark)" : "var(--muted)";
      const g = el("g", { class: "row" });
      g.append(el("rect", { x: 0, y: y - rowH / 2, width: W, height: rowH, class: "hit" }));
      g.append(el("text", { x: L - 12, y: y + 4, "text-anchor": "end", class: "lbl" }, estrecho ? tl(a.atributo).replace("Aire acondicionado", "Aire acond.").replace("Air conditioning", "Air con.").replace(/^(Parking gratuito|Free parking)$/, "Parking") : tl(a.atributo)));
      g.append(el("line", { x1: X(Math.max(a.ic95[0], min)), x2: X(Math.min(a.ic95[1], max)), y1: y, y2: y, stroke: c, "stroke-width": compact ? 4 : 3, "stroke-opacity": .35, "stroke-linecap": "round" }));
      g.append(el("circle", { cx: X(a.prima_pct), cy: y, r: compact ? 7 : 6, fill: c, stroke: "var(--surface)", "stroke-width": 2 }));
      g.append(el("text", { x: X(Math.min(a.ic95[1], max)) + 10, y: y + 4, class: sig ? "lbl val" : "val" }, (a.prima_pct > 0 ? "+" : "") + pc(a.prima_pct, 1)));
      conTip(g, `${tl(a.atributo)}: ${(a.prima_pct > 0 ? "+" : "") + pc(a.prima_pct, 1)}\n${tr("IC 95 %", "95% CI")}: ${fmt(a.ic95[0], 1)} ${tr("a", "to")} ${pc(a.ic95[1], 1)}\n${pc(a.pct_anuncios, 1)} ${tr("de los anuncios lo tiene", "of listings have it")}${sig ? "" : tr("\nNo se distingue de cero", "\nNot distinguishable from zero")}`);
      svg.append(g);
    });
  }
  if (R) $$("svg[data-chart='prima']").forEach(s => responsivo(s, (svg, W) => prima(svg, W, s.dataset.compact === "1")));

  // 2 · Anfitriones: barra apilada ordinal con 2 px de separación; en móvil, etiquetas en leyenda
  const host = $("#hostSvg");
  if (host && R) responsivo(host, (svg, W) => {
    const d = R.mercado.anuncios_por_tramo_anfitrion_pct, keys = ["1", "2-4", "5-19", "20+"];
    const names = EN ? { "1": "1 listing", "2-4": "2 to 4 listings", "5-19": "5 to 19 listings", "20+": "20 or more" }
                       : { "1": "1 anuncio", "2-4": "2 a 4 anuncios", "5-19": "5 a 19 anuncios", "20+": "20 o más" };
    const estrecho = W < 560, H = estrecho ? 44 + keys.length * 22 : 96;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H);
    let x = 0;
    keys.forEach((k, i) => {
      const w = W * d[k] / 100;
      conTip(svg.appendChild(el("rect", { x, y: 4, width: Math.max(w - 2, 0), height: 32, fill: `var(--seq${i + 1})`, class: "mark" })), `${tr("Anfitriones con", "Hosts with")} ${names[k]}\n${pc(d[k], 1)} ${tr("de los anuncios", "of listings")}`);
      if (!estrecho) { svg.append(el("text", { x: x + 2, y: 58, class: "lbl" }, names[k])); svg.append(el("text", { x: x + 2, y: 76 }, pc(d[k], 1))); }
      else { const y = 58 + i * 22; svg.append(el("rect", { x: 0, y: y - 10, width: 12, height: 12, fill: `var(--seq${i + 1})` })); svg.append(el("text", { x: 20, y, class: "lbl" }, names[k])); svg.append(el("text", { x: W, y, "text-anchor": "end" }, pc(d[k], 1))); }
      x += w;
    });
  });

  // 3 · Deciles: barras con extremo redondeado de 4 px anclado a la base; foco en el primer decil
  const dec = $("#decilSvg");
  if (dec && S) responsivo(dec, (svg, W) => {
    const q = S.consultas.find(c => c.fichero.startsWith("05")), iP = q.columnas.indexOf("pct_ingreso"), iN = q.columnas.indexOf("anuncios"), iA = q.columnas.indexOf("pct_acumulado");
    const rows = q.filas, L = 40, B = 196, T = 22, H = 222, bw = (W - L) / rows.length, max = 40, gap = Math.max(4, bw * .18);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H);
    [0, 10, 20, 30, 40].forEach(t => { const y = B - t / max * (B - T); eje(svg, L, W, y, t > 0); svg.append(el("text", { x: L - 8, y: y + 4, "text-anchor": "end" }, pc(t))); });
    rows.forEach((r, k) => {
      const v = r[iP], h = v / max * (B - T), x = L + k * bw + gap / 2, w = bw - gap, rad = Math.min(4, w / 2, h);
      const p = el("path", { d: `M${x},${B}V${B - h + rad}Q${x},${B - h} ${x + rad},${B - h}H${x + w - rad}Q${x + w},${B - h} ${x + w},${B - h + rad}V${B}Z`, fill: k === 0 ? "var(--accent-mark)" : "var(--y1)", class: "mark" });
      conTip(p, `${tr("Decil", "Decile")} ${r[0]}: ${pc(v, 1)} ${tr("del ingreso", "of income")}\n${fmt(r[iN])} ${tr("anuncios", "listings")}\n${tr("Acumulado", "Cumulative")}: ${pc(r[iA], 1)}`);
      svg.append(p);
      if (k === 0 || W >= 560) svg.append(el("text", { x: x + w / 2, y: B - h - 7, "text-anchor": "middle", class: k === 0 ? "lbl" : "" }, fmt(v, 1)));
      svg.append(el("text", { x: x + w / 2, y: B + 18, "text-anchor": "middle" }, (W < 480 ? "" : "D") + r[0]));
    });
  });

  // 4 · Estacionalidad: tres años, foco en el último; retícula con los tres valores del mes
  const seas = $("#seasSvg");
  if (seas && R) responsivo(seas, (svg, W) => {
    const Y = R["reseñas_por_mes"], years = Object.keys(Y), lg = $("#seasLegend"), L = 56, Rr = W - 16, T = 18, B = 214, H = 244, max = 12000;
    const meses = EN ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] : ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H);
    const X = i => L + i * (Rr - L) / 11, YY = v => B - v / max * (B - T);
    [0, 3000, 6000, 9000, 12000].forEach(t => { eje(svg, L, Rr, YY(t), t > 0); svg.append(el("text", { x: L - 8, y: YY(t) + 4, "text-anchor": "end" }, fmt(t))); });
    meses.forEach((m, i) => { if (W >= 480 || i % 2 === 0) svg.append(el("text", { x: X(i), y: B + 20, "text-anchor": "middle" }, m)); });
    const sty = { "2023": ["var(--y1)", 2], "2024": ["var(--y2)", 2], "2025": ["var(--y3)", 3] };
    years.forEach(y => {
      const [c, w] = sty[y] || ["var(--muted)", 2];
      svg.append(el("polyline", { points: Y[y].map((v, i) => X(i) + "," + YY(v)).join(" "), fill: "none", stroke: c, "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      if (W >= 480) svg.append(el("text", { x: X(6), y: YY(Y[y][6]) - 9, "text-anchor": "middle", class: "lbl" }, y));
    });
    const cruz = el("line", { y1: T, y2: B, stroke: "var(--ink)", "stroke-width": 1, opacity: 0 }); svg.append(cruz);
    const puntos = years.map(y => { const c = el("circle", { r: 4.5, fill: (sty[y] || [])[0], stroke: "var(--surface)", "stroke-width": 2, opacity: 0 }); svg.append(c); return c; });
    const capa = el("rect", { x: L, y: T, width: Rr - L, height: B - T, fill: "transparent", class: "hit-area" }); svg.append(capa);
    const mostrar = (i, cx, cy) => {
      cruz.setAttribute("x1", X(i)); cruz.setAttribute("x2", X(i)); cruz.setAttribute("opacity", .35);
      years.forEach((y, k) => { puntos[k].setAttribute("cx", X(i)); puntos[k].setAttribute("cy", YY(Y[y][i])); puntos[k].setAttribute("opacity", 1); });
      tipShow(`${meses[i]}\n` + years.slice().reverse().map(y => `${y}: ${fmt(Y[y][i])} ${tr("reseñas", "reviews")}`).join("\n"), cx, cy);
    };
    const ocultar = () => { cruz.setAttribute("opacity", 0); puntos.forEach(p => p.setAttribute("opacity", 0)); tipHide(); };
    capa.addEventListener("pointermove", e => { const b = svg.getBoundingClientRect(), x = (e.clientX - b.left) * W / b.width; mostrar(Math.max(0, Math.min(11, Math.round((x - L) / ((Rr - L) / 11)))), e.clientX, e.clientY); });
    capa.addEventListener("pointerleave", ocultar);
    if (lg && !lg.childElementCount) years.forEach(y => { const [c, w] = sty[y] || ["var(--muted)", 2]; const sp = document.createElement("span"); sp.innerHTML = `<i style="background:${c};height:${w}px"></i>${esc(y)}: ${fmt(Y[y].reduce((a, b) => a + b, 0))} ${tr("reseñas", "reviews")}`; lg.append(sp); });
  });

  /* Escala secuencial de 4 clases (un solo tono, de claro a oscuro), validada con dataviz/validate_palette.js */
  const MAPA = {
    breaks: [300, 400, 500],
    labels: EN ? ["< €300", "€300-399", "€400-499", "≥ €500"] : ["< 300 €", "300-399 €", "400-499 €", "≥ 500 €"],
    color: v => v == null ? "var(--surface-2)" : `var(--seq${[300, 400, 500].filter(b => v >= b).length + 1})`,
    legend(box) { if (box && !box.childElementCount) this.labels.forEach((t, i) => { const sp = document.createElement("span"); sp.innerHTML = `<i style="background:var(--seq${i + 1});height:10px;width:16px"></i>${t}`; box.append(sp); }); },
    mini(svg) {   // mapa pequeño sin interacción, para tarjetas y miniaturas
      if (!svg || !M) return;
      svg.setAttribute("viewBox", `-4 -4 ${M.w + 8} ${M.h + 8}`);
      M.municipios.forEach(m => svg.append(el("path", { d: m.d, fill: MAPA.color(m.precio_mediano), stroke: "var(--bg)", "stroke-width": 1.5 })));
    },
    // Mapa interactivo: tooltip flotante + texto fijo debajo (para lectores de pantalla y móvil)
    full(svg, fijo) {
      if (!svg || !M) return;
      svg.setAttribute("viewBox", `-4 -4 ${M.w + 8} ${M.h + 8}`);
      M.municipios.forEach(m => {
        const has = m.precio_mediano != null;
        const p = el("path", { d: m.d, fill: MAPA.color(m.precio_mediano), stroke: "var(--surface)", "stroke-width": 1, class: "mun" });
        const txt = has ? `${m.nombre}\n${eur(m.precio_mediano)} ${tr("de mediana por noche", "median per night")}\n${fmt(m.anuncios)} ${tr("anuncios", "listings")}` : `${m.nombre}\n${tr("Sin precio publicado", "No published price")}`;
        conTip(p, txt);
        const fijar = () => { if (fijo) fijo.textContent = txt.replace(/\n/g, ", "); svg.append(p); };
        ["pointerenter", "focus", "click"].forEach(e => p.addEventListener(e, fijar));
        svg.append(p);
      });
    },
  };
  window.PFmap = MAPA;
  $$("svg[data-minimap], #bandMap").forEach(s => MAPA.mini(s));
  if (M && $("#mapSvg")) { MAPA.full($("#mapSvg"), $("#mapTip")); MAPA.legend($("#mapLegend")); }

  const mt = $("#munTable tbody");
  if (mt && R) R.municipios_top_anuncios.forEach(m => {
    const fila = document.createElement("tr");
    fila.innerHTML = `<td>${esc(m.municipio)}</td><td class="r">${fmt(m.anuncios)}</td><td class="r">${eur(m.precio_mediano)}</td><td class="r">${eur(m.ingreso_mediano)}</td><td class="r">${pc(m.piscina_pct)}</td>`;
    mt.append(fila);
  });

  /* ================= SQL: consultas reales con su resultado ================= */
  const META = EN ? {
    "01": ["A clean view over the raw data", "Price arrives as text with a currency symbol and thousands separator. I clean it once in a view and every query starts from there.", ["CREATE VIEW", "CAST", "NULLIF", "REPLACE"]],
    "02": ["Data quality profile in one pass", "Before analysing: volume, duplicates, blanks and outliers.", ["Conditional aggregates", "SUM(expr IS NULL)"]],
    "03": ["Are prices missing at random?", "If listings without a price are different, excluding them biases the result. I check by comparing their activity.", ["CASE", "GROUP BY"]],
    "04": ["Median per municipality without a MEDIAN function", "SQLite has no MEDIAN(). I compute it with window functions, as in engines without percentiles.", ["CTE", "ROW_NUMBER() OVER", "COUNT() OVER", "PARTITION BY"]],
    "05": ["Income concentration by decile", "What share of income each 10% of listings earns, with the running total in the same query.", ["NTILE", "SUM() OVER ()", "Running total with a window"]],
    "06": ["How professional is the supply?", "Listings and hosts by the size of the host's portfolio.", ["CASE", "COUNT(DISTINCT)", "% of total with a window"]],
    "07": ["Year-on-year growth", "Change in activity year on year without self-joins.", ["LAG() OVER", "strftime", "CTE"]],
    "08": ["Calendar: 5.4 million rows", "Unavailable nights per month. I indexed the date so the query is workable.", ["Indexes", "Aggregation over a large table"]],
  } : {
    "01": ["Vista limpia sobre los datos crudos", "El precio llega como texto con símbolo y separador de miles. Lo limpio una sola vez en una vista y todas las consultas parten de ahí.", ["CREATE VIEW", "CAST", "NULLIF", "REPLACE"]],
    "02": ["Perfil de calidad en una pasada", "Antes de analizar: volumen, duplicados, vacíos y extremos.", ["Agregados condicionales", "SUM(expr IS NULL)"]],
    "03": ["¿Faltan los precios al azar?", "Si los anuncios sin precio son distintos, excluirlos sesga el resultado. Lo compruebo comparando su actividad.", ["CASE", "GROUP BY"]],
    "04": ["Mediana por municipio sin función MEDIAN", "SQLite no tiene MEDIAN(). La calculo con funciones de ventana, igual que en motores sin percentiles.", ["CTE", "ROW_NUMBER() OVER", "COUNT() OVER", "PARTITION BY"]],
    "05": ["Concentración del ingreso por deciles", "Qué parte del ingreso factura cada 10 % de anuncios, con el acumulado en la misma consulta.", ["NTILE", "SUM() OVER ()", "Acumulado con ventana"]],
    "06": ["Profesionalización de la oferta", "Anuncios y anfitriones según el tamaño de la cartera del anfitrión.", ["CASE", "COUNT(DISTINCT)", "% sobre total con ventana"]],
    "07": ["Crecimiento interanual", "Variación de la actividad año contra año sin autojoins.", ["LAG() OVER", "strftime", "CTE"]],
    "08": ["Calendario: 5,4 millones de filas", "Noches no disponibles por mes. Indexé la fecha para que la consulta sea viable.", ["Índices", "Agregado sobre tabla grande"]],
  };
  const sl = $("#sqlList");
  if (sl && S) {
    S.consultas.forEach(q => {
      const id = q.fichero.slice(0, 2), [title, why, skills] = META[id] || [q.fichero, "", []];
      const card = document.createElement("article"); card.className = "sql-card"; card.id = "sql-" + id;
      card.innerHTML = `<header><span class="eyebrow">${esc(q.fichero)}</span><h4>${esc(title)}</h4><p class="muted" style="font-size:.95rem">${esc(why)}</p>
        <div class="skills-used">${skills.map(s => `<span class="tag">${esc(s)}</span>`).join("")}</div>
        <div class="meta"><span>${q.columnas.length ? fmt(q.filas.length) + tr(" filas de resultado", " result rows") : tr("crea la vista", "creates the view")}</span><span>${fmt(q.ms)} ms</span></div></header>
        <details${id === "04" ? " open" : ""}><summary>${tr("Ver la consulta", "Show the query")}</summary></details>`;
      $("details", card).append(codeBlock(q.sql, "sql", q.fichero));
      if (q.columnas.length) {
        const rows = q.filas.slice(0, 13);
        const res = document.createElement("div"); res.className = "result";
        res.innerHTML = `<table><thead><tr>${q.columnas.map(c => `<th${typeof q.filas[0][q.columnas.indexOf(c)] === "number" ? ' class="r"' : ""}>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(v => typeof v === "number" ? `<td class="r">${fmt(v, Number.isInteger(v) ? 0 : (Math.abs(v) < 100 ? 1 : 0))}</td>` : `<td>${v == null ? "-" : esc(v)}</td>`).join("")}</tr>`).join("")}</tbody></table>`
          + (q.filas.length > rows.length ? `<p class="muted" style="font-size:.82rem;padding:8px 12px">${tr("Mostrando", "Showing")} ${fmt(rows.length)} ${tr("de", "of")} ${fmt(q.filas.length)} ${tr("filas", "rows")}.</p>` : "");
        card.append(res);
      }
      if (["02", "03", "04", "05", "06"].includes(id)) {
        const row = document.createElement("div"); row.className = "open-row";
        row.innerHTML = '<button class="btn sm ghost" type="button">' + tr("Ejecutar en la consola", "Run in the console") + ' <span class="arr">→</span></button>';
        $("button", row).addEventListener("click", () => window.PFconsole && window.PFconsole.load(q.sql, true));
        $("header", card).after(row);
      }
      sl.append(card);
    });
  }
  const ct = $("#cuadreTable tbody");
  if (ct && S) S.cuadres.forEach(c => {
    const fila = document.createElement("tr");
    fila.innerHTML = `<td class="wrap">${esc(tl(c.control))}${c.nota ? `<br><span class="muted small">${esc(tl(c.nota))}</span>` : ""}</td><td class="r">${esc(typeof c.sql === "number" ? fmt(c.sql, Number.isInteger(c.sql) ? 0 : 1) : tl(c.sql))}</td><td class="r">${esc(typeof c.pandas === "number" ? fmt(c.pandas, Number.isInteger(c.pandas) ? 0 : 1) : tl(c.pandas))}</td><td>${c.ok ? `<span class="ok-mark">✓ ${tr("cuadra", "matches")}</span>` : `<span class="ko-mark">✗ ${tr("revisar", "check")}</span>`}</td>`;
    ct.append(fila);
  });
  const au = $("#auditList");
  if (au && PF.audit) {
    au.innerHTML = `<p class="audit-total">${fmt(PF.audit.ok)} ${tr("de", "of")} ${fmt(PF.audit.total)} ${tr("controles superados", "checks passed")}</p><ul>` +
      PF.audit.controles.map(c => `<li><span class="st ${c.ok ? "ok" : "warn"}">${c.ok ? "✓" : "✗"}</span><span><b>${esc(EN && c.control_en || c.control)}</b><br><small>${esc(EN && c.detalle_en || c.detalle)}</small></span></li>`).join("") + "</ul>";
  }
  const carga = $("#cargaTable tbody");
  if (carga && S) Object.entries(S.carga).forEach(([t, v]) => {
    const fila = document.createElement("tr"); fila.innerHTML = `<td class="mono">${esc(t)}</td><td class="r">${fmt(v.filas)}</td><td class="r">${fmt(v.segundos, 1)} s</td>`; carga.append(fila);
  });
})();

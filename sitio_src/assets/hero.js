/* Hero interactivo de la página de inicio.
   Cuatro pestañas en vivo con datos reales: simulador, SQL, mapa y CSS editable.
   Sin librerías: HTML, CSS, SVG y JavaScript. */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fmt = (n, d = 0) => Number(n).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const demo = $("#demo"), PF = window.PF;
  if (!demo || !PF) return;

  /* ---------- Pestañas accesibles (flechas, Inicio, Fin) ---------- */
  const tabs = $$("[role=tab]", demo), panels = $$("[role=tabpanel]", demo);
  function show(i, focus) {
    tabs.forEach((t, j) => { t.setAttribute("aria-selected", i === j); t.tabIndex = i === j ? 0 : -1; });
    panels.forEach((p, j) => (p.hidden = i !== j));
    if (focus) tabs[i].focus();
  }
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => show(i));
    t.addEventListener("keydown", e => {
      const k = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (k != null) { e.preventDefault(); show((k + tabs.length) % tabs.length, true); }
    });
  });
  show(0);

  /* ---------- 1. Simulador ---------- */
  const S = PF.res.simulador;
  const mun = $("#hMun"), dor = $("#hDor"), sw = $("#hAttrs"), price = $("#hPrice"), bars = $("#hBars");
  Object.entries(S.municipio_n).sort((a, b) => b[1] - a[1]).slice(0, 10)
    .forEach(([m]) => mun.add(new Option(m, m, false, m === "Palma de Mallorca")));
  const [lo, hi] = S.num_rango.bedrooms; dor.min = lo; dor.max = hi; dor.value = 2;
  ["Vista al mar", "Piscina", "Aire acondicionado", "Barbacoa"].forEach((a, i) => {
    const l = document.createElement("label"); l.className = "switch";
    l.innerHTML = `<input type="checkbox" value="${esc(a)}"${i === 0 ? " checked" : ""}><span>${esc(a)}</span>`;
    sw.append(l);
  });
  const xb = on => {
    let v = S.const + (S.municipio[mun.value] || 0) + S.tipo["Apartamento"] + S.mes["2026-07"]
      + S.num.bedrooms * dor.value + S.num.accommodates * Math.min(10, dor.value * 2) + S.num.bathrooms * Math.max(1, Math.round(dor.value / 2));
    on.forEach(a => (v += S.atributos[a])); return v;
  };
  const eur = v => Math.exp(v) * S.smearing;
  let shown = 0, raf;
  function count(to) {
    cancelAnimationFrame(raf);
    if (reduce || !shown) { price.textContent = fmt(to) + " €"; shown = to; return; }   // la primera cifra, sin esperar a la animación
    const from = shown, t0 = performance.now();
    const step = t => { const k = Math.min(1, (t - t0) / 350), v = from + (to - from) * (1 - Math.pow(1 - k, 3)); price.textContent = fmt(v) + " €"; shown = v; if (k < 1) raf = requestAnimationFrame(step); };
    raf = requestAnimationFrame(step);
  }
  function sim() {
    $("#hDorOut").textContent = dor.value;
    const on = $$("input:checked", sw).map(i => i.value), base = eur(xb([])), total = eur(xb(on));
    count(total);
    const parts = [["Base", base, "var(--invert-muted)"]].concat(on.map(a => [a, total - eur(xb(on.filter(x => x !== a))), "var(--accent-mark)"]));
    const max = Math.max(...parts.map(p => p[1]));
    bars.innerHTML = parts.map(([n, v, c]) => `<div class="hb"><span>${esc(n)}</span><i style="--w:${(v / max * 100).toFixed(1)}%;--c:${c}"></i><b>${n === "Base" ? "" : "+"}${fmt(v)} €</b></div>`).join("");
  }
  [mun, dor, sw].forEach(x => x.addEventListener("input", sim));
  sw.addEventListener("change", sim);
  sim();

  /* ---------- 2. SQL con resultado real ---------- */
  const q4 = PF.sql.consultas.find(c => c.fichero.startsWith("04"));
  const sqlShort = "SELECT municipio, precio_mediano\nFROM ( -- mediana con ROW_NUMBER() OVER (PARTITION BY municipio ...) )\nORDER BY anuncios DESC\nLIMIT 5;";
  $("#hSql").innerHTML = window.PFhl ? window.PFhl(sqlShort, "sql") : esc(sqlShort);
  const out = $("#hSqlOut"), runB = $("#hRun");
  runB.addEventListener("click", () => {
    runB.disabled = true; out.innerHTML = '<p class="muted small pad">Ejecutando…</p>';
    const rows = q4.filas.slice(0, 5), max = Math.max(...rows.map(r => r[2]));
    setTimeout(() => {
      out.innerHTML = `<table><thead><tr><th>Municipio</th><th class="r">Anuncios</th><th class="r">Mediana €/noche</th></tr></thead><tbody>${rows.map((r, i) =>
        `<tr style="--d:${i * 70}ms" class="appear"><td>${esc(r[0])}</td><td class="r">${fmt(r[1])}</td><td class="r"><span class="cellbar" style="--w:${(r[2] / max * 100).toFixed(0)}%"></span>${fmt(r[2])}</td></tr>`).join("")}</tbody></table>
        <p class="muted small pad">Resultado real de la consulta 04 (${fmt(q4.ms)} ms en SQLite). <a href="mallorca.html#sql">Ejecútala tú en la consola →</a></p>`;
      runB.disabled = false;
    }, reduce ? 0 : 280);
  });

  /* ---------- 3. Mapa ---------- */
  // Mismo componente que la página del proyecto: tooltip flotante y texto fijo debajo
  if (window.PFmap) { window.PFmap.full($("#hMap"), $("#hTip")); window.PFmap.legend($("#hLegend")); }

  /* ---------- 4. CSS en vivo: edita la propia ventana ---------- */
  // El acento recorre la paleta del portafolio (--p4 a --p10) y se aplica a la ventana en tiempo real
  const css = $("#hCss"), ctrls = { radius: $("#cRadius"), border: $("#cBorder"), accent: $("#cAccent") };
  function paint() {
    const r = ctrls.radius.value, b = ctrls.border.value, a = ctrls.accent.value;
    demo.style.setProperty("--demo-radius", r + "px");
    demo.style.setProperty("--demo-border", b + "px");
    demo.style.setProperty("--accent-mark", `var(--p${a})`);
    $("#cRadiusOut").textContent = r + "px"; $("#cBorderOut").textContent = b + "px"; $("#cAccentOut").textContent = "--p" + a;
    const code = `.demo {\n  border-radius: ${r}px;\n  border-width: ${b}px;\n  --accent-mark: var(--p${a});\n}`;
    css.innerHTML = esc(code).replace(/(\d+px)/g, '<span class="n">$1</span>').replace(/^(\s*)([a-z-]+):/gm, '$1<span class="k">$2</span>:');
  }
  Object.values(ctrls).forEach(c => c.addEventListener("input", paint));
  $("#cReset").addEventListener("click", () => { ctrls.radius.value = 0; ctrls.border.value = 1; ctrls.accent.value = 6; paint(); });
  paint();

  /* ---------- Altura estable: la ventana mide lo que su pestaña más alta, así nada salta al cambiar ---------- */
  const cuerpo = $(".demo-body", demo);
  function igualar() {
    cuerpo.style.minHeight = "";
    const activo = panels.findIndex(p => !p.hidden);
    let alto = 0;
    panels.forEach(p => { p.hidden = false; alto = Math.max(alto, p.offsetHeight); p.hidden = true; });
    panels[activo].hidden = false;
    const pad = parseFloat(getComputedStyle(cuerpo).paddingTop) + parseFloat(getComputedStyle(cuerpo).paddingBottom);
    cuerpo.style.minHeight = (alto + pad) + "px";
  }
  igualar();
  if (document.fonts) document.fonts.ready.then(igualar);
  let t; addEventListener("resize", () => { clearTimeout(t); t = setTimeout(igualar, 150); });
})();

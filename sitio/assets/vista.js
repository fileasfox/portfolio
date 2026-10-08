/* Dashboard de mercado y página «Cómo presento los datos».
   Usa el tooltip (PFtip) y el mapa (PFmap) de app.js. Todo el texto entra con textContent. */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };
  const h = (n, a = {}, t) => { const e = document.createElement(n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };
  const fmt = (n, d = 0) => n == null || Number.isNaN(n) ? "-" : Number(n).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: "always" });
  const signo = (v, d = 0) => (v > 0 ? "+" : v < 0 ? "−" : "") + fmt(Math.abs(v), d);
  const mediana = a => { if (!a.length) return null; const s = Float64Array.from(a).sort(), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const suma = a => a.reduce((x, y) => x + y, 0);
  const tip = window.PFtip || { conTip: n => n, show() {}, hide() {} };
  const MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const r10 = v => v == null ? null : Math.round(v / 10) * 10;   // ingresos a decenas: sin precisión falsa
  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const mesCorto = s => { const [y, m] = s.split("-"); return MESES[+m - 1] + (m === "01" ? " " + y.slice(2) : ""); };

  // Dibuja al ancho real del contenedor y redibuja si cambia (el texto no encoge en móvil)
  function responsivo(svg, dibujar) {
    let ancho = 0;
    const pintar = (forzar) => {
      const w = Math.round(svg.getBoundingClientRect().width) || 600;
      if (!forzar && Math.abs(w - ancho) < 8) return;
      ancho = w; svg.replaceChildren(); dibujar(svg, Math.max(280, w));
    };
    pintar(true);
    if ("ResizeObserver" in window) { let t; new ResizeObserver(() => { clearTimeout(t); t = setTimeout(() => pintar(false), 120); }).observe(svg); }
    return () => pintar(true);
  }
  const lienzo = (svg, W, H) => { svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H); };
  const rejilla = (svg, x1, x2, y, solida) => svg.append(el("line", { x1, x2, y1: y, y2: y, stroke: "var(--line)", "stroke-dasharray": solida ? "0" : "3 4" }));

  // Barras horizontales: filas [{k, v, color, tip, onclick}]; si min no es 0 se ve el truco
  function barrasH(svg, W, filas, o = {}) {
    const L = o.L || Math.min(170, W * .36), Rr = W - (o.rpad || 64), rowH = o.rowH || 28, T = o.top || 4;
    const H = T + filas.length * rowH + (o.ref != null ? 24 : 6);
    lienzo(svg, W, H);
    const max = o.max || Math.max(...filas.map(f => f.v)) * 1.02, X = v => L + v / max * (Rr - L);
    if (o.ref != null) {
      svg.append(el("line", { x1: X(o.ref), x2: X(o.ref), y1: T - 2, y2: T + filas.length * rowH, stroke: "var(--ink)", "stroke-dasharray": "3 3" }));
      svg.append(el("text", { x: X(o.ref), y: H - 6, "text-anchor": "middle", class: "lbl" }, o.refTxt));
    }
    filas.forEach((f, i) => {
      const y = T + i * rowH, g = el("g", { class: "row" + (f.onclick ? " click" : "") });
      g.append(el("rect", { x: 0, y, width: W, height: rowH, class: "hit" }));
      g.append(el("text", { x: L - 10, y: y + rowH / 2 + 4, "text-anchor": "end", class: f.fuerte ? "lbl" : "" }, f.k));
      g.append(el("rect", { x: L, y: y + 5, width: Math.max(1, X(f.v) - L), height: rowH - 10, fill: f.color || "var(--y1)" }));
      g.append(el("text", { x: X(f.v) + 6, y: y + rowH / 2 + 4, class: "val" + (f.fuerte ? " lbl" : "") }, f.txt != null ? f.txt : fmt(f.v)));
      if (f.tip) tip.conTip(g, f.tip);
      if (f.onclick) { g.addEventListener("click", f.onclick); g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); f.onclick(); } }); }
      svg.append(g);
    });
  }

  /* ======================================================= DASHBOARD */
  const D = window.PD, panel = $("#panel");
  if (D && panel) {
    const A = D.anuncios, N = A.m.length, MUN = D.municipios;
    const TRAMOS = ["Particular", "2-4", "5-19", "20+"], TRAMOS_LARGO = ["particulares (1 anuncio)", "anfitriones con 2 a 4 anuncios", "gestores con 5 a 19 anuncios", "grandes gestores (20 o más)"];
    const st = { m: -1, t: -1, c: -1 };

    // Estado en el enlace: #m=Pollença&t=0&c=2
    try {
      const q = new URLSearchParams(location.hash.slice(1));
      const m = MUN.indexOf(q.get("m") || ""); if (m >= 0) st.m = m;
      const t = +q.get("t"); if (q.has("t") && t >= 0 && t < 4) st.t = t;
      const c = +q.get("c"); if (q.has("c") && c >= 0 && c < 4) st.c = c;
    } catch (e) { /* enlace mal formado: se ignora */ }

    const pasa = (i, s) => (s.m < 0 || A.m[i] === s.m) && (s.t < 0 || A.t[i] === s.t) && (s.c < 0 || A.c[i] === s.c);
    const clavePasa = (k, s) => { const [m, t, c] = k.split("|").map(Number); return (s.m < 0 || m === s.m) && (s.t < 0 || t === s.t) && (s.c < 0 || c === s.c); };

    function calcular(s) {
      const p = [], ing = [], sc = []; let n = 0;
      for (let i = 0; i < N; i++) if (pasa(i, s)) {
        n++; if (A.p[i] != null) p.push(A.p[i]); if (A.i[i] != null) ing.push(A.i[i]); if (A.s[i] != null) sc.push(A.s[i]);
      }
      const nd = Array(12).fill(0), no = Array(12).fill(0), rv = Array(24).fill(0);
      for (const k in D.cubos) if (clavePasa(k, s)) { const v = D.cubos[k]; for (let j = 0; j < 12; j++) { nd[j] += v[0][j]; no[j] += v[1][j]; } for (let j = 0; j < 24; j++) rv[j] += v[2][j]; }
      const occ = suma(no) ? suma(nd) / suma(no) * 100 : null, rev12 = suma(rv.slice(12)), rev0 = suma(rv.slice(0, 12));
      return { n, precios: p, precio: mediana(p), ingreso: r10(mediana(ing)), valor: sc.length ? suma(sc) / sc.length : null,
               occ, occMes: nd.map((v, j) => no[j] ? v / no[j] * 100 : null), rv, rev12, revYoY: rev0 ? (rev12 / rev0 - 1) * 100 : null, nPrecio: p.length };
    }
    const TOTAL = calcular({ m: -1, t: -1, c: -1 });

    // Por municipio con los filtros de anfitrión y capacidad (para mapa, ranking y CSV)
    function porMunicipio(s) {
      return MUN.map((nombre, m) => ({ nombre, m, ...calcular({ m, t: s.t, c: s.c }) }));
    }

    /* ---------- controles ---------- */
    const fMun = $("#fMun");
    MUN.map((nombre, m) => ({ nombre, m, n: A.m.filter(x => x === m).length })).sort((a, b) => a.nombre.localeCompare(b.nombre, "es"))
      .forEach(o => fMun.append(h("option", { value: o.m }, `${o.nombre} (${fmt(o.n)})`)));
    fMun.addEventListener("change", () => { st.m = fMun.value === "" ? -1 : +fMun.value; pintar(); });
    function segmentado(box, etiquetas, clave) {
      ["Todos", ...etiquetas].forEach((t, k) => {
        const b = h("button", { type: "button", class: "chip", "aria-pressed": "false" }, t);
        b.addEventListener("click", () => { st[clave] = k - 1; pintar(); });
        box.append(b);
      });
    }
    segmentado($("#fTramo"), TRAMOS, "t");
    segmentado($("#fCap"), D.capacidad, "c");
    $("#dReset").addEventListener("click", () => { st.m = st.t = st.c = -1; pintar(); });
    $("#fRank").addEventListener("change", () => pintar());
    const avisar = (b, txt) => { const o = b.textContent; b.textContent = txt; setTimeout(() => (b.textContent = o), 1800); };
    $("#dLink").addEventListener("click", e => {
      if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(() => avisar(e.target, "Enlace copiado"), () => avisar(e.target, "Copia la barra de direcciones"));
      else avisar(e.target, "Copia la barra de direcciones");
    });
    $("#dCsv").addEventListener("click", () => {
      const filas = porMunicipio(st).filter(r => r.n > 0).sort((a, b) => b.n - a.n);
      const q = v => /[;"\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v);
      const num = (v, d = 0) => v == null ? "" : v.toFixed(d).replace(".", ",");
      const csv = ["municipio;anuncios;precio_mediano_eur;noches_no_disponibles_pct;ingreso_mediano_eur;valoracion_media"]
        .concat(filas.map(r => [q(r.nombre), r.n, num(r.precio), num(r.occ, 1), num(r.ingreso), num(r.valor, 2)].join(";"))).join("\r\n");
      const url = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
      const a = h("a", { href: url, download: "mallorca-municipios.csv" }); document.body.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });

    /* ---------- piezas ---------- */
    const etiquetaSel = () => {
      const p = [];
      if (st.m >= 0) p.push(MUN[st.m]);
      if (st.t >= 0) p.push(TRAMOS_LARGO[st.t]);
      if (st.c >= 0) p.push(`viviendas para ${D.capacidad[st.c]} personas`);
      return p.length ? p.join(", ") : "Toda Mallorca";
    };
    const hayFiltro = () => st.m >= 0 || st.t >= 0 || st.c >= 0;

    function kpis(S) {
      const box = $("#dKpis"); box.replaceChildren();
      const pct = (a, b) => a == null || b == null ? null : (a / b - 1) * 100;
      const items = [
        ["Anuncios", fmt(S.n), hayFiltro() ? `${fmt(S.n / TOTAL.n * 100, 1)} % de la isla` : `${fmt(MUN.length)} municipios`, null],
        ["Precio mediano / noche", S.precio == null ? "-" : fmt(S.precio) + " €", null, pct(S.precio, TOTAL.precio), "%"],
        ["Noches no disponibles", S.occ == null ? "-" : fmt(S.occ, 1) + " %", null, S.occ == null ? null : S.occ - TOTAL.occ, "pp"],
        ["Ingreso mediano 12 meses", S.ingreso == null ? "-" : fmt(S.ingreso) + " €", null, pct(S.ingreso, TOTAL.ingreso), "%"],
        ["Reseñas 12 meses", fmt(S.rev12), S.revYoY == null ? "" : `${signo(S.revYoY, 1)} % frente al año anterior`, null],
        ["Valoración media", S.valor == null ? "-" : fmt(S.valor, 2) + " / 5", null, S.valor == null ? null : S.valor - TOTAL.valor, "pt"],
      ];
      items.forEach(([t, v, nota, delta, u]) => {
        const d = h("div", { class: "dk" });
        d.append(h("span", { class: "dk-t" }, t), h("b", {}, v));
        let txt = nota || "";
        if (delta != null && hayFiltro()) {
          const dec = u === "pt" ? 2 : 1, cero = Math.abs(delta) < (u === "pt" ? .005 : .05);
          txt = cero ? "igual que Mallorca" : `${signo(delta, dec)} ${u === "%" ? "%" : u === "pp" ? "puntos" : ""} frente a Mallorca`.replace("  ", " ");
          d.dataset.dir = cero ? "0" : delta > 0 ? "up" : "down";
        } else if (delta != null) txt = "referencia de la isla";
        d.append(h("span", { class: "dk-d" }, txt));
        box.append(d);
      });
      box.classList.toggle("low", S.n > 0 && S.n < 30);
    }

    function lectura(S) {
      const box = $("#dRead");
      if (!S.n) { box.textContent = "No hay anuncios con esta combinación de filtros."; return; }
      if (!hayFiltro()) {
        const pico = S.occMes.indexOf(Math.max(...S.occMes));
        box.textContent = `Mallorca: ${fmt(S.n)} anuncios con un precio mediano de ${fmt(S.precio)} € por noche. El ${fmt(S.occ, 0)} % de las noches del próximo año ya no está disponible, con el pico en ${MESES_LARGO[+D.meses_cal[pico].slice(5) - 1]}, y las reseñas crecen un ${fmt(S.revYoY, 0)} % interanual. Usa los filtros o haz clic en el mapa.`;
        return;
      }
      const dp = S.precio != null ? (S.precio / TOTAL.precio - 1) * 100 : null, doc = S.occ - TOTAL.occ;
      let t = `${etiquetaSel()}: ${fmt(S.n)} anuncios, el ${fmt(S.n / TOTAL.n * 100, 1)} % de la isla. `;
      if (dp != null) t += Math.abs(dp) < 2 ? "El precio mediano está en línea con Mallorca" : `El precio mediano es un ${fmt(Math.abs(dp), 0)} % ${dp > 0 ? "más alto" : "más bajo"} que en Mallorca`;
      t += Math.abs(doc) < 1 ? " y la disponibilidad es similar." : ` y tiene ${fmt(Math.abs(doc), 1)} puntos ${doc > 0 ? "más" : "menos"} de noches no disponibles.`;
      if (S.revYoY != null) t += ` La demanda, medida en reseñas, ${S.revYoY >= 0 ? "crece" : "cae"} un ${fmt(Math.abs(S.revYoY), 0)} % interanual.`;
      if (S.n < 30) t += " Atención: con menos de 30 anuncios estas cifras son poco fiables.";
      box.textContent = t;
    }

    let S = TOTAL, PM = porMunicipio(st);
    const redibujar = [];

    // Noches no disponibles por mes: selección frente a Mallorca, con retícula al pasar
    redibujar.push(responsivo($("#dOcc"), (svg, W) => {
      const L = 40, Rr = W - 14, T = 14, B = 190, H = 216, X = j => L + j * (Rr - L) / 11, Y = v => B - v / 100 * (B - T);
      lienzo(svg, W, H);
      [0, 25, 50, 75, 100].forEach(t => { rejilla(svg, L, Rr, Y(t), t === 0); svg.append(el("text", { x: L - 8, y: Y(t) + 4, "text-anchor": "end" }, t + " %")); });
      D.meses_cal.forEach((m, j) => { if (W >= 520 || j % 2 === 0) svg.append(el("text", { x: X(j), y: B + 18, "text-anchor": "middle" }, mesCorto(m))); });
      const linea = (serie, c, w) => svg.append(el("polyline", { points: serie.map((v, j) => v == null ? "" : X(j) + "," + Y(v)).join(" "), fill: "none", stroke: c, "stroke-width": w, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      linea(TOTAL.occMes, "var(--muted)", 2);
      if (hayFiltro()) linea(S.occMes, "var(--accent-mark)", 3);
      const cruz = el("line", { y1: T, y2: B, stroke: "var(--ink)", opacity: 0 }); svg.append(cruz);
      const pA = el("circle", { r: 4.5, fill: "var(--muted)", opacity: 0, stroke: "var(--surface)", "stroke-width": 2 }), pB = el("circle", { r: 5, fill: "var(--accent-mark)", opacity: 0, stroke: "var(--surface)", "stroke-width": 2 });
      svg.append(pA, pB);
      const capa = el("rect", { x: L, y: T, width: Rr - L, height: B - T, fill: "transparent", class: "hit-area" }); svg.append(capa);
      capa.addEventListener("pointermove", e => {
        const b = svg.getBoundingClientRect(), x = (e.clientX - b.left) * W / b.width, j = Math.max(0, Math.min(11, Math.round((x - L) / ((Rr - L) / 11))));
        cruz.setAttribute("x1", X(j)); cruz.setAttribute("x2", X(j)); cruz.setAttribute("opacity", .3);
        pA.setAttribute("cx", X(j)); pA.setAttribute("cy", Y(TOTAL.occMes[j])); pA.setAttribute("opacity", 1);
        if (hayFiltro() && S.occMes[j] != null) { pB.setAttribute("cx", X(j)); pB.setAttribute("cy", Y(S.occMes[j])); pB.setAttribute("opacity", 1); }
        tip.show(`${mesCorto(D.meses_cal[j])} ${D.meses_cal[j].slice(0, 4)}\n` + (hayFiltro() ? `Selección: ${fmt(S.occMes[j], 1)} %\n` : "") + `Mallorca: ${fmt(TOTAL.occMes[j], 1)} %`, e.clientX, e.clientY);
      });
      capa.addEventListener("pointerleave", () => { [cruz, pA, pB].forEach(n => n.setAttribute("opacity", 0)); tip.hide(); });
    }));

    // Mapa: color por precio mediano con los filtros de anfitrión y capacidad; clic = filtro de municipio
    const mapSvg = $("#dMap"), MAP = window.PF && window.PF.mapa, ESC = window.PFmap;
    function mapa() {
      if (!MAP || !ESC) return;
      mapSvg.replaceChildren(); mapSvg.setAttribute("viewBox", `-4 -4 ${MAP.w + 8} ${MAP.h + 8}`);
      const porNombre = Object.fromEntries(PM.map(r => [r.nombre, r]));
      let sel = null;
      MAP.municipios.forEach(mm => {
        const r = porNombre[mm.nombre], v = r && r.nPrecio >= 5 ? r.precio : null, activo = r && r.m === st.m;
        const p = el("path", { d: mm.d, fill: ESC.color(v), stroke: activo ? "var(--ink)" : "var(--surface)", "stroke-width": activo ? 3 : 1, class: "mun" + (st.m >= 0 && !activo ? " dim" : "") });
        tip.conTip(p, r ? `${mm.nombre}\n${v == null ? "Pocos precios publicados" : fmt(v) + " € de mediana"}\n${fmt(r.n)} anuncios · clic para ${activo ? "quitar el filtro" : "filtrar"}` : mm.nombre);
        if (r) {
          const ir = () => { st.m = activo ? -1 : r.m; pintar(); };
          p.addEventListener("click", ir);
          p.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); ir(); } });
        }
        if (activo) sel = p; else mapSvg.append(p);
      });
      if (sel) mapSvg.append(sel);   // el seleccionado encima, para que su borde se vea entero
    }
    ESC && ESC.legend($("#dMapLegend"));

    // Histograma: % de anuncios por tramo de 50 €; Mallorca en contorno gris, selección en rojo
    const BIN = 50, NB = 30;
    const histo = precios => { const c = Array(NB + 1).fill(0); precios.forEach(p => c[Math.min(NB, Math.floor(p / BIN))]++); return c.map(v => precios.length ? v / precios.length * 100 : 0); };
    const HT = histo(TOTAL.precios);
    redibujar.push(responsivo($("#dHist"), (svg, W) => {
      const L = 36, Rr = W - 8, T = 22, B = 170, H = 196, hs = hayFiltro() ? histo(S.precios) : HT, max = Math.max(8, ...hs, ...HT) * 1.1;
      const bw = (Rr - L) / (NB + 1), X = k => L + k * bw, Y = v => B - v / max * (B - T);
      lienzo(svg, W, H);
      [0, Math.round(max / 2), Math.floor(max)].forEach(t => { rejilla(svg, L, Rr, Y(t), t === 0); svg.append(el("text", { x: L - 6, y: Y(t) + 4, "text-anchor": "end" }, t + "%")); });
      hs.forEach((v, k) => {
        const r = el("rect", { x: X(k) + 1, y: Y(v), width: Math.max(1, bw - 2), height: B - Y(v), fill: hayFiltro() ? "var(--accent-mark)" : "var(--y2)", class: "mark" });
        tip.conTip(r, `${k === NB ? "≥ " + fmt(NB * BIN) : fmt(k * BIN) + "-" + fmt(k * BIN + BIN - 1)} €\n${fmt(v, 1)} % de los anuncios` + (hayFiltro() ? `\nMallorca: ${fmt(HT[k], 1)} %` : ""));
        svg.append(r);
      });
      if (hayFiltro()) svg.append(el("polyline", { points: HT.flatMap((v, k) => [`${X(k)},${Y(v)}`, `${X(k + 1)},${Y(v)}`]).join(" "), fill: "none", stroke: "var(--muted)", "stroke-width": 1.5 }));
      [0, 500, 1000, 1500].forEach(t => svg.append(el("text", { x: t === 1500 ? Rr : X(t / BIN), y: B + 16, "text-anchor": t === 1500 ? "end" : "start" }, (t === 1500 ? "≥ " : "") + fmt(t) + " €")));
      if (S.precio != null) {
        const xm = L + Math.min(S.precio, NB * BIN) / BIN * bw;
        svg.append(el("line", { x1: xm, x2: xm, y1: T - 6, y2: B, stroke: "var(--ink)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }));
        svg.append(el("text", { x: xm + 6, y: T - 8, class: "lbl" }, `mediana ${fmt(S.precio)} €`));
      }
    }));

    // Reseñas: barras por mes, últimos 12 en color y los 12 anteriores en gris detrás
    redibujar.push(responsivo($("#dRev"), (svg, W) => {
      const L = 44, Rr = W - 8, T = 12, B = 170, H = 196, R0 = S.rv.slice(0, 12), R1 = S.rv.slice(12), max = Math.max(1, ...S.rv) * 1.1;
      const gw = (Rr - L) / 12, Y = v => B - v / max * (B - T), meses = D.meses_rev.slice(12);
      lienzo(svg, W, H);
      [0, max / 2, max / 1.1].forEach(t => { rejilla(svg, L, Rr, Y(t), t === 0); svg.append(el("text", { x: L - 6, y: Y(t) + 4, "text-anchor": "end" }, fmt(t >= 1000 ? Math.round(t / 100) * 100 : Math.round(t)))); });
      meses.forEach((m, j) => {
        const x = L + j * gw, g = el("g", { class: "mark" });
        g.append(el("rect", { x: x + gw * .12, y: Y(R0[j]), width: gw * .5, height: B - Y(R0[j]), fill: "var(--y1)" }));
        g.append(el("rect", { x: x + gw * .38, y: Y(R1[j]), width: gw * .5, height: B - Y(R1[j]), fill: "var(--accent-mark)" }));
        const yoy = R0[j] ? (R1[j] / R0[j] - 1) * 100 : null;
        tip.conTip(g, `${mesCorto(m)} ${m.slice(0, 4)}: ${fmt(R1[j])} reseñas\nMismo mes del año anterior: ${fmt(R0[j])}` + (yoy == null ? "" : `\nVariación: ${signo(yoy, 1)} %`));
        svg.append(g);
        if (W >= 520 || j % 2 === 0) svg.append(el("text", { x: x + gw / 2, y: B + 16, "text-anchor": "middle" }, mesCorto(m)));
      });
    }));

    // Ranking de municipios (al menos 30 anuncios) por la métrica elegida; clic para filtrar
    redibujar.push(responsivo($("#dRank"), (svg, W) => {
      const met = $("#fRank").value, val = { n: r => r.n, p: r => r.precio, o: r => r.occ, i: r => r.ingreso }[met];
      const txt = { n: v => fmt(v), p: v => fmt(v) + " €", o: v => fmt(v, 1) + " %", i: v => fmt(v) + " €" }[met];
      const ok = PM.filter(r => r.n >= 30 && val(r) != null).sort((a, b) => val(b) - val(a));
      let top = ok.slice(0, 10);
      const selR = PM[st.m];
      if (selR && !top.includes(selR) && val(selR) != null) top = top.concat(selR);
      if (!top.length) { lienzo(svg, W, 40); svg.append(el("text", { x: 0, y: 24 }, "Ningún municipio llega a 30 anuncios con estos filtros.")); return; }
      barrasH(svg, W, top.map(r => ({
        k: r.nombre.replace("Palma de Mallorca", "Palma").replace("Sant Llorenç des Cardassar", "Sant Llorenç"), v: val(r), txt: txt(val(r)),
        color: r.m === st.m ? "var(--accent-mark)" : "var(--y1)", fuerte: r.m === st.m,
        tip: `${r.nombre}\n${fmt(r.n)} anuncios · ${fmt(r.precio)} € · ${fmt(r.occ, 1)} % no disp.\nClic para ${r.m === st.m ? "quitar el filtro" : "filtrar"}`,
        onclick: () => { st.m = r.m === st.m ? -1 : r.m; pintar(); },
      })), { L: Math.min(130, W * .34), rowH: 26, rpad: 70 });
    }));

    // Tabla por capacidad con los filtros de municipio y anfitrión
    function tabla() {
      const tb = $("#dTable tbody"); tb.replaceChildren();
      D.capacidad.forEach((cap, c) => {
        const r = calcular({ m: st.m, t: st.t, c }), tr = h("tr", { class: (st.c === c ? "on" : "") + (r.n < 30 ? " low" : "") });
        tr.append(h("th", { scope: "row" }, cap + " personas"), h("td", {}, fmt(r.n)), h("td", {}, r.precio == null ? "-" : fmt(r.precio) + " €"),
          h("td", {}, r.occ == null ? "-" : fmt(r.occ, 1) + " %"), h("td", {}, r.ingreso == null ? "-" : fmt(r.ingreso) + " €"), h("td", {}, r.valor == null ? "-" : fmt(r.valor, 2)));
        tb.append(tr);
      });
    }

    function pintar() {
      S = calcular(st); PM = porMunicipio(st);
      fMun.value = st.m < 0 ? "" : String(st.m);
      $$("#fTramo .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(k - 1 === st.t)));
      $$("#fCap .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(k - 1 === st.c)));
      $("#dReset").disabled = !hayFiltro();
      kpis(S); lectura(S); mapa(); tabla(); redibujar.forEach(f => f());
      $("#dFoot").textContent = `Fuente: Inside Airbnb, extracción del ${D.fecha.split("-").reverse().join("/")} (CC BY 4.0). ${fmt(S.nPrecio)} de ${fmt(S.n)} anuncios de la selección publican precio. Calendario: ${D.meses_cal[0]} a ${D.meses_cal[11]}. Reseñas: ${D.meses_rev[0]} a ${D.meses_rev[23]}.`;
      try {
        const q = new URLSearchParams();
        if (st.m >= 0) q.set("m", MUN[st.m]); if (st.t >= 0) q.set("t", st.t); if (st.c >= 0) q.set("c", st.c);
        history.replaceState(null, "", q.toString() ? "#" + q.toString() : location.pathname + location.search);
      } catch (e) { /* sin history: el panel funciona igual */ }
    }
    pintar();
  }

  /* ======================================================= VISUALIZACIÓN: antes y después */
  const PF = window.PF || {}, R = PF.res;
  if (R && $(".vz")) {
    const TOP = R.municipios_top_anuncios, TOTAL_N = R.calidad.anuncios, MED = R.mercado.precio_mediano_noche;
    const corto = s => s.replace("Palma de Mallorca", "Palma").replace("Santa Margalida", "Sta. Margalida");
    const ARCO = ["#e6194b", "#f58231", "#ffe119", "#bfef45", "#3cb44b", "#42d4f4", "#4363d8", "#911eb4", "#f032e6", "#a9a9a9", "#9a6324", "#800000", "#469990"];
    const titulo = (id, t) => { const n = $(id); if (n) n.textContent = t; };

    // 01 · Tarta → barras
    const top3 = suma(TOP.slice(0, 3).map(m => m.anuncios)) / TOTAL_N * 100;
    titulo("#t-tarta", `Tres municipios concentran el ${fmt(top3, 0)} % de los anuncios de la isla`);
    const resto = TOTAL_N - suma(TOP.map(m => m.anuncios));
    $$("svg[data-vz='tarta-mal']").forEach(s => responsivo(s, (svg, W) => {
      const datos = TOP.map(m => [m.municipio, m.anuncios]).concat([["Resto", resto]]);
      const estrecho = W < 420, r = estrecho ? W * .3 : Math.min(110, W * .22), cx = estrecho ? W / 2 : r + 10, cy = r + 10;
      const leyH = estrecho ? Math.ceil(datos.length / 2) * 17 + 10 : 0, H = Math.max(2 * r + 20, estrecho ? 0 : datos.length * 17 + 10) + leyH;
      lienzo(svg, W, H);
      let a0 = -Math.PI / 2;
      datos.forEach(([k, v], i) => {
        const a1 = a0 + v / TOTAL_N * 2 * Math.PI, big = a1 - a0 > Math.PI ? 1 : 0;
        svg.append(el("path", { d: `M${cx},${cy}L${cx + r * Math.cos(a0)},${cy + r * Math.sin(a0)}A${r},${r} 0 ${big} 1 ${cx + r * Math.cos(a1)},${cy + r * Math.sin(a1)}Z`, fill: ARCO[i], stroke: "#fff", "stroke-width": 1 }));
        a0 = a1;
        const lx = estrecho ? (i % 2) * W / 2 : 2 * r + 34, ly = estrecho ? 2 * r + 30 + Math.floor(i / 2) * 17 : 14 + i * 17;
        svg.append(el("rect", { x: lx, y: ly - 9, width: 10, height: 10, fill: ARCO[i] }));
        svg.append(el("text", { x: lx + 16, y: ly }, corto(k)));
      });
    }));
    $$("svg[data-vz='tarta-bien']").forEach(s => responsivo(s, (svg, W) => {
      const filas = TOP.slice(0, 8).map((m, i) => ({ k: corto(m.municipio), v: m.anuncios / TOTAL_N * 100, txt: fmt(m.anuncios / TOTAL_N * 100, 1) + " %", color: i < 3 ? "var(--accent-mark)" : "var(--y1)", fuerte: i < 3, tip: `${m.municipio}\n${fmt(m.anuncios)} anuncios` }));
      const nResto = TOTAL_N - suma(TOP.slice(0, 8).map(m => m.anuncios));
      filas.push({ k: "Otros 45", v: nResto / TOTAL_N * 100, txt: fmt(nResto / TOTAL_N * 100, 1) + " %", color: "var(--surface-2)", tip: `Los otros 45 municipios\n${fmt(nResto)} anuncios` });
      barrasH(svg, W, filas, { L: Math.min(120, W * .32), rowH: 26, rpad: 56 });
    }));

    // 02 · Eje truncado
    const seis = TOP.slice(0, 6), palma = TOP.find(m => /^Palma/.test(m.municipio));
    titulo("#t-eje", `Palma es un ${fmt((1 - palma.precio_mediano / MED) * 100, 0)} % más barata que la mediana de la isla`);
    $$("svg[data-vz='eje-mal']").forEach(s => responsivo(s, (svg, W) => {
      const L = 36, Rr = W - 6, T = 10, B = 190, H = 230, min = 250, max = 500, Y = v => B - (v - min) / (max - min) * (B - T), bw = (Rr - L) / seis.length;
      lienzo(svg, W, H);
      [250, 300, 350, 400, 450, 500].forEach(t => { rejilla(svg, L, Rr, Y(t), t === 250); svg.append(el("text", { x: L - 6, y: Y(t) + 4, "text-anchor": "end" }, t)); });
      seis.forEach((m, i) => {
        svg.append(el("rect", { x: L + i * bw + bw * .15, y: Y(m.precio_mediano), width: bw * .7, height: B - Y(m.precio_mediano), fill: "var(--y2)" }));
        const t = el("text", { x: L + i * bw + bw / 2, y: B + 16, "text-anchor": "end", transform: `rotate(-30 ${L + i * bw + bw / 2} ${B + 16})` }, corto(m.municipio));
        svg.append(t);
      });
    }));
    $$("svg[data-vz='eje-bien']").forEach(s => responsivo(s, (svg, W) => {
      const filas = seis.slice().sort((a, b) => b.precio_mediano - a.precio_mediano).map(m => ({
        k: corto(m.municipio), v: m.precio_mediano, txt: fmt(m.precio_mediano) + " €", color: m === palma ? "var(--accent-mark)" : "var(--y1)", fuerte: m === palma,
        tip: `${m.municipio}: ${fmt(m.precio_mediano)} € por noche\n${signo((m.precio_mediano / MED - 1) * 100, 0)} % frente a la isla` }));
      barrasH(svg, W, filas, { L: Math.min(110, W * .3), rowH: 28, rpad: 54, max: 520, ref: MED, refTxt: `Mallorca ${fmt(MED)} €` });
    }));

    // 03 · Media frente a mediana
    const V = PF.viz;
    if (V) {
      titulo("#t-media", `El anuncio típico ingresa ${fmt(V.ingreso_mediano)} € al año, no ${fmt(V.ingreso_medio)} €`);
      const k = $("#vzMediaMal");
      if (k) k.append(h("span", {}, "Ingreso medio por anuncio"), h("b", {}, fmt(V.ingreso_medio) + " €"), h("small", {}, "últimos 12 meses"));
    }
    const S5 = PF.sql && PF.sql.consultas.find(c => c.fichero.startsWith("05"));
    $$("svg[data-vz='media-bien']").forEach(s => responsivo(s, (svg, W) => {
      if (!S5) return;
      const iP = S5.columnas.indexOf("pct_ingreso"), rows = S5.filas, L = 34, B = 172, T = 46, H = 196, max = 40, bw = (W - L) / rows.length;
      lienzo(svg, W, H);
      if (V) {
        svg.append(el("text", { x: 0, y: 16, class: "lbl" }, `Mediana: ${fmt(V.ingreso_mediano)} € · media: ${fmt(V.ingreso_medio)} €`));
        svg.append(el("text", { x: 0, y: 32 }, `${fmt(V.bajo_media_pct, 0)} % de los anuncios ingresa menos que la media`));
      }
      [0, 20, 40].forEach(t => { const y = B - t / max * (B - T); rejilla(svg, L, W, y, t === 0); svg.append(el("text", { x: L - 6, y: y + 4, "text-anchor": "end" }, t + "%")); });
      rows.forEach((r, i) => {
        const v = r[iP], hh = v / max * (B - T), x = L + i * bw + bw * .15;
        const b = el("rect", { x, y: B - hh, width: bw * .7, height: hh, fill: i === 0 ? "var(--accent-mark)" : "var(--y1)", class: "mark" });
        tip.conTip(b, `Decil ${r[0]}: ${fmt(v, 1)} % del ingreso total`); svg.append(b);
        if (i === 0) svg.append(el("text", { x: x + bw * .8, y: B - hh + 12, class: "lbl" }, `el 10 % de arriba: ${fmt(v, 1)} %`));
        svg.append(el("text", { x: x + bw * .35, y: B + 16, "text-anchor": "middle" }, (W < 420 ? "" : "D") + r[0]));
      });
    }));

    // 04 · Doble eje → dos paneles alineados
    const ocho = TOP.slice(0, 8);
    titulo("#t-doble", "Tener más anuncios no significa cobrar más");
    $$("svg[data-vz='doble-mal']").forEach(s => responsivo(s, (svg, W) => {
      const L = 40, Rr = W - 40, T = 10, B = 180, H = 222, bw = (Rr - L) / ocho.length, maxN = 2400, minP = 240, maxP = 480;
      const YN = v => B - v / maxN * (B - T), YP = v => B - (v - minP) / (maxP - minP) * (B - T);
      lienzo(svg, W, H);
      [0, 800, 1600, 2400].forEach(t => { rejilla(svg, L, Rr, YN(t), t === 0); svg.append(el("text", { x: L - 6, y: YN(t) + 4, "text-anchor": "end" }, fmt(t))); });
      [240, 320, 400, 480].forEach(t => svg.append(el("text", { x: Rr + 6, y: YP(t) + 4, fill: ARCO[0] }, t + "€")));
      ocho.forEach((m, i) => {
        svg.append(el("rect", { x: L + i * bw + bw * .15, y: YN(m.anuncios), width: bw * .7, height: B - YN(m.anuncios), fill: ARCO[6] }));
        svg.append(el("text", { x: L + i * bw + bw / 2, y: B + 14, "text-anchor": "end", transform: `rotate(-35 ${L + i * bw + bw / 2} ${B + 14})` }, corto(m.municipio).slice(0, 9)));
      });
      svg.append(el("polyline", { points: ocho.map((m, i) => `${L + i * bw + bw / 2},${YP(m.precio_mediano)}`).join(" "), fill: "none", stroke: ARCO[0], "stroke-width": 3 }));
    }));
    $$("svg[data-vz='doble-bien']").forEach(s => responsivo(s, (svg, W) => {
      const L = Math.min(118, W * .3), gap = 18, pw = (W - L - gap) / 2, rowH = 24, T = 22, H = T + ocho.length * rowH + 6;
      lienzo(svg, W, H);
      const maxN = Math.max(...ocho.map(m => m.anuncios)), maxP = 520;
      svg.append(el("text", { x: L, y: 12, class: "lbl" }, "Anuncios"), el("text", { x: L + pw + gap, y: 12, class: "lbl" }, "Precio mediano"));
      ocho.forEach((m, i) => {
        const y = T + i * rowH, g = el("g", { class: "row" });
        g.append(el("rect", { x: 0, y, width: W, height: rowH, class: "hit" }));
        g.append(el("text", { x: L - 8, y: y + rowH / 2 + 4, "text-anchor": "end" }, corto(m.municipio)));
        const wN = m.anuncios / maxN * (pw - 46), wP = m.precio_mediano / maxP * (pw - 46);
        g.append(el("rect", { x: L, y: y + 5, width: wN, height: rowH - 10, fill: "var(--y1)" }));
        g.append(el("text", { x: L + wN + 5, y: y + rowH / 2 + 4, class: "val" }, fmt(m.anuncios)));
        const caro = m.precio_mediano >= MED;
        g.append(el("rect", { x: L + pw + gap, y: y + 5, width: wP, height: rowH - 10, fill: caro ? "var(--accent-mark)" : "var(--y1)" }));
        g.append(el("text", { x: L + pw + gap + wP + 5, y: y + rowH / 2 + 4, class: "val" }, fmt(m.precio_mediano) + " €"));
        tip.conTip(g, `${m.municipio}\n${fmt(m.anuncios)} anuncios · ${fmt(m.precio_mediano)} € de mediana\n${caro ? "Por encima" : "Por debajo"} de la mediana de la isla`);
        svg.append(g);
      });
    }));

    // 05 · Color en el mapa: arcoíris frente a secuencial
    const MAPD = PF.mapa, ESC = window.PFmap;
    const cortes = [250, 300, 350, 400, 450, 500];
    const arco = v => v == null ? "#ddd" : ARCO[[0, 4, 2, 6, 1, 8, 3][cortes.filter(b => v >= b).length]];
    const pintaMapa = (svg, color) => {
      if (!MAPD) return;
      svg.setAttribute("viewBox", `-4 -4 ${MAPD.w + 8} ${MAPD.h + 8}`);
      MAPD.municipios.forEach(m => {
        const p = el("path", { d: m.d, fill: color(m.precio_mediano), stroke: "var(--surface)", "stroke-width": 1, class: "mun" });
        tip.conTip(p, m.precio_mediano == null ? m.nombre : `${m.nombre}\n${fmt(m.precio_mediano)} € de mediana`);
        svg.append(p);
      });
    };
    $$("svg[data-vz='color-mal']").forEach(s => pintaMapa(s, arco));
    $$("svg[data-vz='color-bien']").forEach(s => ESC && pintaMapa(s, ESC.color));
    const legMal = $("#vzLegMal");
    if (legMal) ["< 250", "250-299", "300-349", "350-399", "400-449", "450-499", "≥ 500"].forEach((t, i) => {
      const sp = h("span"), ic = h("i"); ic.style.background = ARCO[[0, 4, 2, 6, 1, 8, 3][i]]; ic.style.height = "10px"; sp.append(ic, t + " €"); legMal.append(sp);
    });
    ESC && ESC.legend($("#vzLegBien"));

    // 06 · Tablas
    const tm = $("#vzTablaMal"), tbn = $("#vzTablaBien");
    if (tm) {
      const cols = ["municipio", "anuncios", "precio_mediano", "ingreso_mediano", "piscina_pct"];
      const trh = h("tr"); cols.forEach(c => trh.append(h("th", {}, c))); tm.tHead.append(trh);
      TOP.slice().sort((a, b) => a.municipio.localeCompare(b.municipio)).slice(0, 8).forEach(m => {
        const tr = h("tr"); cols.forEach(c => tr.append(h("td", {}, typeof m[c] === "number" ? m[c].toFixed(1) : m[c]))); tm.tBodies[0].append(tr);
      });
    }
    if (tbn) {
      const trh = h("tr");
      [["Municipio", ""], ["Anuncios", "num"], ["Precio mediano", "num"], ["frente a la isla", "num"], ["Ingreso mediano", "num"]].forEach(([t, c]) => trh.append(h("th", { scope: "col", class: c }, t)));
      tbn.tHead.append(trh);
      const maxN = TOP[0].anuncios;
      TOP.slice(0, 8).forEach(m => {
        const tr = h("tr"), d = (m.precio_mediano / MED - 1) * 100;
        const cN = h("td", { class: "num" }), barra = h("span", { class: "inbar", "aria-hidden": "true" }); barra.style.setProperty("--w", (m.anuncios / maxN * 100).toFixed(1) + "%");
        cN.append(barra, document.createTextNode(fmt(m.anuncios)));
        const cD = h("td", { class: "num " + (d > 2 ? "up" : d < -2 ? "down" : "") }, Math.abs(d) <= 2 ? "≈" : signo(d, 0) + " %");
        tr.append(h("th", { scope: "row" }, m.municipio), cN, h("td", { class: "num" }, fmt(m.precio_mediano) + " €"), cD, h("td", { class: "num" }, fmt(m.ingreso_mediano) + " €"));
        tbn.tBodies[0].append(tr);
      });
    }
  }
})();

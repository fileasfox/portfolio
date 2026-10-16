/* Proyecto «Turismo, calor y agua en Mallorca»: gráficos y explorador por año.
   Lee window.PF.clima (resultados.json del análisis). Todo el texto entra con textContent. */
(function () {
  "use strict";
  const C = window.PF && window.PF.clima;
  if (!C || !document.querySelector("[data-clima]")) return;
  const $ = (s, r = document) => r.querySelector(s);
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}, t) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };
  const EN = document.documentElement.lang === "en";
  const tr = (es, en) => EN ? en : es;
  const fmt = (n, d = 0) => n == null ? "-" : Number(n).toLocaleString(EN ? "en-GB" : "es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: "always" });
  const pc = (n, d = 0) => fmt(n, d) + (EN ? "%" : " %");
  const grados = (n, d = 1) => (n > 0 ? "+" : n < 0 ? "−" : "") + fmt(Math.abs(n), d) + " °C";
  const tip = window.PFtip || { conTip: n => n, show() {}, hide() {} };
  const MES = EN ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] : ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  function responsivo(svg, dibujar) {
    let ancho = 0;
    const pintar = forzar => {
      const w = Math.round(svg.getBoundingClientRect().width) || 640;
      if (!forzar && Math.abs(w - ancho) < 8) return;
      ancho = w; svg.replaceChildren(); dibujar(svg, Math.max(300, w));
    };
    pintar(true);
    if ("ResizeObserver" in window) { let t; new ResizeObserver(() => { clearTimeout(t); t = setTimeout(() => pintar(false), 120); }).observe(svg); }
    // El tema cambia los colores de la escala: se redibuja
    new MutationObserver(() => pintar(true)).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }
  const lienzo = (svg, W, H) => { svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("height", H); };
  const linea = (svg, x1, x2, y1, y2, a = {}) => svg.append(el("line", { x1, x2, y1, y2, stroke: "var(--line)", ...a }));
  const texto = (svg, x, y, t, a = {}) => svg.append(el("text", { x, y, ...a }, t));

  /* ---------- 1. Franjas de calentamiento (estilo Ed Hawkins) ---------- */
  // Escala divergente ColorBrewer RdBu de 11 clases: azul = más frío que la normal 1991-2020, rojo = más cálido
  const RDBU = ["#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0", "#f7f7f7", "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"];
  const colorAnom = v => RDBU[Math.max(0, Math.min(10, Math.round(v / 0.4) + 5))];
  const franjas = $("#cStripes");
  if (franjas) responsivo(franjas, (svg, W) => {
    const A = C.anual, H = 96, bw = W / A.length;
    lienzo(svg, W, H + 22);
    A.forEach((r, i) => {
      const rect = el("rect", { x: i * bw, y: 0, width: bw + .6, height: H, fill: colorAnom(r.palma), class: "mark" });
      tip.conTip(rect, `${r.anio}: ${grados(r.palma, 2)}\n${tr("frente a la normal 1991-2020", "vs the 1991-2020 normal")}`);
      svg.append(rect);
    });
    texto(svg, 0, H + 16, A[0].anio);
    texto(svg, W - 2, H + 16, A[A.length - 1].anio, { "text-anchor": "end" });
  });

  /* ---------- 2. Anomalía de Palma frente al planeta, con tendencias ---------- */
  const anom = $("#cAnom");
  if (anom) responsivo(anom, (svg, W) => {
    const A = C.anual, L = 44, Rr = W - (W < 560 ? 92 : 128), T = 16, B = 230, H = 258;
    const x0 = A[0].anio, x1 = A[A.length - 1].anio, X = a => L + (a - x0) / (x1 - x0) * (Rr - L), Y = v => B - (v + 2) / 4.5 * (B - T);
    lienzo(svg, W, H);
    [-2, -1, 0, 1, 2].forEach(v => { linea(svg, L, Rr, Y(v), Y(v), v === 0 ? { stroke: css("--ink"), "stroke-width": 1 } : { "stroke-dasharray": "3 4" }); texto(svg, L - 8, Y(v) + 4, (v > 0 ? "+" : "") + v + " °C", { "text-anchor": "end" }); });
    [1980, 1990, 2000, 2010, 2020].forEach(a => texto(svg, X(a), B + 18, a, { "text-anchor": "middle" }));
    const serie = (k, color, w) => svg.append(el("polyline", { points: A.map(r => X(r.anio) + "," + Y(r[k])).join(" "), fill: "none", stroke: color, "stroke-width": w, "stroke-linejoin": "round" }));
    serie("global", "var(--y2)", 2);
    serie("palma", "var(--accent)", 2.5);
    // Rectas de tendencia (pendiente por década del análisis, ancladas en la media de cada serie)
    const recta = (k, pend, color) => {
      const xm = A.reduce((s, r) => s + r.anio, 0) / A.length, ym = A.reduce((s, r) => s + r[k], 0) / A.length;
      svg.append(el("line", { x1: X(x0), x2: X(x1), y1: Y(ym + pend / 10 * (x0 - xm)), y2: Y(ym + pend / 10 * (x1 - xm)), stroke: color, "stroke-width": 1.5, "stroke-dasharray": "6 4" }));
    };
    recta("palma", C.tendencias.palma_c_decada.pendiente, "var(--accent)");
    recta("global", C.tendencias.global_c_decada.pendiente, "var(--y2)");
    const u = A[A.length - 1];
    texto(svg, Rr + 8, Y(u.palma) + 4, tr("Palma ", "Palma ") + grados(u.palma), { class: "lbl", fill: "var(--accent)" });
    texto(svg, Rr + 8, Y(u.global) + 4, tr("Planeta ", "Planet ") + grados(u.global), { class: "lbl" });
    A.forEach(r => {
      const c = el("circle", { cx: X(r.anio), cy: Y(r.palma), r: 7, fill: "transparent", class: "mark" });
      tip.conTip(c, `${r.anio}\nPalma: ${grados(r.palma, 2)}\n${tr("Planeta", "Planet")}: ${grados(r.global, 2)}`);
      svg.append(c);
    });
  });

  /* ---------- 3. Noches tropicales por año ---------- */
  const trop = $("#cTrop");
  if (trop) responsivo(trop, (svg, W) => {
    const A = C.anual, L = 36, Rr = W - 8, T = 18, B = 200, H = 226, max = 130, bw = (Rr - L) / A.length;
    const Y = v => B - v / max * (B - T);
    lienzo(svg, W, H);
    [0, 30, 60, 90, 120].forEach(v => { linea(svg, L, Rr, Y(v), Y(v), v ? { "stroke-dasharray": "3 4" } : {}); texto(svg, L - 6, Y(v) + 4, v, { "text-anchor": "end" }); });
    const rec = C.tropicales.record;
    A.forEach((r, i) => {
      const b = el("rect", { x: L + i * bw + 1, y: Y(r.tropicales), width: Math.max(1, bw - 2), height: B - Y(r.tropicales), fill: r.anio === rec[1] ? "var(--accent)" : "var(--seq2)", class: "mark" });
      tip.conTip(b, `${r.anio}: ${fmt(r.tropicales)} ${tr("noches tropicales", "tropical nights")}`);
      svg.append(b);
      if (r.anio % 10 === 0) texto(svg, L + i * bw + bw / 2, B + 18, r.anio, { "text-anchor": "middle" });
    });
    // Media móvil de 10 años: la tendencia sin el ruido de cada verano
    const mm = A.map((r, i) => i < 9 ? null : A.slice(i - 9, i + 1).reduce((s, x) => s + x.tropicales, 0) / 10);
    svg.append(el("polyline", { points: mm.map((v, i) => v == null ? "" : `${L + i * bw + bw / 2},${Y(v)}`).join(" "), fill: "none", stroke: "var(--ink)", "stroke-width": 2 }));
    const yN = Y(C.tropicales.normal_1991_2020);
    texto(svg, L + 6, T + 2, tr(`Récord: ${rec[0]} en ${rec[1]}`, `Record: ${rec[0]} in ${rec[1]}`), { class: "lbl", fill: "var(--accent)" });
    linea(svg, L, Rr, yN, yN, { stroke: "var(--muted)", "stroke-dasharray": "2 3" });
    texto(svg, Rr - 4, yN - 6, tr("normal 1991-2020", "1991-2020 normal"), { "text-anchor": "end" });
  });

  /* ---------- 4. Mapa de calor: pernoctaciones por mes y año ---------- */
  const heat = $("#cHeat");
  if (heat) responsivo(heat, (svg, W) => {
    const filas = Object.entries(C.turismo.matriz).filter(([a]) => +a >= 1999), L = 42, T = 22, ch = 15, cw = (W - L) / 12;
    const H = T + filas.length * ch + 6;
    lienzo(svg, W, H);
    MES.forEach((m, j) => texto(svg, L + j * cw + cw / 2, 14, W < 520 ? m[0] : m, { "text-anchor": "middle" }));
    // Escala secuencial de un solo tono, en millones de pernoctaciones
    const cortes = [0.5, 2, 4, 6, 7.5], escala = ["var(--surface)", "var(--seq1)", "var(--seq2)", "var(--seq3)", "var(--seq4)", "var(--ink)"];
    filas.forEach(([a, meses], i) => {
      texto(svg, L - 6, T + i * ch + ch - 4, a, { "text-anchor": "end", style: "font-size:10px" });
      meses.forEach((v, j) => {
        const k = v == null ? -1 : cortes.filter(c => v / 1e6 >= c).length;
        const r = el("rect", { x: L + j * cw + 1, y: T + i * ch + 1, width: cw - 2, height: ch - 2, rx: 2, fill: k < 0 ? "transparent" : escala[k], stroke: k < 0 ? "var(--line)" : "none", class: "mark" });
        tip.conTip(r, v == null ? `${MES[j]} ${a}: ${tr("sin dato", "no data")}` : `${MES[j]} ${a}\n${fmt(v / 1e6, 2)} ${tr("millones de pernoctaciones", "million hotel nights")}`);
        svg.append(r);
      });
    });
    const ley = $("#cHeatLeyenda");
    if (ley && !ley.childElementCount) ["< 0,5", "0,5-2", "2-4", "4-6", "6-7,5", "> 7,5"].forEach((t, i) => {
      const s = document.createElement("span"), c = document.createElement("i");
      c.style.background = escala[i]; c.style.height = "10px"; c.style.width = "16px"; c.style.border = "1px solid var(--line)";
      s.append(c, (EN ? t.replace(/,/g, ".") : t) + tr(" M", "M")); ley.append(s);
    });
  });

  /* ---------- 5. Dos paneles alineados: peso de cada mes y noches tropicales de cada mes ---------- */
  const perfil = $("#cPerfil");
  if (perfil) responsivo(perfil, (svg, W) => {
    const E = C.exposicion, L = 40, Rr = W - 8, gw = (Rr - L) / 12, H = 380, P1 = [26, 160], P2 = [228, 352];
    lienzo(svg, W, H);
    const panel = ([t, b], max, titulo, claves, paso) => {
      const Y = v => b - v / max * (b - t);
      texto(svg, L, t - 10, titulo, { class: "lbl" });
      for (let v = 0; v <= max; v += paso) { linea(svg, L, Rr, Y(v), Y(v), v ? { "stroke-dasharray": "3 4" } : {}); texto(svg, L - 6, Y(v) + 4, v + (EN ? "%" : " %"), { "text-anchor": "end" }); }
      return Y;
    };
    // Panel 1: % de las pernoctaciones del año que caen en cada mes
    let Y = panel(P1, 20, tr("Peso de cada mes en las pernoctaciones del año", "Each month's share of the year's hotel nights"), null, 5);
    MES.forEach((m, j) => {
      [["perfil_antes", "var(--y1)", 0], ["perfil_ahora", "var(--accent)", 1]].forEach(([k, col, o]) => {
        const v = E[k].pernoct_pct[j], x = L + j * gw + gw * (.16 + o * .34);
        const b = el("rect", { x, y: Y(v), width: gw * .32, height: P1[1] - Y(v), fill: col, class: "mark" });
        tip.conTip(b, `${MES[j]} ${k === "perfil_antes" ? E.antes[0] + "-" + E.antes[3] : E.ahora[0] + "-" + E.ahora[3]}: ${pc(v, 1)} ${tr("de las pernoctaciones", "of hotel nights")}`);
        svg.append(b);
      });
    });
    // Panel 2: % de las noches del mes que son tropicales
    Y = panel(P2, 100, tr("Noches tropicales dentro de cada mes", "Tropical nights within each month"), null, 50);
    [["perfil_antes", "var(--y2)"], ["perfil_ahora", "var(--accent)"]].forEach(([k, col]) => {
      svg.append(el("polyline", { points: E[k].tropicales_pct.map((v, j) => `${L + j * gw + gw / 2},${Y(v)}`).join(" "), fill: "none", stroke: col, "stroke-width": 2.5, "stroke-linejoin": "round" }));
      E[k].tropicales_pct.forEach((v, j) => {
        const c = el("circle", { cx: L + j * gw + gw / 2, cy: Y(v), r: 4, fill: col, stroke: "var(--card)", "stroke-width": 1.5, class: "mark" });
        tip.conTip(c, `${MES[j]} ${k === "perfil_antes" ? E.antes[0] + "-" + E.antes[3] : E.ahora[0] + "-" + E.ahora[3]}: ${pc(v, 0)} ${tr("de las noches son tropicales", "of nights are tropical")}`);
        svg.append(c);
      });
    });
    MES.forEach((m, j) => texto(svg, L + j * gw + gw / 2, H - 6, W < 520 ? m[0] : m, { "text-anchor": "middle" }));
  });

  /* ---------- 6. Cascada: de dónde sale el aumento de la exposición ---------- */
  const desc = $("#cDescomp");
  if (desc) responsivo(desc, (svg, W) => {
    const E = C.exposicion, L = W < 520 ? 104 : 150, Rr = W - 60, rowH = 40, T = 6, max = 70;
    const X = v => L + v / max * (Rr - L);
    const pasos = [
      [tr(`${E.antes[0]}-${E.antes[3]}`, `${E.antes[0]}-${E.antes[3]}`), 0, E.pct_antes, "var(--y1)", pc(E.pct_antes, 1)],
      [tr("Más calor", "More heat"), E.pct_antes, E.efecto_clima, "var(--accent)", "+" + fmt(E.efecto_clima, 1)],
      [tr("Calendario turístico", "Tourism calendar"), E.pct_antes + E.efecto_clima, E.efecto_temporada, "var(--seq2)", "+" + fmt(E.efecto_temporada, 1)],
      [tr("Los dos a la vez", "Both together"), E.pct_antes + E.efecto_clima + E.efecto_temporada, E.interaccion, "var(--seq1)", "+" + fmt(E.interaccion, 1)],
      [tr(`${E.ahora[0]}-${E.ahora[3]}`, `${E.ahora[0]}-${E.ahora[3]}`), 0, E.pct_ahora, "var(--ink)", pc(E.pct_ahora, 1)],
    ];
    const H = T + pasos.length * rowH + 24;
    lienzo(svg, W, H);
    [0, 20, 40, 60].forEach(v => { linea(svg, X(v), X(v), T, H - 22, { "stroke-dasharray": v ? "3 4" : "0" }); texto(svg, X(v), H - 6, pc(v), { "text-anchor": "middle" }); });
    pasos.forEach(([k, ini, v, col, et], i) => {
      const y = T + i * rowH + 8;
      texto(svg, L - 10, y + 16, k, { "text-anchor": "end", class: i === 0 || i === 4 ? "lbl" : "" });
      const r = el("rect", { x: X(ini), y, width: Math.max(2, X(ini + v) - X(ini)), height: rowH - 16, rx: 4, fill: col, class: "mark" });
      tip.conTip(r, `${k}: ${et}${i && i < 4 ? tr(" puntos", " points") : ""}`);
      svg.append(r);
      texto(svg, X(ini + v) + 8, y + 16, et + (i && i < 4 ? tr(" pt", " pts") : ""), { class: "lbl" });
    });
  });

  /* ---------- 7. Reservas de agua: serie mensual ---------- */
  const resv = $("#cReservas");
  if (resv) responsivo(resv, (svg, W) => {
    const S = C.reservas.mensual, L = 40, Rr = W - 10, T = 16, B = 210, H = 236, n = S.length;
    const X = i => L + i / (n - 1) * (Rr - L), Y = v => B - (v - 30) / 50 * (B - T);
    lienzo(svg, W, H);
    [30, 40, 50, 60, 70, 80].forEach(v => { linea(svg, L, Rr, Y(v), Y(v), v > 30 ? { "stroke-dasharray": "3 4" } : {}); texto(svg, L - 6, Y(v) + 4, pc(v), { "text-anchor": "end" }); });
    S.forEach(([p], i) => { if (p.endsWith("-01") && +p.slice(0, 4) % 2 === 0) texto(svg, X(i), B + 18, p.slice(0, 4), { "text-anchor": "middle" }); });
    svg.append(el("path", { d: `M${X(0)},${B} ` + S.map(([, v], i) => `L${X(i)},${Y(v)}`).join(" ") + ` L${X(n - 1)},${B} Z`, fill: "var(--accent-soft)" }));
    svg.append(el("polyline", { points: S.map(([, v], i) => `${X(i)},${Y(v)}`).join(" "), fill: "none", stroke: "var(--accent)", "stroke-width": 2.2, "stroke-linejoin": "round" }));
    // Mínimo de cada año hidrológico marcado
    C.reservas.anual.forEach(r => {
      const i = S.findIndex(([p]) => p === r.mes_minimo);
      if (i < 0) return;
      const c = el("circle", { cx: X(i), cy: Y(r.minimo), r: 4.5, fill: "var(--ink)", stroke: "var(--card)", "stroke-width": 1.5, class: "mark" });
      tip.conTip(c, `${tr("Mínimo del año hidrológico", "Low point of hydrological year")} ${r.anio}: ${pc(r.minimo, 1)} (${r.mes_minimo})`);
      svg.append(c);
    });
    const u = S[n - 1];
    svg.append(el("circle", { cx: X(n - 1), cy: Y(u[1]), r: 5, fill: "var(--accent)", stroke: "var(--card)", "stroke-width": 2 }));
    texto(svg, X(n - 1) - 8, Y(u[1]) + 18, `${u[0]}: ${pc(u[1], 1)}`, { class: "lbl", "text-anchor": "end" });
    S.forEach(([p, v, lluvia], i) => {
      const h = el("rect", { x: X(i) - (Rr - L) / n / 2, y: T, width: (Rr - L) / n, height: B - T, fill: "transparent", class: "mark" });
      tip.conTip(h, `${p}: ${pc(v, 1)}\n${tr("Lluvia del mes", "Rain that month")}: ${fmt(lluvia)} mm`);
      svg.append(h);
    });
  });

  /* ---------- 8. Caída de cada verano frente a las pernoctaciones de ese verano ---------- */
  const caida = $("#cCaida");
  if (caida) responsivo(caida, (svg, W) => {
    const A = C.reservas.anual, L = 36, Rr = W - 8, T = 28, B = 170, H = 222, bw = (Rr - L) / A.length, max = 14;
    const Y = v => B - v / max * (B - T);
    lienzo(svg, W, H);
    [0, 5, 10].forEach(v => { linea(svg, L, Rr, Y(v), Y(v), v ? { "stroke-dasharray": "3 4" } : {}); texto(svg, L - 6, Y(v) + 4, v, { "text-anchor": "end" }); });
    A.forEach((r, i) => {
      const x = L + i * bw + bw * .18, es2020 = r.anio === 2020;
      const b = el("rect", { x, y: Y(r.caida_verano), width: bw * .64, height: B - Y(r.caida_verano), rx: 4, fill: es2020 ? "var(--accent)" : "var(--y1)", class: "mark" });
      tip.conTip(b, `${r.anio}: ${tr("las reservas bajan", "reserves drop")} ${fmt(r.caida_verano, 1)} ${tr("puntos de mayo a septiembre", "points from May to September")}\n${fmt(r.pernoct_may_sep / 1e6, 1)} ${tr("M de pernoctaciones en esos meses", "M hotel nights in those months")}`);
      svg.append(b);
      texto(svg, x + bw * .32, Y(r.caida_verano) - 6, fmt(r.caida_verano, 1), { "text-anchor": "middle", class: es2020 ? "lbl" : "" });
      texto(svg, x + bw * .32, B + 16, r.anio, { "text-anchor": "middle" });
      texto(svg, x + bw * .32, B + 32, fmt(r.pernoct_may_sep / 1e6, 0) + tr(" M", "M"), { "text-anchor": "middle", fill: es2020 ? "var(--accent)" : "var(--muted)" });
    });
    texto(svg, L, 14, tr("Puntos de reservas perdidos de mayo a septiembre · pernoctaciones de esos meses debajo", "Reserve points lost May to September · hotel nights in those months below"), { class: "lbl" });
  });

  /* ---------- 9. Explorador por año ---------- */
  const rango = $("#cAnio");
  if (rango) {
    const porAnio = Object.fromEntries(C.anual.map(r => [r.anio, r]));
    const pern = Object.fromEntries(C.turismo.anual);
    const expo = Object.fromEntries(C.exposicion.anual);
    const resA = Object.fromEntries(C.reservas.anual.map(r => [r.anio, r]));
    const caja = $("#cKpis"), salida = $("#cAnioOut");
    rango.min = 2000; rango.max = C.anual[C.anual.length - 1].anio; rango.value = rango.max;
    const kpi = (titulo, valor, nota) => {
      const d = document.createElement("div"); d.className = "dk";
      const s = document.createElement("span"); s.className = "dk-t"; s.textContent = titulo;
      const b = document.createElement("b"); b.textContent = valor;
      const n = document.createElement("span"); n.className = "dk-d"; n.textContent = nota;
      d.append(s, b, n); return d;
    };
    const pintar = () => {
      const a = +rango.value, r = porAnio[a], rs = resA[a];
      salida.textContent = a;
      caja.replaceChildren(
        kpi(tr("Temperatura frente a la normal", "Temperature vs normal"), grados(r.palma, 2), tr("Planeta: ", "Planet: ") + grados(r.global, 2)),
        kpi(tr("Noches tropicales", "Tropical nights"), fmt(r.tropicales), tr(`normal 1991-2020: ${C.tropicales.normal_1991_2020}`, `1991-2020 normal: ${C.tropicales.normal_1991_2020}`)),
        kpi(tr("Pernoctaciones hoteleras", "Hotel nights"), pern[a] ? fmt(pern[a] / 1e6, 1) + tr(" M", "M") : "-", pern[a] ? tr("isla de Mallorca, INE", "island of Mallorca, INE") : tr("año incompleto", "incomplete year")),
        kpi(tr("Pernoctaciones en noche tropical", "Hotel nights on a tropical night"), expo[a] != null ? pc(expo[a], 1) : "-", tr("del total del año", "of the year's total")),
        kpi(tr("Reservas de agua, mínimo", "Water reserves, low point"), rs ? pc(rs.minimo, 1) : "-", rs ? tr(`caída de verano: ${fmt(rs.caida_verano, 1)} pt`, `summer drop: ${fmt(rs.caida_verano, 1)} pts`) : tr("serie desde 2017", "series from 2017")));
    };
    rango.addEventListener("input", pintar);
    pintar();
  }
})();

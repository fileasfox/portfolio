/* Código interactivo del proyecto Mallorca:
   1) Consola SQL: SQLite (sql.js, compilado a JavaScript) corre dentro del navegador con los anuncios reales.
   2) Simulador de precio: aplica los coeficientes reales de la regresión. */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const fmt = (n, d = 0) => n == null ? "-" : Number(n).toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  const PF = window.PF || {};
  const hl = window.PFhl || (s => esc(s));

  /* ================= 1. Consola SQL ================= */
  const box = $("#sqlConsole");
  if (box && PF.sql) {
    const SQLJS = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-asm.js";
    // Subresource Integrity: si el CDN sirviera un fichero alterado, el navegador no lo ejecuta
    const SQLJS_SRI = "sha384-ur9WCykw0SZNZ8drFEOH/m9+bB+wzKinbF63kpF2yRb4AYvAFbrGvvEC/RfCK8Wp";
    const ta = $("#sqlInput"), code = $("#sqlHl"), pre = code.parentElement, out = $("#sqlOut"), st = $("#sqlStatus"), run = $("#runSql"), pres = $("#presets");
    const q = id => PF.sql.consultas.find(c => c.fichero.startsWith(id)).sql;
    const PRESETS = [
      ["Vista al mar: comparación bruta", "-- Comparación sin controles: ¿cuánto más cobra un anuncio con vista al mar?\n-- (el modelo de la sección 05 corrige esta cifra por tamaño, zona, tipo y temporada)\nSELECT\n    vista_mar,\n    COUNT(*)              AS anuncios,\n    ROUND(AVG(precio))    AS precio_medio,\n    ROUND(AVG(bedrooms), 1) AS dormitorios_medios\nFROM listings_limpio\nWHERE room_type = 'Entire home/apt'\n  AND precio BETWEEN 71 AND 3870\nGROUP BY vista_mar;"],
      ["Perfil de calidad", q("02")],
      ["¿Faltan precios al azar?", q("03")],
      ["Mediana por municipio", q("04")],
      ["Deciles de ingreso", q("05")],
      ["Anfitriones", q("06")],
      ["Crecimiento anual", "-- Reseñas agregadas por año y variación con LAG()\nWITH anual AS (\n    SELECT anio, SUM(resenas) AS resenas\n    FROM reviews_mes\n    WHERE anio BETWEEN 2019 AND 2025\n    GROUP BY anio\n)\nSELECT\n    anio,\n    resenas,\n    ROUND(100.0 * (1.0 * resenas / LAG(resenas) OVER (ORDER BY anio) - 1), 1) AS crecimiento_pct\nFROM anual\nORDER BY anio;"],
      ["Esquema de tablas", "-- Tablas disponibles en esta base de datos\nSELECT name AS tabla, sql AS definicion\nFROM sqlite_master\nWHERE type = 'table';"],
    ];
    let db = null, loading = null;

    const paint = () => { code.innerHTML = hl(ta.value, "sql") + "\n"; pre.scrollTop = ta.scrollTop; pre.scrollLeft = ta.scrollLeft; };
    ta.addEventListener("input", paint);
    ta.addEventListener("scroll", () => { pre.scrollTop = ta.scrollTop; pre.scrollLeft = ta.scrollLeft; });
    ta.addEventListener("keydown", e => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); exec(); }
      if (e.key === "Tab" && !e.shiftKey) { e.preventDefault(); const a = ta.selectionStart; ta.setRangeText("  ", a, ta.selectionEnd, "end"); paint(); }
    });

    PRESETS.forEach(([name, sql], i) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = name; b.setAttribute("aria-pressed", i === 0);
      b.addEventListener("click", () => { [...pres.children].forEach(c => c.setAttribute("aria-pressed", c === b)); load(sql, true, false); });
      pres.append(b);
    });

    function load(sql, runIt, scroll = true) {
      ta.value = sql; paint();
      if (scroll) box.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      if (runIt) exec();
    }
    window.PFconsole = { load };

    const loadScript = (src, sri) => new Promise((ok, ko) => {
      const s = document.createElement("script"); s.src = src; s.onload = ok;
      if (sri) { s.integrity = sri; s.crossOrigin = "anonymous"; }
      s.onerror = () => ko(new Error("No se pudo cargar " + src + ". Comprueba la conexión y vuelve a intentarlo."));
      document.head.append(s);
    });

    function ensureDb() {
      if (db) return Promise.resolve(db);
      if (loading) return loading;
      loading = (async () => {
        const t0 = performance.now();
        st.className = "status"; st.innerHTML = '<span class="spinner"></span>Cargando SQLite en tu navegador…';
        await loadScript(SQLJS, SQLJS_SRI);
        const SQL = await window.initSqlJs();
        st.innerHTML = '<span class="spinner"></span>Cargando 14.817 anuncios…';
        if (!window.PG) await loadScript("assets/playground.js");
        const d = new SQL.Database();
        for (const [name, t] of Object.entries(window.PG)) {
          const types = t.columnas.map((_, j) => {
            const v = t.filas.find(r => r[j] != null);
            return v == null ? "TEXT" : typeof v[j] === "number" ? (t.filas.every(r => r[j] == null || Number.isInteger(r[j])) ? "INTEGER" : "REAL") : "TEXT";
          });
          d.run(`CREATE TABLE ${name} (${t.columnas.map((c, j) => c + " " + types[j]).join(", ")})`);
          const ins = d.prepare(`INSERT INTO ${name} VALUES (${t.columnas.map(() => "?").join(",")})`);
          d.run("BEGIN");
          t.filas.forEach(r => ins.run(r));
          d.run("COMMIT"); ins.free();
        }
        db = d;
        st.textContent = `Base lista en ${fmt((performance.now() - t0) / 1000, 1)} s · tablas: ${Object.keys(window.PG).join(", ")}`;
        return db;
      })().catch(e => { loading = null; throw e; });
      return loading;
    }

    function table(r) {
      const rows = r.values.slice(0, 200);
      const num = r.columns.map((_, j) => rows.some(x => typeof x[j] === "number"));
      return `<table><thead><tr>${r.columns.map((c, j) => `<th${num[j] ? ' class="r"' : ""}>${esc(c)}</th>`).join("")}</tr></thead><tbody>` +
        rows.map(x => `<tr>${x.map((v, j) => num[j] && typeof v === "number"
          ? `<td class="r">${fmt(v, Number.isInteger(v) ? 0 : 2)}</td>`
          : `<td class="${String(v).length > 60 ? "wrap" : ""}">${v == null ? "NULL" : esc(v)}</td>`).join("")}</tr>`).join("") +
        `</tbody></table>`;
    }

    async function exec() {
      const sql = ta.value.trim();
      if (!sql) { st.className = "status err"; st.textContent = "Escribe una consulta para ejecutarla."; return; }
      run.disabled = true;
      try {
        const d = await ensureDb();
        const t = performance.now();
        const res = d.exec(sql);
        const ms = performance.now() - t;
        st.className = "status";
        if (!res.length) { out.innerHTML = ""; st.textContent = `Ejecutada en ${fmt(ms, 1)} ms · sin filas de resultado`; }
        else {
          const r = res[res.length - 1];
          out.innerHTML = table(r);
          st.textContent = `${fmt(r.values.length)} filas en ${fmt(ms, 1)} ms` + (r.values.length > 200 ? " · mostrando 200" : "");
        }
      } catch (e) {
        st.className = "status err"; st.textContent = "Error";
        out.innerHTML = `<div class="errbox">${esc(e.message)}\n\nPista: las tablas son listings_limpio y reviews_mes. Usa «Esquema de tablas» para ver sus columnas, o «Restaurar datos» si has borrado algo.</div>`;
      } finally { run.disabled = false; }
    }
    run.addEventListener("click", exec);
    // La base vive en la memoria del visitante: un DROP o un DELETE solo afecta a su copia. Esto la recrea.
    $("#resetDb").addEventListener("click", () => {
      if (db) db.close();
      db = null; loading = null; out.innerHTML = "";
      st.className = "status"; st.textContent = "Datos restaurados: la próxima ejecución vuelve a cargar los 14.817 anuncios.";
    });
    load(PRESETS[0][1], false, false);
  }

  /* ================= 2. Simulador de precio ================= */
  const sim = $("#sim");
  const S = PF.res && PF.res.simulador;
  if (sim && S) {
    const mun = $("#simMun"), tipo = $("#simTipo"), mes = $("#simMes"), attrsBox = $("#simAttrs");
    const MESES = { "2026-06": "Junio 2026", "2026-07": "Julio 2026", "2026-08": "Agosto 2026", "2026-09": "Septiembre 2026", "2026-10": "Octubre 2026" };
    const sig = Object.fromEntries(PF.res.hedonico.atributos.map(a => [a.atributo, a.ic95[0] > 0 || a.ic95[1] < 0]));
    Object.entries(S.municipio_n).filter(([, n]) => n >= 40).sort((a, b) => b[1] - a[1])
      .forEach(([m, n]) => mun.add(new Option(`${m} (${fmt(n)})`, m, false, m === "Palma de Mallorca")));
    Object.keys(S.tipo).forEach(t => tipo.add(new Option(t, t, false, t === "Apartamento")));
    Object.entries(MESES).forEach(([k, v]) => mes.add(new Option(v, k, false, k === "2026-07")));
    const ranges = { accommodates: "#simCap", bedrooms: "#simDor", bathrooms: "#simBan" };
    Object.entries(ranges).forEach(([k, sel]) => {
      const r = $(sel), [lo, hi, med] = S.num_rango[k];
      r.min = lo; r.max = hi; r.value = med; r.step = 1;
    });
    Object.keys(S.atributos).forEach(a => {
      const l = document.createElement("label"); l.className = "switch";
      l.innerHTML = `<input type="checkbox" value="${esc(a)}"${a === "Vista al mar" ? " checked" : ""}><span>${esc(a)}${sig[a] ? "" : " (n.s.)"}</span>`;
      attrsBox.append(l);
    });

    const price = $("#simPrice"), brk = $("#simBreak");
    function xb(on) {
      let v = S.const + (S.municipio[mun.value] || 0) + (S.tipo[tipo.value] || 0) + (S.mes[mes.value] || 0);
      Object.entries(ranges).forEach(([k, sel]) => (v += S.num[k] * Number($(sel).value)));
      on.forEach(a => (v += S.atributos[a]));
      return v;
    }
    const eur = v => Math.exp(v) * S.smearing;
    let last = 0;
    function update() {
      Object.values(ranges).forEach(sel => ($(sel + "Out").textContent = $(sel).value));
      const on = [...attrsBox.querySelectorAll("input:checked")].map(i => i.value);
      const total = eur(xb(on)), base = eur(xb([]));
      price.innerHTML = `${fmt(total)} €<small>/ noche</small>`;
      if (Math.round(total) !== Math.round(last)) { price.classList.add("bump"); setTimeout(() => price.classList.remove("bump"), 180); }
      last = total;
      brk.innerHTML = `<li><span>Sin atributos</span><b>${fmt(base)} €</b></li>` +
        on.map(a => { const d = total - eur(xb(on.filter(x => x !== a))); return `<li><span>${esc(a)}${sig[a] ? "" : " (n.s.)"}</span><b>${d >= 0 ? "+" : "−"}${fmt(Math.abs(d))} €</b></li>`; }).join("");
    }
    sim.addEventListener("input", update);
    sim.addEventListener("change", update);
    update();
  }
})();

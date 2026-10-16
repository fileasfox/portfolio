-- Tabla de hechos mensual: una fila por mes con turismo, clima, reservas y contexto global.
-- Es la tabla que se conectaría a Looker Studio, Power BI o Tableau.
DROP TABLE IF EXISTS mart_mes;
CREATE TABLE mart_mes AS
WITH normal AS (            -- normal climática 1991-2020 de cada mes del año (referencia de la OMM)
    SELECT mes, AVG(tmedia) AS tmedia_normal, AVG(noches_tropicales) AS tropicales_normal
    FROM int_clima_mensual
    WHERE anio BETWEEN 1991 AND 2020
    GROUP BY mes
),
base AS (
    SELECT
        c.periodo, c.anio, c.mes, c.dias,
        c.tmedia, c.tmax_media, c.tmin_media, c.tmax_absoluta,
        c.noches_tropicales, c.dias_calor, c.dias_calor_extremo,
        c.precipitacion_mm,
        ROUND(c.tmedia - n.tmedia_normal, 2)                             AS anomalia_palma,
        g.anomalia_global,
        t.pernoct_espana + t.pernoct_extranjero                          AS pernoctaciones,
        t.pernoct_extranjero,
        t.viajeros_espana + t.viajeros_extranjero                        AS viajeros,
        t.plazas, t.ocupacion_pct, t.personal, t.provisional,
        r.reservas_pct, r.anio_hidrologico
    FROM int_clima_mensual c
    JOIN normal n USING (mes)
    LEFT JOIN stg_global   g ON g.periodo = c.periodo
    LEFT JOIN stg_turismo  t ON t.periodo = c.periodo
    LEFT JOIN stg_reservas r ON r.periodo = c.periodo
    -- Meses con al menos el 90 % de los días observados (hay huecos puntuales en la estación)
    WHERE c.dias >= 0.9 * CAST(strftime('%d', date(c.periodo || '-01', '+1 month', '-1 day')) AS INTEGER)
)
SELECT
    *,
    -- Exposición: pernoctaciones que caen en noche tropical, suponiendo un reparto uniforme dentro del mes
    ROUND(pernoctaciones * noches_tropicales * 1.0 / dias)               AS pernoct_noche_tropical,
    ROUND(100.0 * pernoct_extranjero / NULLIF(pernoctaciones, 0), 1)     AS pct_extranjero,
    -- Variación interanual: el mismo mes del año anterior es la comparación justa en turismo
    ROUND(100.0 * (pernoctaciones * 1.0 / NULLIF(LAG(pernoctaciones, 12) OVER w, 0) - 1), 1) AS pernoct_var_interanual_pct,
    SUM(pernoctaciones) OVER (w ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)                  AS pernoct_12m,
    ROUND(reservas_pct - LAG(reservas_pct, 1) OVER w, 2)                                    AS reservas_cambio_mes
FROM base
WINDOW w AS (ORDER BY anio, mes);

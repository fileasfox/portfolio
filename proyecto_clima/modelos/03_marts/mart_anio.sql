-- Una fila por año completo. Las anomalías de Palma y del planeta se expresan frente a la
-- misma base, la normal climática vigente de la OMM (1991-2020), para poder compararlas.
DROP TABLE IF EXISTS mart_anio;
CREATE TABLE mart_anio AS
WITH anual AS (
    SELECT
        anio,
        COUNT(*)                                            AS meses,
        ROUND(AVG(tmedia), 2)                               AS tmedia,
        ROUND(AVG(CASE WHEN mes IN (6, 7, 8) THEN tmedia END), 2) AS tmedia_verano,
        SUM(noches_tropicales)                              AS noches_tropicales,
        SUM(dias_calor)                                     AS dias_calor,
        SUM(dias_calor_extremo)                             AS dias_calor_extremo,
        ROUND(SUM(precipitacion_mm), 0)                     AS precipitacion_mm,
        ROUND(AVG(anomalia_global), 3)                      AS anomalia_global_1951,
        SUM(pernoctaciones)                                 AS pernoctaciones,
        SUM(pernoct_noche_tropical)                         AS pernoct_noche_tropical,
        SUM(CASE WHEN mes BETWEEN 6 AND 9 THEN pernoctaciones END) AS pernoct_jun_sep,
        COUNT(pernoctaciones)                               AS meses_turismo
    FROM mart_mes
    GROUP BY anio
),
base AS (
    SELECT AVG(tmedia) AS t_palma, AVG(anomalia_global_1951) AS t_global
    FROM anual WHERE anio BETWEEN 1991 AND 2020
)
SELECT
    a.anio, a.tmedia, a.tmedia_verano,
    ROUND(a.tmedia - b.t_palma, 2)                                   AS anomalia_palma,
    ROUND(a.anomalia_global_1951 - b.t_global, 2)                    AS anomalia_global,
    a.noches_tropicales, a.dias_calor, a.dias_calor_extremo, a.precipitacion_mm,
    CASE WHEN a.meses_turismo = 12 THEN a.pernoctaciones END         AS pernoctaciones,
    CASE WHEN a.meses_turismo = 12 THEN ROUND(100.0 * a.pernoct_jun_sep / a.pernoctaciones, 1) END        AS pct_jun_sep,
    CASE WHEN a.meses_turismo = 12 THEN ROUND(100.0 * a.pernoct_noche_tropical / a.pernoctaciones, 1) END AS pct_noche_tropical
FROM anual a CROSS JOIN base b
WHERE a.meses = 12;

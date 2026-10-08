-- 07 · Crecimiento interanual de la actividad (reseñas como indicador de estancias)
WITH anual AS (
    SELECT CAST(strftime('%Y', date) AS INTEGER) AS anio,
           COUNT(*)                              AS resenas
    FROM reviews
    WHERE date >= '2022-01-01' AND date < '2026-01-01'
    GROUP BY anio
)
SELECT
    anio,
    resenas,
    LAG(resenas) OVER (ORDER BY anio)                                         AS anio_anterior,
    ROUND(100.0 * (1.0 * resenas / LAG(resenas) OVER (ORDER BY anio) - 1), 1) AS crecimiento_pct
FROM anual
ORDER BY anio;

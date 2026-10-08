-- 05 · Concentración del ingreso: ¿qué parte factura cada decil de anuncios?
WITH r AS (
    SELECT ingreso_12m,
           NTILE(10) OVER (ORDER BY ingreso_12m DESC) AS decil
    FROM listings_limpio
    WHERE ingreso_12m > 0
)
SELECT
    decil,
    COUNT(*)                                                       AS anuncios,
    ROUND(SUM(ingreso_12m))                                        AS ingreso_total,
    ROUND(100.0 * SUM(ingreso_12m) / SUM(SUM(ingreso_12m)) OVER (), 1) AS pct_ingreso,
    ROUND(SUM(SUM(ingreso_12m)) OVER (ORDER BY decil) * 100.0
          / SUM(SUM(ingreso_12m)) OVER (), 1)                      AS pct_acumulado
FROM r
GROUP BY decil
ORDER BY decil;

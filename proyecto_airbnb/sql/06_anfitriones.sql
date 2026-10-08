-- 06 · Profesionalización: anuncios según el tamaño de la cartera de su anfitrión
SELECT
    CASE
        WHEN anuncios_anfitrion = 1  THEN '1'
        WHEN anuncios_anfitrion <= 4 THEN '2-4'
        WHEN anuncios_anfitrion <= 19 THEN '5-19'
        ELSE '20+'
    END                                                   AS cartera,
    COUNT(*)                                              AS anuncios,
    COUNT(DISTINCT host_id)                               AS anfitriones,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)    AS pct_anuncios
FROM listings_limpio
GROUP BY cartera
ORDER BY MIN(anuncios_anfitrion);

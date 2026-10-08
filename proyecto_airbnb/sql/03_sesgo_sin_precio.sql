-- 03 · ¿Los precios faltan al azar? Comparo la actividad de los anuncios con y sin precio
SELECT
    CASE WHEN precio IS NULL THEN 'Sin precio' ELSE 'Con precio' END  AS grupo,
    COUNT(*)                                                          AS anuncios,
    ROUND(AVG(number_of_reviews_ltm), 1)                              AS resenas_12m_media,
    ROUND(100.0 * SUM(number_of_reviews_ltm = 0) / COUNT(*), 1)       AS pct_sin_actividad_12m
FROM listings_limpio
GROUP BY grupo;

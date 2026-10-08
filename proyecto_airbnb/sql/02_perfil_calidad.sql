-- 02 · Perfil de calidad: volumen, duplicados, vacíos y extremos en una sola pasada
SELECT
    COUNT(*)                                              AS anuncios,
    COUNT(*) - COUNT(DISTINCT id)                         AS ids_duplicados,
    SUM(precio IS NULL)                                   AS sin_precio,
    ROUND(100.0 * SUM(precio IS NULL) / COUNT(*), 1)      AS pct_sin_precio,
    SUM(number_of_reviews = 0)                            AS sin_resenas,
    MIN(precio)                                           AS precio_min,
    MAX(precio)                                           AS precio_max
FROM listings_limpio;

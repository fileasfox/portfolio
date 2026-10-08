-- 04 · Precio mediano por municipio
-- SQLite no tiene MEDIAN(): se calcula con ROW_NUMBER() y COUNT() como funciones de ventana.
WITH ordenado AS (
    SELECT
        municipio,
        precio,
        ROW_NUMBER() OVER (PARTITION BY municipio ORDER BY precio) AS rn,
        COUNT(*)     OVER (PARTITION BY municipio)                 AS n
    FROM listings_limpio
    WHERE precio IS NOT NULL
)
SELECT
    municipio,
    MAX(n)               AS anuncios_con_precio,
    ROUND(AVG(precio), 2) AS precio_mediano   -- sin redondear a entero: ver cuadre
FROM ordenado
WHERE rn IN ((n + 1) / 2, (n + 2) / 2)      -- 1 fila si n es impar, 2 si es par
GROUP BY municipio
ORDER BY anuncios_con_precio DESC;

-- 08 · Calendario (≈5,4 M de filas): % de noches no disponibles por mes, próximos 12 meses
-- "No disponible" mezcla reservas y bloqueos del propietario: es un techo, no la ocupación.
SELECT
    strftime('%Y-%m', date)                                   AS mes,
    COUNT(DISTINCT listing_id)                                AS anuncios,
    COUNT(*)                                                  AS noches,
    ROUND(100.0 * SUM(available = 'f') / COUNT(*), 1)         AS pct_no_disponible
FROM calendar
WHERE date >= '2026-07-01' AND date < '2027-07-01'
GROUP BY mes
ORDER BY mes;

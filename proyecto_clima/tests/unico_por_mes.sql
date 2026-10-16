-- mart_mes debe tener exactamente una fila por mes
SELECT periodo, COUNT(*) AS filas FROM mart_mes GROUP BY periodo HAVING COUNT(*) > 1;

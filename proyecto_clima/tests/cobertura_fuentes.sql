-- Todas las fuentes cruzan con el calendario: ningún mes de turismo, reservas o temperatura
-- global (desde 1975, primer año completo de la estación) se queda fuera del mart por no tener clima
SELECT 'turismo' AS fuente, periodo FROM stg_turismo WHERE periodo NOT IN (SELECT periodo FROM mart_mes) AND periodo < '2026-09'
UNION ALL
SELECT 'reservas', periodo FROM stg_reservas WHERE periodo NOT IN (SELECT periodo FROM mart_mes)
UNION ALL
SELECT 'global', periodo FROM stg_global WHERE anio >= 1975 AND periodo NOT IN (SELECT periodo FROM mart_mes) AND periodo < '2026-09';

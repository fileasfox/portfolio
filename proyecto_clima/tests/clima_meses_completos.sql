-- Los meses del mart tienen al menos el 90 % de sus días con máxima y mínima válidas
SELECT periodo, dias,
       CAST(strftime('%d', date(periodo || '-01', '+1 month', '-1 day')) AS INTEGER) AS dias_del_mes
FROM mart_mes
WHERE dias < 0.9 * CAST(strftime('%d', date(periodo || '-01', '+1 month', '-1 day')) AS INTEGER)
   OR dias > CAST(strftime('%d', date(periodo || '-01', '+1 month', '-1 day')) AS INTEGER);

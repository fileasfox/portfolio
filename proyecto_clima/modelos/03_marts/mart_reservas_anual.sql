-- Ciclo anual de las reservas por año hidrológico (octubre a septiembre):
-- máximo de invierno, mínimo de final de verano, caída del verano y lluvia del año.
DROP TABLE IF EXISTS mart_reservas_anual;
CREATE TABLE mart_reservas_anual AS
WITH ciclo AS (
    SELECT
        anio_hidrologico,
        COUNT(reservas_pct)                                          AS meses,
        MAX(reservas_pct)                                            AS maximo,
        MIN(reservas_pct)                                            AS minimo,
        -- Caída del verano: de mayo a septiembre del mismo año hidrológico
        MAX(CASE WHEN mes = 5 THEN reservas_pct END) - MAX(CASE WHEN mes = 9 THEN reservas_pct END) AS caida_verano,
        SUM(precipitacion_mm)                                        AS lluvia_mm,
        SUM(CASE WHEN mes BETWEEN 5 AND 9 THEN pernoctaciones END)   AS pernoct_may_sep
    FROM mart_mes
    WHERE anio_hidrologico IS NOT NULL
    GROUP BY anio_hidrologico
)
SELECT
    c.*,
    -- Mes en que se toca fondo (el primero si hay empate)
    (SELECT m.periodo FROM mart_mes m
      WHERE m.anio_hidrologico = c.anio_hidrologico AND m.reservas_pct = c.minimo
      ORDER BY m.periodo LIMIT 1)                                    AS mes_minimo
FROM ciclo c
WHERE c.meses = 12;                                                  -- solo años hidrológicos completos

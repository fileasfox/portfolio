-- Reservas hídricas ponderadas de Mallorca (% de su capacidad), Govern de les Illes Balears
DROP VIEW IF EXISTS stg_reservas;
CREATE VIEW stg_reservas AS
SELECT
    anio,
    mes,
    printf('%04d-%02d', anio, mes)                           AS periodo,
    reservas_pct,
    -- Año hidrológico: de octubre a septiembre (el de 2025 va de oct-2024 a sep-2025)
    CASE WHEN mes >= 10 THEN anio + 1 ELSE anio END          AS anio_hidrologico
FROM raw_reservas;

-- Turismo hotelero en la isla de Mallorca, un mes por fila (INE, EOH, zona turística)
-- De formato largo (una serie por fila) a formato ancho (una métrica por columna).
DROP VIEW IF EXISTS stg_turismo;
CREATE VIEW stg_turismo AS
SELECT
    anio,
    mes,
    printf('%04d-%02d', anio, mes)                                                AS periodo,
    MAX(CASE WHEN variable = 'viajeros_res_espana'           THEN valor END)      AS viajeros_espana,
    MAX(CASE WHEN variable = 'viajeros_res_extranjero'       THEN valor END)      AS viajeros_extranjero,
    MAX(CASE WHEN variable = 'pernoctaciones_res_espana'     THEN valor END)      AS pernoct_espana,
    MAX(CASE WHEN variable = 'pernoctaciones_res_extranjero' THEN valor END)      AS pernoct_extranjero,
    MAX(CASE WHEN variable = 'plazas'                        THEN valor END)      AS plazas,
    MAX(CASE WHEN variable = 'ocupacion_plazas_pct'          THEN valor END)      AS ocupacion_pct,
    MAX(CASE WHEN variable = 'personal_empleado'             THEN valor END)      AS personal,
    MAX(estado = 'provisional')                                                   AS provisional
FROM raw_ine
GROUP BY anio, mes;

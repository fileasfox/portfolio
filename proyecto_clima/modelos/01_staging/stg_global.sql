-- Anomalía de temperatura global (NASA GISTEMP v4, tierra y océano, base 1951-1980)
DROP VIEW IF EXISTS stg_global;
CREATE VIEW stg_global AS
SELECT anio, mes, printf('%04d-%02d', anio, mes) AS periodo, anomalia AS anomalia_global
FROM raw_gistemp;

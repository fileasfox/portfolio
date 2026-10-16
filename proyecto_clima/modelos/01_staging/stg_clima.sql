-- Clima diario en Palma (NOAA GHCN-Daily, estación Palma de Mallorca CMT, OMM 08306)
-- La media diaria se calcula como (máxima + mínima) / 2, igual que AEMET en sus valores normales.
DROP VIEW IF EXISTS stg_clima;
CREATE VIEW stg_clima AS
SELECT
    date(fecha)                          AS fecha,
    CAST(substr(fecha, 1, 4) AS INTEGER) AS anio,
    CAST(substr(fecha, 6, 2) AS INTEGER) AS mes,
    tmax,
    tmin,
    (tmax + tmin) / 2.0                  AS tmedia,
    precipitacion
FROM raw_clima
WHERE tmax IS NOT NULL AND tmin IS NOT NULL;   -- días sin las dos temperaturas válidas no cuentan

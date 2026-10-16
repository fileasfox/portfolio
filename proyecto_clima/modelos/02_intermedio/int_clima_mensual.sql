-- Del día al mes: medias, extremos y conteos de días con umbrales de calor estándar
--   noche tropical: mínima >= 20 °C (definición de AEMET)
--   día de calor:   máxima >= 30 °C;  día de calor extremo: máxima >= 35 °C
DROP TABLE IF EXISTS int_clima_mensual;
CREATE TABLE int_clima_mensual AS
SELECT
    anio,
    mes,
    printf('%04d-%02d', anio, mes)             AS periodo,
    COUNT(*)                                   AS dias,
    ROUND(AVG(tmedia), 2)                      AS tmedia,
    ROUND(AVG(tmax), 2)                        AS tmax_media,
    ROUND(AVG(tmin), 2)                        AS tmin_media,
    ROUND(MAX(tmax), 1)                        AS tmax_absoluta,
    SUM(tmin >= 20)                            AS noches_tropicales,
    SUM(tmax >= 30)                            AS dias_calor,
    SUM(tmax >= 35)                            AS dias_calor_extremo,
    ROUND(SUM(precipitacion), 1)               AS precipitacion_mm
FROM stg_clima
GROUP BY anio, mes;

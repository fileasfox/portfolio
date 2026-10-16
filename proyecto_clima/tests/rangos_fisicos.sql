-- Valores físicamente posibles: temperaturas razonables para Mallorca, máxima >= mínima,
-- porcentajes entre 0 y 100 y conteos no negativos
SELECT 'clima' AS tabla, fecha AS clave FROM stg_clima
 WHERE tmax < tmin OR tmax > 46 OR tmin < -10 OR precipitacion < 0
UNION ALL
SELECT 'reservas', periodo FROM stg_reservas WHERE reservas_pct NOT BETWEEN 0 AND 100
UNION ALL
SELECT 'turismo', periodo FROM stg_turismo
 WHERE ocupacion_pct NOT BETWEEN 0 AND 100 OR pernoct_espana < 0 OR pernoct_extranjero < 0;

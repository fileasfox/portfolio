-- 01 · Vista limpia sobre la tabla cruda de anuncios
-- El precio llega como texto ("$1,035.00"): se limpia en SQL y los vacíos pasan a NULL.
DROP VIEW IF EXISTS listings_limpio;
CREATE VIEW listings_limpio AS
SELECT
    id,
    host_id,
    neighbourhood_cleansed                                   AS municipio,
    room_type,
    property_type,
    accommodates,
    bedrooms,
    bathrooms,
    CAST(NULLIF(REPLACE(REPLACE(price, '$', ''), ',', ''), '') AS REAL) AS precio,
    number_of_reviews,
    number_of_reviews_ltm,
    estimated_revenue_l365d                                  AS ingreso_12m,
    estimated_occupancy_l365d                                AS noches_12m,
    calculated_host_listings_count                           AS anuncios_anfitrion
FROM listings;

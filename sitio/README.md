# Matteo Eiras · Portafolio de Data Analyst

Web: https://fileasfox.github.io/portfolio

## Proyecto principal · ¿Cuánto vale una vista al mar en Mallorca?

Estudio del alquiler vacacional de Mallorca con los 14.817 anuncios de Inside Airbnb (extracción del 23/06/2026, CC BY 4.0).

| Pregunta | Resultado |
|---|---|
| ¿Qué atributos justifican un precio mayor? | Vista al mar +27 %, piscina +19 %, aire acondicionado +12 % (regresión hedónica con controles de tamaño, municipio, tipo y temporada) |
| ¿Cuánto engaña la comparación bruta? | La piscina parece valer +73 % sin controles y +19 % con ellos |
| ¿Cómo es la oferta? | 94,8 % viviendas enteras; 54 % de los anuncios en manos de anfitriones con 20 o más |
| ¿Cuánto pesa el verano? | De mayo a septiembre se concentra el 65 % de la actividad; +25,7 % en 2024 y +16,4 % en 2025 |

### Reproducir

```bash
python proyecto_airbnb/analisis_mallorca.py proyecto_airbnb/datos proyecto_airbnb   # pandas + modelo
python proyecto_airbnb/ejecutar_sql.py proyecto_airbnb/datos proyecto_airbnb        # SQLite: 8 consultas + cuadres con pandas
python sitio_src/build.py                                                          # genera las 9 páginas en sitio/
python sitio_src/auditoria.py sitio                                                # 19 controles: si falla uno, no se publica
python sitio_src/build.py                                                          # incluye el resultado de la auditoría en la web
```

Los datos se descargan de https://insideairbnb.com/get-the-data/ (Mallorca): `listings.csv.gz`, `calendar.csv.gz`, `reviews.csv` y `neighbourhoods.geojson`. No se versionan en el repositorio.

## Casos profesionales (anonimizados)

Salud de cuenta y churn por ROI · Cuadre de un dashboard que contaba el doble · Alertas del funnel de invitaciones e integraciones · Limpieza reproducible de datos de facturación.

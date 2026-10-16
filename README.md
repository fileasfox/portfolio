# Portafolio · Matteo Eiras Pé

Portafolio de data analyst en hospitality tech. Web estática, generada con Python y sin frameworks.

**Web:** https://fileasfox.github.io/portfolio

- **Proyecto principal:** ¿cuánto vale una vista al mar en Mallorca? Datos reales de Inside Airbnb (CC BY 4.0), análisis con pandas, 8 consultas SQL cuadradas contra pandas, regresión hedónica, consola SQL que se ejecuta en el navegador (sql.js) y simulador de precio.
- **Casos profesionales anonimizados:** churn por ROI, cuadre de métricas, alertas de integraciones y limpieza de datos de facturación.

## Estructura

| Carpeta | Contenido |
|---|---|
| `proyecto_clima/` | Turismo, calor y agua: ingesta de INE, NOAA, NASA y el Govern balear (`ingesta.py`), SQL por capas con tests (`modelos/`, `tests/`, `modelos.py`) y análisis estadístico (`analisis.py`) |
| `proyecto_mercado/` | Recuento de skills en ofertas reales de data analyst (`mercado.py`) |
| `proyecto_airbnb/` | Análisis en Python (`analisis_mallorca.py`), consultas SQL (`sql/`), cuadre SQL frente a pandas (`ejecutar_sql.py`) y datos del dashboard (`dashboard.py`) |
| `sitio_src/` | Páginas en español (`pages/`) y en inglés (`pages_en/`), estilos, scripts, generador (`build.py`) y auditoría (`auditoria.py`) |
| `sitio/` | Web generada, la que se publica en GitHub Pages (inglés en `sitio/en/`) |

## Reproducir

```bash
# 1. Datos: descargar de https://insideairbnb.com/get-the-data/ (Mallorca) en proyecto_airbnb/datos/
#    listings.csv.gz, calendar.csv.gz, reviews.csv y neighbourhoods.geojson
python proyecto_airbnb/analisis_mallorca.py proyecto_airbnb/datos proyecto_airbnb
python proyecto_airbnb/ejecutar_sql.py proyecto_airbnb/datos proyecto_airbnb
python proyecto_airbnb/dashboard.py proyecto_airbnb/datos proyecto_airbnb

# Turismo, calor y agua (descarga sola las cuatro fuentes oficiales y las cachea en proyecto_clima/datos/)
python proyecto_clima/ingesta.py
python proyecto_clima/modelos.py      # SQL por capas + tests; exporta los marts a CSV
python proyecto_clima/analisis.py

# Mercado: skills que piden las ofertas abiertas (APIs públicas de empleo)
python proyecto_mercado/mercado.py

# 2. Web: generar, auditar (debe dar 23/23) y volver a generar con el resultado de la auditoría
python sitio_src/build.py
python sitio_src/auditoria.py sitio
python sitio_src/build.py
```

Para ver la web en local: `python -m http.server 8765 --directory sitio` y abrir http://localhost:8765.

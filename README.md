# Portafolio · Matteo Eiras Pé

Portafolio de data analyst en hospitality tech. Web estática, generada con Python y sin frameworks.

**Web:** https://fileasfox.github.io/portfolio

- **Proyecto principal:** ¿cuánto vale una vista al mar en Mallorca? Datos reales de Inside Airbnb (CC BY 4.0), análisis con pandas, 8 consultas SQL cuadradas contra pandas, regresión hedónica, consola SQL que se ejecuta en el navegador (sql.js) y simulador de precio.
- **Casos profesionales anonimizados:** churn por ROI, cuadre de métricas, alertas de integraciones y limpieza de datos de facturación.

## Estructura

| Carpeta | Contenido |
|---|---|
| `proyecto_airbnb/` | Análisis en Python (`analisis_mallorca.py`), consultas SQL (`sql/`), cuadre SQL frente a pandas (`ejecutar_sql.py`), datos del dashboard (`dashboard.py`) y cuaderno de pandas (`cuaderno.py`, que genera `cuaderno.ipynb`) |
| `sitio_src/` | Páginas, estilos, scripts, generador (`build.py`) y auditoría (`auditoria.py`) |
| `sitio/` | Web generada, la que se publica en GitHub Pages |

## Reproducir

```bash
# 1. Datos: descargar de https://insideairbnb.com/get-the-data/ (Mallorca) en proyecto_airbnb/datos/
#    listings.csv.gz, calendar.csv.gz, reviews.csv y neighbourhoods.geojson
python proyecto_airbnb/analisis_mallorca.py proyecto_airbnb/datos proyecto_airbnb
python proyecto_airbnb/ejecutar_sql.py proyecto_airbnb/datos proyecto_airbnb
python proyecto_airbnb/dashboard.py proyecto_airbnb/datos proyecto_airbnb
python proyecto_airbnb/cuaderno.py proyecto_airbnb/datos proyecto_airbnb

# 2. Web: generar, auditar (debe dar 23/23) y volver a generar con el resultado de la auditoría
python sitio_src/build.py
python sitio_src/auditoria.py sitio
python sitio_src/build.py
```

Para ver la web en local: `python -m http.server 8765 --directory sitio` y abrir http://localhost:8765.

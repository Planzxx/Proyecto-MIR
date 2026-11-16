# Plazas MIR

Aplicación en Python (Flask) para consultar las plazas MIR adjudicadas y simular tu elección con tu nota.

## Ejecutar

```bash
pip install -r requirements.txt
python app.py              # abre http://127.0.0.1:5000
python app.py --puerto 8080 --no-abrir
```

## Qué hace

- **Plazas**: búsqueda libre (sin tildes, varios términos), filtros por especialidad, comunidad, provincia, centro y rango de nº de orden, ordenación por columnas y «Mostrar más».
- **Resumen**: agrupa por especialidad, centro, comunidad o provincia (plazas, primer y último nº). Pulsa una fila para ver sus plazas.
- **Simulador**: convierte aciertos/errores/netas y expediente en nota total y nº de orden (escalas 2025 y 2026), o usa tu nº de orden. Reproduce la elección con tu lista de preferencias y muestra mejor caso, caso estimado y peor caso, el estado de cada preferencia, qué quedaba en tu turno y qué eligieron los números cercanos. Guarda tus datos en el navegador.

## Estructura

```
app.py              servidor y API (/api/meta, /api/plazas, /api/resumen, /api/opciones, /api/centros, /api/simulador)
mir/data.py         carga del CSV, filtros, ordenación y resumen
mir/scoring.py      nota total y nº de orden estimado
mir/simulator.py    simulación de la elección
mir/texto.py        normalización y mayúsculas legibles
mir/geo.py          provincia y comunidad de cada localidad
mir/pdf_import.py   PDF del listado -> data/plazas.csv
data/plazas.csv     4.710 plazas del PDF
templates/ static/  interfaz web
tests/              pruebas (python -m unittest discover -s tests -t .)
```

## Cambiar los datos

```bash
python -m mir.pdf_import LISTADO.pdf -o data/plazas.csv     # necesita pdfplumber
python app.py --datos otro.csv
```

El CSV tiene las columnas `adj,n,localidad,centro,especialidad`. Toda localidad nueva debe añadirse a `mir/geo.py`.

## Límites

- Los datos son del PDF aportado, generado en mayo de 2022 (no es la convocatoria de 2025) y solo llega al nº 4800.
- El nº de orden se estima por interpolación de las tablas publicadas; por eso hay un margen de error.
- Las especialidades que se siguen eligiendo después del nº 4800 no se marcan como agotadas.

# Sistema RDR para recomendación de nanofármacos

Motor de reglas (RDR/GRDR) para inferir afinidad ligando–nanopartícula y generar recomendaciones accionables. Incluye GUI sencilla (Tkinter) y flujo batch para procesar datasets NCIt.

## Componentes clave
- `implementacion_rdr.py`: motor GRDR + árbol de reglas raíz.
- `reglas_para_rdr.py`: conocimiento de dominio (reglas y excepciones).
- `extract_input.py`: conversión de filas NCIt a estructura RDR (incluye heurísticas y trazabilidad).
- `generate_recommendations.py`: interpreta predicciones y produce reportes legibles (single y batch).
- `app.py`: GUI (Tkinter) con búsqueda NCIt, entrada custom y evaluación completa.

## Requisitos
- Python ≥ 3.9
- Dependencias: `pip install -r requirements.txt`
  - Si usas la GUI en Windows, Tkinter viene incluido con Python oficial.

## Datos esperados
- Dataset principal filtrado: `datasets/dataset_FINAL2.csv`
- Tesauro NCIt para búsquedas GUI: `datasets/Tesauro.xlsx`
- Inputs de ejemplo: `RDR/ins/rdr_inputs_v4.jsonl` (u otros en `RDR/ins/`)

## Ejecución rápida
- GUI: `python RDR/app.py`

## Salidas
- Resultados completos (JSON): `rdr_full_evaluation_results*.json`
- Directamente en la app

## Tests
- Ejecuta `pytest RDR/tests` para validar heurísticas principales.


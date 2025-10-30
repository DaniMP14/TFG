# Copilot Instructions for AI Coding Agents

## Visión General del Proyecto
- El workspace contiene scripts de procesamiento de datos, análisis y manipulación de ontologías OWL, y recursos relacionados con tesauros y datasets biomédicos.
- Los principales flujos de trabajo giran en torno a la manipulación de archivos OWL/RDF, análisis de datasets CSV y automatización de tareas de integración de datos.

## Estructura Clave
- `owl/automatiz_owl.py`: Script principal para automatización y manipulación de ontologías OWL.
- `datasets/`: Contiene datasets CSV y scripts Python para análisis y filtrado de datos biomédicos.
- `tesauro/`: Incluye tesauros en varios formatos (OWL, TXT, OWX) para enriquecer o validar información semántica.
- `Excel_RDR_distribution 0.871/`: Archivos Excel y recursos de apoyo para análisis de reglas de decisión.

## Patrones y Convenciones
- Scripts Python suelen trabajar con rutas relativas a la raíz del workspace.
- Los nombres de archivos y carpetas reflejan el tipo de datos o el propósito del script (ej: `dataset_nano_ONCO.py` procesa `dataset_nano_ONCO.csv`).
- Los scripts de ontologías suelen esperar archivos OWL/RDF en la carpeta `owl/` y pueden generar nuevas versiones con sufijos como `_completed` o `_con_annotations`.

## Flujos de Trabajo Críticos
- **Procesamiento de Ontologías:** Ejecutar `owl/automatiz_owl.py` para automatizar tareas sobre archivos OWL/RDF.
- **Análisis de Datasets:** Usar scripts en `datasets/` para filtrar, analizar o transformar archivos CSV.
- **Integración Tesauro-Ontología:** Los recursos en `tesauro/` pueden ser utilizados por scripts para enriquecer ontologías.

## Dependencias y Entorno
- El entorno principal es Python (recomendado >=3.8).
- Instalar dependencias típicas: `rdflib`, `pandas`, `openpyxl`.
- No hay un gestor de dependencias explícito (como requirements.txt), instalar paquetes manualmente según errores de importación.

## Ejemplo de Ejecución
```bash
# Procesar una ontología OWL
echo Ejecutando automatización OWL...
python owl/automatiz_owl.py

# Analizar un dataset específico
python datasets/dataset_nano_ONCO.py
```

## Notas
- No hay tests automatizados ni scripts de build detectados.
- Los archivos Excel pueden requerir procesamiento manual o scripts adicionales.
- Mantener consistencia en los sufijos de archivos generados para facilitar el versionado y trazabilidad.

---

¿Faltan detalles sobre algún flujo, convención o integración? Indica qué parte del proyecto necesita más explicación para mejorar estas instrucciones.
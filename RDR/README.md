# Sistema RDR para predicción de afinidad en nanomedicinas

Sistema de reglas (Ripple-Down Rules) para inferir afinidad ligando–nanopartícula, orden de monocapa y generar recomendaciones accionables para formulaciones de nanomedicinas.

## Descripción

El sistema utiliza un motor GRDR (Generalized Ripple-Down Rules) que combina:
- **Reglas de conocimiento experto** sobre interacciones nanopartícula-ligando-biomolécula
- **Heurísticas de extracción** desde términos del tesauro NCIt
- **Sistema de recomendaciones** con decisiones go/no-go para producción

## Componentes principales

- `implementacion_rdr.py`: Motor GRDR con evaluación jerárquica de reglas
- `reglas_para_rdr.py`: Base de conocimiento (reglas y excepciones del dominio)
- `extract_input.py`: Conversión de datasets NCIt a estructura de entrada RDR
- `generate_recommendations.py`: Generación de recomendaciones accionables y decisiones de producción
- `app.py`: Interfaz gráfica (Tkinter) para evaluación interactiva

## Instalación

### Requisitos
- Python ≥ 3.9
- Tkinter (incluido en Python oficial de Windows)

### Dependencias

```bash
pip install -r requirements.txt
```

## Uso

### 1. Ejemplo básico (línea de comandos)

```bash
python examples/ejemplo_uso_basico.py
```

Este script muestra cómo:
- Construir un caso de entrada manualmente
- Evaluar con el motor RDR
- Generar recomendaciones

### 2. Interfaz gráfica

```bash
python app.py
```

La GUI permite:
- Buscar fármacos del tesauro NCIt
- Crear casos personalizados
- Generar reportes completos del dataset

### 3. Uso programático

```python
from implementacion_rdr import rule_root
from generate_recommendations import generate_recommendation

# Definir caso de entrada
caso = {
    "nanoparticle": {
        "type": "lipid-based",
        "type_confidence": 1.0,
        "surface_charge": "neutral"
    },
    "ligand": {"type": "peg", "type_confidence": 1.0},
    "biomolecule": {"type": "RNA", "type_confidence": 1.0},
    "surface": {"material": "peg"},
    "context": {
        "display_name": "LNP-mRNA Vaccine",
        "source_code": "C12345"
    }
}

# Evaluar con RDR
prediccion = rule_root.evaluate(caso)

# Generar recomendación
reporte = generate_recommendation(
    prediction=prediccion,
    context=caso["context"],
    full_case=caso
)

print(reporte["decision_produccion"])
```

## Datos

- **Dataset procesado**: `ins/rdr_inputs_v4.jsonl` (ejemplos de casos extraídos del tesauro NCIt)
- **Dataset fuente**: Requiere `../datasets/dataset_FINAL2.csv` y `../datasets/Tesauro.xlsx` para funcionalidad completa

## Estructura del proyecto

```
RDR/
├── implementacion_rdr.py          # Motor GRDR
├── reglas_para_rdr.py             # Base de conocimiento
├── extract_input.py               # Extracción desde NCIt
├── generate_recommendations.py    # Sistema de recomendaciones
├── app.py                         # GUI interactiva
├── requirements.txt               # Dependencias
├── README.md                      # Esta documentación
├── ins/
│   └── rdr_inputs_v4.jsonl       # Dataset procesado (ejemplos)
└── examples/
    └── ejemplo_uso_basico.py     # Script de demostración
```

## Salidas

El sistema genera reportes con:
- **Afinidad predicha** (high/moderate/low)
- **Orden de monocapa** (stable/ordered/semi-ordered/fluid/disordered)
- **Score de viabilidad** (0.0 - 1.0)
- **Confianza de la predicción** (%)
- **Decisión de producción** (APROBADO / VIABLE CON OPTIMIZACIONES / NO APROBADO / REQUIERE VALIDACIÓN)
- **Recomendaciones accionables** y **optimizaciones específicas**

## Notas

- Los campos `*_confidence` en los inputs son **requeridos** para cálculos de confianza (usar 1.0 para datos confiables)
- El sistema combina confianza de entrada × confianza de regla para la predicción final
- Las optimizaciones se adaptan al contexto (RNA/DNA, lipídicas, PEG, metálicas)


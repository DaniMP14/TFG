# examples/ejemplo_uso_basico.py
"""
Ejemplo de uso básico del sistema RDR para predicción de afinidad
y organización de monocapas en nanomedicinas.
"""
import sys
from pathlib import Path

# Añadir el directorio padre al path para poder importar RDR
sys.path.insert(0, str(Path(__file__).parent.parent))

from implementacion_rdr import rule_root
from generate_recommendations import generate_recommendation

# Caso de ejemplo: nanopartícula lipídica con RNA (para probar, se puede modificar)
caso_ejemplo = {
    "nanoparticle": {
        "type": "lipid-based",
        "type_confidence": 1.0,
        "surface_charge": "neutral"
    },
    "ligand": {
        "type": "peg",
        "type_confidence": 1.0
    },
    "biomolecule": {
        "type": "RNA",
        "type_confidence": 1.0
    },
    "surface": {
        "material": "peg"
    },
    "context": {
        "display_name": "LNP-mRNA Vaccine",
        "source_code": "C12345"
    }
}

# Ejecutar predicción
prediccion = rule_root.evaluate(caso_ejemplo)

# Generar recomendación
reporte = generate_recommendation(
    prediction=prediccion,
    context=caso_ejemplo["context"],
    full_case=caso_ejemplo
)

print(f"Regla aplicada: {reporte['regla_aplicada']}")
print(f"Afinidad: {reporte['resultados']['afinidad']}")
print(f"Monocapa: {reporte['resultados']['orden_monocapa']}")
print(f"Score: {reporte['resultados']['score_viabilidad']}")
print(f"Confianza: {reporte['confianza_prediccion']}")
print(f"Decisión: {reporte['decision_produccion']}")
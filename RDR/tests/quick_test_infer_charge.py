"""
Script de prueba rápido para validar infer_charge en RDR/extract_input.py
Ejecuta varios ejemplos en memoria y muestra los resultados.
"""
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path para poder importar RDR
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from RDR.extract_input import infer_charge

examples = [
    {
        "name": "positive_with_peg",
        "display": "PEGylated micelle, positively charged surface",
        "definition": "A PEGylated micelle with cationic surface modifiers",
        "subset": "",
        "expectation": "positive (prefer charged over neutral)"
    },
    {
        "name": "positive_zeta",
        "display": "PEGylated micelle",
        "definition": "Measured zeta potential +35 mV (highly positive)",
        "subset": "",
        "expectation": "positive (parametric zeta boost)"
    },
    {
        "name": "conflict_zeta_text",
        "display": "Cationic coating",
        "definition": "Measured zeta -38 mV (strongly negative)",
        "subset": "",
        "expectation": "ambiguous (conflict positive vs negative)"
    },
    {
        "name": "neutral_only",
        "display": "PEGylated nanoparticle",
        "definition": "Surface shows PEG; expected neutral or uncharged behaviour",
        "subset": "",
        "expectation": "neutral or unknown depending on cues"
    },
]

print("Running quick infer_charge tests:\n")
for ex in examples:
    label, conf, prov = infer_charge(ex['display'], ex['definition'], ex['subset'])
    print(f"CASE: {ex['name']}")
    print(f"  input display: {ex['display']}")
    print(f"  input definition: {ex['definition']}")
    print(f"  result: label={label}, confidence={conf}, provenance={prov}")
    print(f"  expected: {ex['expectation']}\n")

print("Done.")

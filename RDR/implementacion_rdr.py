import pandas as pd
import json
from typing import Callable, Dict, Any, List, Optional
import time
from reglas_para_rdr import attach_rules

class GRDRRule:
    """
    Generalized Ripple-Down Rule (GRDR)
    Permite definir reglas jerárquicas con múltiples dominios de entrada
    y salidas estructuradas (predicciones, propiedades, etc.)
    """

    def __init__(self, 
                 name: str, 
                 condition: Callable[[Dict[str, Any]], bool],
                 action: Callable[[Dict[str, Any]], Dict[str, Any]],
                 domain: str = "general"):
        self.name = name
        self.condition = condition
        self.action = action
        self.domain = domain           # nanoparticle / ligand / biomolecule / surface
        self.exceptions: List["GRDRRule"] = []
        self.execution_time: Optional[float] = None

    def evaluate(self, input_case: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evalúa la regla actual y sus excepciones jerárquicas.
        Combina una medida de confianza de los datos (agregando los campos *_confidence)
        con la confianza explícita de la regla (si la acción devuelve 'rule_confidence').

        Devuelve un dict con claves: rule, output, prediction_confidence, input_confidence,
        provenance, execution_time. Si una excepción produce resultado, se devuelve tal cual.
        """
        start_time = time.time()

        # helper: agregar confidences y provenance desde el input
        def _gather_confidences(inp: Dict[str, Any]):
            confs = []
            provs = []
            for section in ("nanoparticle", "ligand", "biomolecule"):
                sec = inp.get(section, {}) or {}
                for k, v in sec.items():
                    if isinstance(k, str) and k.endswith("_confidence") and isinstance(v, (int, float)):
                        confs.append(float(v))
                    if isinstance(k, str) and k.endswith("_provenance") and v:
                        provs.append(f"{section}.{k}:{v}")
            input_conf = float(sum(confs) / len(confs)) if confs else 0.0
            return input_conf, list(dict.fromkeys(provs))

        if self.condition(input_case):
            # En SCRDR puro, evaluamos excepciones en el orden en que fueron añadidas.
            for ex in self.exceptions:
                result = ex.evaluate(input_case)
                if result is not None:
                    self.execution_time = time.time() - start_time
                    return result

            # acción de la regla base
            action_result = self.action(input_case) or {}

            # extracción de confidencias
            input_conf, provenance = _gather_confidences(input_case)

            # la regla puede declarar su propia confianza devolviendo 'rule_confidence' en la acción
            rule_conf = float(action_result.get("rule_confidence", 1.0)) if isinstance(action_result, dict) else 1.0

            prediction_confidence = input_conf * rule_conf

            self.execution_time = time.time() - start_time

            return {
                "rule": self.name,
                "output": action_result,
                "prediction_confidence": prediction_confidence,
                "input_confidence": input_conf,
                "provenance": provenance,
                "execution_time": self.execution_time,
            }

        return None

    def evaluate_all(self, input_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Devuelve todas las conclusiones aplicables en el subárbol (modo MCRDR-like).

        Recorre el árbol de excepciones y recoge todas las salidas de reglas cuya condición se cumple.
        """
        results: List[Dict[str, Any]] = []

        # si la condición no se cumple, nada en este subárbol aplica
        if not self.condition(input_case):
            return results

        # primero recorrer excepciones y recolectar sus salidas
        for ex in self.exceptions:
            results.extend(ex.evaluate_all(input_case))

        # añadir la salida de la regla base (si proporciona un resultado no vacío)
        action_result = self.action(input_case) or {}
        if action_result:
            # extraer confidences/provenance como en evaluate
            def _gather_confidences_local(inp: Dict[str, Any]):
                confs = []
                provs = []
                for section in ("nanoparticle", "ligand", "biomolecule"):
                    sec = inp.get(section, {}) or {}
                    for k, v in sec.items():
                        if isinstance(k, str) and k.endswith("_confidence") and isinstance(v, (int, float)):
                            confs.append(float(v))
                        if isinstance(k, str) and k.endswith("_provenance") and v:
                            provs.append(f"{section}.{k}:{v}")
                input_conf = float(sum(confs) / len(confs)) if confs else 0.0
                return input_conf, list(dict.fromkeys(provs))

            input_conf, provenance = _gather_confidences_local(input_case)
            rule_conf = float(action_result.get("rule_confidence", 1.0)) if isinstance(action_result, dict) else 1.0
            prediction_confidence = input_conf * rule_conf

            results.append({
                "rule": self.name,
                "output": action_result,
                "prediction_confidence": prediction_confidence,
                "input_confidence": input_conf,
                "provenance": provenance,
                "execution_time": None,
            })

        return results

    def add_exception(self, rule: "GRDRRule"):
        """Agrega una regla de excepción con prioridad opcional."""
        self.exceptions.append(rule)

    def explain(self):
        """Devuelve la jerarquía textual de la regla (para depuración o interfaz visual)."""
        text = f"Rule: {self.name} (domain={self.domain})"
        for ex in self.exceptions:
            text += "\n  ↳ Exception: " + ex.explain().replace("\n", "\n    ")
        return text

# Construir un árbol SCRDR puro: crear una regla raíz y anexar excepciones
rule_root = GRDRRule(name="Root", condition=lambda inp: True, action=lambda inp: {})

# Adjuntar reglas desde el módulo externo (patrón 1):
# attach_rules debe añadir excepciones/nodos al 'rule_root' sin ejecutar evaluación.
attach_rules(rule_root)

if __name__ == "__main__":
    # Caso de prueba ejecutable solo cuando se corre el módulo directamente
    case_C102875 = {
        "nanoparticle": {
            "type": "lipid-based",
            "type_confidence": 0.95,
            "type_provenance": "keywords",
            "surface_charge": "positive",
            "surface_charge_confidence": 0.0,
            "surface_charge_provenance": "none",
        },
        "ligand": {
            "type": "unknown",
            "polarity": "unknown",
            "charge": "negative",
            "type_confidence": 0.0,
            "polarity_confidence": 0.0,
            "charge_confidence": 0.0,
            "type_provenance": "none",
            "polarity_provenance": "none",
            "charge_provenance": "none",
        },
        "biomolecule": {"type": "DNA", "type_confidence": 0.95, "type_provenance": "keywords"},
        "surface": {"material": "unknown", "charge": "unknown"},
        "context": {
            "source_code": "C102875",
            "display_name": "Nanoparticle-encapsulated Doxorubicin Hydrochloride",
            "semantic_type": "Pharmacologic Substance",
        },
    }

    prediction = rule_root.evaluate(case_C102875)
    print(json.dumps(prediction, indent=2, ensure_ascii=False))



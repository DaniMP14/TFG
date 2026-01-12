"""
Generador de recomendaciones accionables desde predicciones RDR.

Convierte las salidas JSON del RDR en recomendaciones legibles y accionables
para su uso en producción: decisiones sobre formulación, estabilidad,
optimización de monocapas y potencial terapéutico.

Uso:
    python RDR/generate_recommendations.py
"""
import json
from typing import Dict, Any, List, Optional


def confidence_adjustment(current_conf: float, input_case: Dict[str, Any]) -> float:
    """
    Ajuste heurístico de confianza basado en coherencia física y biológica.
    No altera la regla RDR, pero refina la confianza final del sistema.
    """
    conf = current_conf
    
    # Asegurar acceso seguro a diccionarios anidados
    np_type = input_case.get("nanoparticle", {}).get("type", "")
    surf_mat = input_case.get("surface", {}).get("material", "")
    lig_type = input_case.get("ligand", {}).get("type", "")

    # Refuerzo por coherencia material-superficie (físicamente más predecible)
    if np_type and surf_mat and np_type == surf_mat:
        conf += 0.05

    # Refuerzo por ligando biológico (interacciones más específicas/estudiadas)
    if lig_type in ("antibody", "peptide", "protein"):
        conf += 0.05

    return min(conf, 0.99)


# --- Reglas de Consenso (Score Boosters) ---

def _consensus_electrostatic(inp: Dict[str, Any]) -> float:
    """Regla C1 — Consenso electrostático fuerte"""
    np_charge = inp.get("nanoparticle", {}).get("surface_charge")
    biom_type = inp.get("biomolecule", {}).get("type")

    if np_charge == "positive" and biom_type in ["DNA", "RNA"]:
        return 0.15
    return 0.0

def _consensus_material_biomolecule(inp: Dict[str, Any]) -> float:
    """Regla C2 — Consenso material–biomolécula"""
    np_type = inp.get("nanoparticle", {}).get("type")
    biom_type = inp.get("biomolecule", {}).get("type")

    if np_type == "metallic" and biom_type in ["DNA", "RNA", "protein"]:
        return 0.12

    if np_type in ["lipid-based", "liposomal"] and biom_type == "RNA":
        return 0.18
    return 0.0

def _consensus_encapsulation(inp: Dict[str, Any]) -> float:
    """Regla C3 — Consenso encapsulación conocida"""
    surf = inp.get("surface", {}).get("material")
    biom = inp.get("biomolecule", {}).get("type")

    if surf in ["peg", "polymer"] and biom in ["DNA", "RNA"]:
        return 0.10
    return 0.0

def _consensus_context(inp: Dict[str, Any]) -> float:
    """Regla C3 (Contexto) — Refuerzo contextual"""
    name = inp.get("context", {}).get("display_name", "").lower()
    keywords = ["in vivo", "clinical", "approved", "therapeutic"]
    if any(k in name for k in keywords):
        return 0.08
    return 0.0


def compute_support_score(result: Dict[str, Any], input_case: Optional[Dict[str, Any]]) -> float:
    """
    Calcula un score de viabilidad para producción (0.0 - 1.0).
    Combina la calidad de la predicción (afinidad/monocapa) con 
    características deseables del material y reglas de consenso.
    """
    score = 0.0

    # Extraer valores de predicción
    if isinstance(result.get("output"), dict):
        action = result.get("output", {})
    else:
        action = result

    affinity = action.get("predicted_affinity", "unknown")
    monolayer = action.get("monolayer_order", "unknown")

    # 1. Afinidad (Max 0.4)
    if affinity == "high":
        score += 0.4
    elif affinity == "moderate":
        score += 0.2

    # 2. Orden de monocapa (Max 0.3)
    if monolayer in ["ordered", "stable"]:
        score += 0.3
    elif monolayer in ["partial", "semi-ordered"]:
        score += 0.15

    # 3. Refuerzos semánticos y Consenso (Max variable, cap en 1.0)
    if input_case:
        ligand_type = input_case.get("ligand", {}).get("type", "")
        np_type = input_case.get("nanoparticle", {}).get("type", "")

        # Base legacy (reducido para dar peso al consenso)
        if ligand_type in ["antibody", "peptide", "peg", "protein"]:
            score += 0.05
        if np_type in ["metallic", "lipid-based", "gold", "silver"]:
            score += 0.05

        # --- NUEVAS REGLAS DE CONSENSO ---
        # Capa 1: Consenso Estructural
        score += _consensus_electrostatic(input_case)
        score += _consensus_material_biomolecule(input_case)
        score += _consensus_encapsulation(input_case)
        
        # Capa 3: Contexto
        score += _consensus_context(input_case)

    # Capa 2: Coherencia Interna (No depende de input_case)
    if affinity == "high" and monolayer in ["ordered", "stable"]:
        score += 0.10

    return min(score, 1.0)


def generate_recommendation(prediction: Dict[str, Any], context: Dict[str, Any], full_case: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Genera recomendación estructurada desde la predicción RDR.
    
    Args:
        prediction: salida del RDR (predicted_affinity, monolayer_order, rule_confidence, etc.)
        context: información del fármaco (display_name, source_code, semantic_type)
        full_case: (Opcional) El caso de entrada completo para ajustes heurísticos de confianza.
    
    Returns:
        Dict con recomendaciones accionables
    """
    # Extraer información clave
    # manejar estructura RDR: resultado puede venir en top-level o dentro de 'output'
    if isinstance(prediction.get("output"), dict):
        action = prediction.get("output", {})
    else:
        # en caso legacy: prediction itself may be the action dict
        action = prediction

    drug_name = context.get("display_name", "Unknown Drug")
    affinity = action.get("predicted_affinity", "unknown")
    monolayer = action.get("monolayer_order", "unknown")
    rule_conf = float(action.get("rule_confidence", 0.0))
    combined_conf = float(prediction.get("prediction_confidence", rule_conf))
    
    # Aplicar ajuste heurístico si tenemos el caso completo
    if full_case:
        combined_conf = confidence_adjustment(combined_conf, full_case)
    
    # Calcular score de viabilidad (Support Score)
    support_score = compute_support_score(prediction, full_case)
        
    rule_name = prediction.get("rule", action.get("rule", "No rule matched"))
    
    # Interpretación de afinidad
    affinity_interpretation = {
        "high": "Alta afinidad ligando-nanopartícula",
        "moderate": "Afinidad moderada ligando-nanopartícula",
        "low": "Baja afinidad ligando-nanopartícula",
        "unknown": "Afinidad no determinada"
    }
    
    # Interpretación de monocapa
    monolayer_interpretation = {
        "stable": "Monocapa estable con orden estructurado",
        "semi-ordered": "Monocapa semi-ordenada con estabilidad intermedia",
        "partial": "Monocapa parcial con cobertura incompleta",
        "ordered": "Monocapa altamente ordenada",
        "fluid": "Monocapa fluida con reorganización dinámica",
        "disordered": "Monocapa desordenada",
        "unstable": "Monocapa inestable con riesgo de desestabilización",
        "unknown": "Orden de monocapa no determinado"
    }
    
    # Generar recomendaciones según el caso
    recommendations = []
    warnings = []
    optimizations = []
    
    # Lógica de recomendaciones basada en afinidad y orden
    if affinity == "high" and monolayer in ["stable", "ordered", "semi-ordered"]:
        recommendations.append("Formulación prometedora desde el punto de vista de afinidad y organización superficial")
        recommendations.append("Proceder con ensayos de caracterización y estabilidad")
        optimizations.extend([
            "Validar tiempo de vida útil (shelf-life) a temperatura controlada",
            "Confirmar reproducibilidad del autoensamblaje en lotes"
        ])
        
        # Optimizaciones específicas por contexto
        if full_case:
            biomolecule = full_case.get("biomolecule", {}).get("type", "").lower()
            np_type = full_case.get("nanoparticle", {}).get("type", "").lower()
            surface_material = full_case.get("surface", {}).get("material", "").lower()
            
            if biomolecule in ["rna", "dna"]:
                optimizations.append("Evaluar integridad de la biomolécula tras encapsulación y almacenamiento")
            
            if "lipid" in rule_name.lower() or np_type == "lipid-based":
                optimizations.append("Validar temperatura de transición de fase lipídica (Tm)")
            
            if surface_material == "peg":
                optimizations.append("Evaluar posible efecto de escudo estérico (PEG shielding) en biodisponibilidad")
            
            if np_type == "metallic":
                optimizations.append("Evaluar agregación y oxidación superficial bajo condiciones fisiológicas")
        
    elif affinity == "high" and monolayer in ["fluid", "disordered"]:
        recommendations.append("Alta afinidad pero estructura de monocapa subóptima")
        warnings.append("Riesgo de reorganización estructural durante almacenamiento")
        optimizations.append("Considerar crosslinking químico para estabilizar monocapa")
        optimizations.append("Evaluar condiciones de temperatura/pH para mejorar orden")
        
    elif affinity == "moderate":
        recommendations.append("Formulación viable con optimizaciones recomendadas")
        if monolayer in ["stable", "semi-ordered"]:
            optimizations.append("Aumentar concentración de ligando para mejorar cobertura")
            optimizations.append("Probar modificaciones químicas del ligando (PEGylation, acetilación)")
        else:
            warnings.append("Monocapa requiere estabilización adicional")
            optimizations.append("Revisar ratio ligando:nanopartícula")
            optimizations.append("Considerar coadyuvantes estabilizadores")
    
    elif affinity == "low":
        warnings.append("Baja afinidad ligando-nanopartícula detectada")
        recommendations.append("NO RECOMENDADO para producción sin modificaciones")
        optimizations.append("CRÍTICO: Rediseñar funcionalización de superficie")
        optimizations.append("Evaluar ligandos alternativos con mejor afinidad")
        optimizations.append("Considerar cambio de estrategia de conjugación")
        
    else:  # unknown
        warnings.append("Datos insuficientes para predicción confiable")
        recommendations.append("Requiere caracterización experimental adicional")
        optimizations.append("Medir zeta potential para determinar carga superficial")
        optimizations.append("Análisis de composición química del recubrimiento")
    
    # Advertencias específicas por tipo de monocapa
    if monolayer == "unstable":
        warnings.append("CRÍTICO: Monocapa inestable - riesgo alto de agregación")
        optimizations.append("Urgente: Modificar condiciones de formulación")
    
    if monolayer == "fluid" and "lipid" in rule_name.lower():
        recommendations.append("Nota: Fluidez esperada en formulaciones lipídicas")
        optimizations.append("Validar temperatura de transición de fase")
    
    # Evaluación de confianza
    confidence_level = "Alta" if combined_conf >= 0.8 else "Media" if combined_conf >= 0.4 else "Baja"
    
    # Construir reporte estructurado
    report = {
        "farmaco": drug_name,
        "codigo_fuente": context.get("source_code", "N/A"),
        "regla_aplicada": rule_name,
        "confianza_prediccion": f"{combined_conf:.2%} ({confidence_level})",
        "resultados": {
            "afinidad": affinity_interpretation.get(affinity, affinity),
            "orden_monocapa": monolayer_interpretation.get(monolayer, monolayer),
            "score_viabilidad": round(support_score, 2)
        },
        "comentarios": recommendations,
        "advertencias": warnings if warnings else ["Ninguna advertencia crítica"],
        "optimizaciones_sugeridas": optimizations if optimizations else ["No se requieren optimizaciones adicionales"],
        "decision_produccion": _decision_produccion(affinity, monolayer, combined_conf, support_score)
    }
    
    return report


def _decision_produccion(affinity: str, monolayer: str, confidence: float, score: float = 0.0) -> str:
    """
    Decisión final go/no-go para producción.
    El score representa la coherencia global del caso.
    La confianza modula la fiabilidad de la inferencia.
    """

    # Rechazo claro: patrón negativo explícito
    if affinity == "low" or monolayer == "unstable":
        return "NO APROBADO - Rediseño necesario"

    # Caso excelente: score máximo con umbral de confianza relajado
    if score >= 0.9 and confidence >= 0.3:
        return "APROBADO para producción - Proceder con validación de lotes"

    # Caso fuerte: score alto y confianza suficiente
    if score >= 0.7 and confidence >= 0.4:
        return "APROBADO para producción - Proceder con validación de lotes"

    # Caso razonable pero incompleto
    if score >= 0.45:
        return "VIABLE CON OPTIMIZACIONES - Implementar mejoras sugeridas"

    # Caso débil
    return "REQUIERE VALIDACIÓN EXPERIMENTAL - Evidencia insuficiente"


def generate_single_drug_report(drug_input: Dict[str, Any]) -> str:
    """
    Genera reporte para un único fármaco (uso en producción).
    
    Args:
        drug_input: input case completo (nanoparticle, ligand, biomolecule, surface, context)
    
    Returns:
        String con reporte formateado para consola/log
    """
    from implementacion_rdr import rule_root
    
    # Evaluar con RDR
    prediction = rule_root.evaluate(drug_input)
    if prediction is None:
        prediction = {
            "rule": "No rule matched",
            "predicted_affinity": "unknown",
            "monolayer_order": "unknown",
            "rule_confidence": 0.0
        }
    
    context = drug_input.get("context", {})
    # Pasamos drug_input como full_case
    report = generate_recommendation(prediction, context, full_case=drug_input)
    
    # Formatear para output de consola
    output = f"""
{'=' * 80}
ANÁLISIS RDR - {report['farmaco']}
{'=' * 80}
Código: {report['codigo_fuente']}
Regla: {report['regla_aplicada']}
Confianza: {report['confianza_prediccion']}

RESULTADOS:
  Afinidad: {report['resultados']['afinidad']}
  Monocapa: {report['resultados']['orden_monocapa']}
  Score Viabilidad: {report['resultados'].get('score_viabilidad', 'N/A')}

COMENTARIOS:
"""
    for rec in report['comentarios']:
        output += f"  {rec}\n"
    
    output += "\nADVERTENCIAS:\n"
    for warn in report['advertencias']:
        output += f"  {warn}\n"
    
    output += "\nOPTIMIZACIONES:\n"
    for opt in report['optimizaciones_sugeridas']:
        output += f"  • {opt}\n"
    
    output += f"\nDECISIÓN: {report['decision_produccion']}\n"
    output += "=" * 80
    
    return output


if __name__ == '__main__':
    pass

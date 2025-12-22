"""
Generador de recomendaciones accionables desde predicciones RDR.

Convierte las salidas JSON del RDR en recomendaciones legibles y accionables
para su uso en producción: decisiones sobre formulación, estabilidad,
optimización de monocapas y potencial terapéutico.

Uso:
    python RDR/generate_recommendations.py
"""
import json
from typing import Dict, Any, List


def generate_recommendation(prediction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera recomendación estructurada desde la predicción RDR.
    
    Args:
        prediction: salida del RDR (predicted_affinity, monolayer_order, rule_confidence, etc.)
        context: información del fármaco (display_name, source_code, semantic_type)
    
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
        recommendations.append("Formulación ÓPTIMA para uso terapéutico")
        recommendations.append("Proceder con ensayos de caracterización y estabilidad")
        optimizations.append("Validar tiempo de vida útil (shelf-life) a temperatura controlada")
        optimizations.append("Confirmar reproducibilidad del autoensamblaje en lotes")
        
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
    confidence_level = "Alta" if combined_conf >= 0.9 else "Media" if combined_conf >= 0.7 else "Baja"
    
    # Construir reporte estructurado
    report = {
        "farmaco": drug_name,
        "codigo_fuente": context.get("source_code", "N/A"),
        "regla_aplicada": rule_name,
        "confianza_prediccion": f"{combined_conf:.2%} ({confidence_level})",
        "resultados": {
            "afinidad": affinity_interpretation.get(affinity, affinity),
            "orden_monocapa": monolayer_interpretation.get(monolayer, monolayer)
        },
        "recomendaciones": recommendations,
        "advertencias": warnings if warnings else ["Ninguna advertencia crítica"],
        "optimizaciones_sugeridas": optimizations if optimizations else ["No se requieren optimizaciones adicionales"],
        "decision_produccion": _decision_produccion(affinity, monolayer, combined_conf)
    }
    
    return report


def _decision_produccion(affinity: str, monolayer: str, confidence: float) -> str:
    """Genera decisión final go/no-go para producción."""
    if confidence < 0.6:
        return "REQUIERE VALIDACIÓN EXPERIMENTAL - Datos insuficientes"
    
    if affinity == "high" and monolayer in ["stable", "ordered", "semi-ordered"]:
        return "APROBADO para producción - Proceder con validación de lotes"
    
    if affinity == "high" and monolayer in ["fluid", "disordered"]:
        return "CONDICIONAL - Validar estabilidad antes de escalar"
    
    if affinity == "moderate" and monolayer in ["stable", "semi-ordered"]:
        return "VIABLE CON OPTIMIZACIONES - Implementar mejoras sugeridas"
    
    if affinity == "low" or monolayer == "unstable":
        return "NO APROBADO - Rediseño necesario"
    
    return "REVISAR - Consultar con equipo de formulación"


def generate_batch_report(predictions_path: str, output_path: str):
    """
    Genera reporte completo desde archivo de predicciones JSONL.
    
    Args:
        predictions_path: ruta al archivo rdr_predictions_vX.jsonl
        output_path: ruta donde guardar el reporte legible
    """
    with open(predictions_path, 'r', encoding='utf-8') as f:
        predictions = [json.loads(line) for line in f if line.strip()]
    
    reports = []
    stats = {
        "aprobados": 0,
        "condicionales": 0,
        "rechazados": 0,
        "requieren_validacion": 0
    }
    
    for pred in predictions:
        context = pred.get("context", {})
        prediction = pred.get("prediction", {})
        
        # Manejar multi-resultado (evaluate_all)
        if prediction.get("multi"):
            # Tomar el primer resultado (mejor match)
            results = prediction.get("results", [])
            if results:
                prediction = results[0]
            else:
                prediction = {}
        
        report = generate_recommendation(prediction, context)
        reports.append(report)
        
        # Estadísticas
        decision = report["decision_produccion"]
        if "APROBADO" in decision:
            stats["aprobados"] += 1
        elif "CONDICIONAL" in decision or "VIABLE" in decision:
            stats["condicionales"] += 1
        elif "NO APROBADO" in decision:
            stats["rechazados"] += 1
        else:
            stats["requieren_validacion"] += 1
    
    # Guardar reporte completo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("REPORTE DE DECISIÓN - SISTEMA RDR NANOFARMACOLOGÍA\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total de fármacos analizados: {len(reports)}\n")
        f.write(f"Aprobados: {stats['aprobados']}\n")
        f.write(f"Condicionales/Viables: {stats['condicionales']}\n")
        f.write(f"Rechazados: {stats['rechazados']}\n")
        f.write(f"Requieren validación: {stats['requieren_validacion']}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        for i, report in enumerate(reports, 1):
            f.write(f"\n{'─' * 80}\n")
            f.write(f"FÁRMACO #{i}: {report['farmaco']}\n")
            f.write(f"{'─' * 80}\n")
            f.write(f"Código NCIt: {report['codigo_fuente']}\n")
            f.write(f"Regla aplicada: {report['regla_aplicada']}\n")
            f.write(f"Confianza: {report['confianza_prediccion']}\n\n")
            
            f.write(f"RESULTADOS:\n")
            f.write(f"  - Afinidad: {report['resultados']['afinidad']}\n")
            f.write(f"  - Monocapa: {report['resultados']['orden_monocapa']}\n\n")
            
            f.write(f"RECOMENDACIONES:\n")
            for rec in report['recomendaciones']:
                f.write(f"  {rec}\n")
            f.write("\n")
            
            f.write(f"ADVERTENCIAS:\n")
            for warn in report['advertencias']:
                f.write(f"  {warn}\n")
            f.write("\n")
            
            f.write(f"OPTIMIZACIONES SUGERIDAS:\n")
            for opt in report['optimizaciones_sugeridas']:
                f.write(f"  - {opt}\n")
            f.write("\n")
            
            f.write(f"DECISIÓN DE PRODUCCIÓN:\n")
            f.write(f"  >>> {report['decision_produccion']} <<<\n")
            f.write("\n")
    
    # Guardar también versión JSON estructurada
    json_output = output_path.replace('.txt', '.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({
            "estadisticas": stats,
            "reportes": reports
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Reporte generado: {output_path}")
    print(f"Versión JSON: {json_output}")
    print(f"\nResumen: {stats['aprobados']} aprobados, {stats['condicionales']} condicionales, "
          f"{stats['rechazados']} rechazados, {stats['requieren_validacion']} requieren validación")


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
    report = generate_recommendation(prediction, context)
    
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

RECOMENDACIONES:
"""
    for rec in report['recomendaciones']:
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


def main():
    """Genera reporte desde las predicciones v4."""
    predictions_path = r"rdr_predictions_v4.jsonl"
    output_path = r"reporte_decisiones_v4.txt"
    
    generate_batch_report(predictions_path, output_path)


if __name__ == '__main__':
    main()

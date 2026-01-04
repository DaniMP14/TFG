"""
Script de análisis de resultados del sistema RDR.
Genera estadísticas y revisa casos difíciles.
"""
import json
from pathlib import Path

def analyze_results():
    results_path = Path(__file__).parent.parent / "rdr_full_evaluation_results.json"
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    reportes = data['reportes']
    stats = data['estadisticas']
    total = sum(stats.values())
    
    print("=" * 70)
    print("ANÁLISIS DE RESULTADOS - SISTEMA RDR NANOFARMACOLOGÍA")
    print("=" * 70)
    
    # Distribución general
    print("\n📊 DISTRIBUCIÓN GENERAL")
    print("-" * 40)
    for k, v in stats.items():
        bar = "█" * int(v / total * 30)
        print(f"  {k:25} {v:3} ({v/total*100:5.1f}%) {bar}")
    print(f"  {'TOTAL':25} {total:3}")
    
    # Distribución de reglas
    print("\n📋 REGLAS MÁS APLICADAS")
    print("-" * 40)
    reglas = {}
    for r in reportes:
        regla = r['regla_aplicada']
        reglas[regla] = reglas.get(regla, 0) + 1
    for regla, count in sorted(reglas.items(), key=lambda x: -x[1])[:10]:
        print(f"  {regla[:45]:45} {count:3}")
    
    # Distribución de scores
    print("\n📈 DISTRIBUCIÓN DE SCORE VIABILIDAD")
    print("-" * 40)
    scores = [r['resultados']['score_viabilidad'] for r in reportes]
    bins = [(0, 0.3, "Bajo"), (0.3, 0.5, "Medio-Bajo"), (0.5, 0.7, "Medio"), (0.7, 0.9, "Alto"), (0.9, 1.01, "Muy Alto")]
    for lo, hi, label in bins:
        count = sum(1 for s in scores if lo <= s < hi)
        bar = "█" * int(count / total * 30)
        print(f"  {label:15} [{lo:.1f}-{hi:.1f}): {count:3} {bar}")
    print(f"  Score promedio: {sum(scores)/len(scores):.3f}")
    print(f"  Score máximo:   {max(scores):.3f}")
    print(f"  Score mínimo:   {min(scores):.3f}")
    
    # Casos RECHAZADOS
    print("\n" + "=" * 70)
    print("❌ CASOS RECHAZADOS (NO APROBADO)")
    print("=" * 70)
    rechazados = [r for r in reportes if 'NO APROBADO' in r['decision_produccion']]
    for i, r in enumerate(rechazados, 1):
        print(f"\n[{i}] {r['farmaco']}")
        print(f"    Código: {r['codigo_fuente']}")
        print(f"    Regla: {r['regla_aplicada']}")
        print(f"    Afinidad: {r['resultados']['afinidad']}")
        print(f"    Monocapa: {r['resultados']['orden_monocapa']}")
        print(f"    Score: {r['resultados']['score_viabilidad']}")
        print(f"    Advertencias: {r['advertencias']}")
    
    # Casos REQUIEREN VALIDACIÓN
    print("\n" + "=" * 70)
    print("⚠️  CASOS QUE REQUIEREN VALIDACIÓN EXPERIMENTAL")
    print("=" * 70)
    validacion = [r for r in reportes if 'REQUIERE VALIDACIÓN' in r['decision_produccion']]
    for i, r in enumerate(validacion, 1):
        print(f"\n[{i}] {r['farmaco']}")
        print(f"    Código: {r['codigo_fuente']}")
        print(f"    Regla: {r['regla_aplicada']}")
        print(f"    Afinidad: {r['resultados']['afinidad']}")
        print(f"    Score: {r['resultados']['score_viabilidad']}")
    
    # Top APROBADOS (mejores scores)
    print("\n" + "=" * 70)
    print("✅ TOP 10 APROBADOS (mayor score)")
    print("=" * 70)
    aprobados = [r for r in reportes if 'APROBADO' in r['decision_produccion'] and 'NO APROBADO' not in r['decision_produccion']]
    aprobados_sorted = sorted(aprobados, key=lambda x: -x['resultados']['score_viabilidad'])
    for i, r in enumerate(aprobados_sorted[:10], 1):
        print(f"  {i:2}. [{r['resultados']['score_viabilidad']:.2f}] {r['farmaco'][:55]}")
        print(f"      Regla: {r['regla_aplicada']}")
    
    # Casos CONDICIONALES con score alto (casi aprobados)
    print("\n" + "=" * 70)
    print("🔶 CONDICIONALES CON SCORE ALTO (cerca de aprobación)")
    print("=" * 70)
    condicionales = [r for r in reportes if 'VIABLE' in r['decision_produccion']]
    cond_altos = sorted(condicionales, key=lambda x: -x['resultados']['score_viabilidad'])[:10]
    for i, r in enumerate(cond_altos, 1):
        print(f"  {i:2}. [{r['resultados']['score_viabilidad']:.2f}] {r['farmaco'][:55]}")
    
    # Análisis de coherencia
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN DE COHERENCIA")
    print("=" * 70)
    
    # Casos con afinidad "high" pero rechazados
    high_aff_rejected = [r for r in rechazados if 'Alta afinidad' in r['resultados']['afinidad']]
    print(f"\n  Afinidad alta pero rechazados: {len(high_aff_rejected)}")
    for r in high_aff_rejected:
        print(f"    - {r['farmaco'][:40]} (monocapa: {r['resultados']['orden_monocapa'][:30]}...)")
    
    # Casos con afinidad "low" pero aprobados (no debería haber)
    low_aff_approved = [r for r in aprobados if 'Baja afinidad' in r['resultados']['afinidad']]
    print(f"\n  Afinidad baja pero aprobados: {len(low_aff_approved)}")
    if low_aff_approved:
        print("    ⚠️ ALERTA: Esto indica un problema en las reglas de decisión")
        for r in low_aff_approved:
            print(f"    - {r['farmaco']}")
    else:
        print("    ✅ OK - Ningún caso con baja afinidad fue aprobado")
    
    # Casos con monocapa "unstable" pero aprobados (no debería haber)
    unstable_approved = [r for r in aprobados if 'inestable' in r['resultados']['orden_monocapa'].lower()]
    print(f"\n  Monocapa inestable pero aprobados: {len(unstable_approved)}")
    if unstable_approved:
        print("    ⚠️ ALERTA: Esto indica un problema en las reglas de decisión")
    else:
        print("    ✅ OK - Ningún caso con monocapa inestable fue aprobado")
    
    print("\n" + "=" * 70)
    print("FIN DEL ANÁLISIS")
    print("=" * 70)


if __name__ == '__main__':
    analyze_results()

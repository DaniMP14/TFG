"""
Análisis en profundidad del nanoparticle.surface_charge en rdr_inputs_v1.jsonl

Objetivos:
1. Distribución de labels (positive/negative/neutral/unknown/ambiguous)
2. Distribución de provenance (keywords/parametric:zeta/inferred/conflict/none)
3. Estadísticas de confianza por label
4. Casos con zeta potential detectado
5. Casos unknown con análisis de contenido textual
6. Identificar oportunidades de mejora en la inferencia
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict

def load_jsonl(path):
    """Cargar archivo JSONL"""
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def analyze_np_charge(inputs):
    """Análisis completo de nanoparticle.surface_charge"""
    
    # Estadísticas básicas
    labels = []
    provenances = []
    confidences = []
    
    # Agrupación por label
    by_label = defaultdict(list)
    
    # Casos especiales
    zeta_cases = []
    unknown_cases = []
    ambiguous_cases = []
    high_conf_cases = []
    
    for entry in inputs:
        np = entry.get("nanoparticle", {})
        ctx = entry.get("context", {})
        
        label = np.get("surface_charge", "unknown")
        conf = np.get("surface_charge_confidence", 0.0)
        prov = np.get("surface_charge_provenance", "none")
        
        labels.append(label)
        provenances.append(prov)
        confidences.append(conf)
        
        case_info = {
            "code": ctx.get("source_code"),
            "display": ctx.get("display_name"),
            "label": label,
            "confidence": conf,
            "provenance": prov
        }
        
        by_label[label].append(case_info)
        
        # Detectar casos con zeta
        if "zeta" in prov:
            zeta_cases.append(case_info)
        
        # Casos unknown para analizar
        if label == "unknown":
            unknown_cases.append(case_info)
        
        # Casos ambiguous
        if label == "ambiguous":
            ambiguous_cases.append(case_info)
        
        # High confidence
        if conf >= 0.9:
            high_conf_cases.append(case_info)
    
    # Imprimir resultados
    print("=" * 80)
    print("ANÁLISIS DE NANOPARTICLE.SURFACE_CHARGE (v1)")
    print("=" * 80)
    
    print(f"\n📊 TOTAL DE CASOS: {len(inputs)}")
    
    # Distribución de labels
    print("\n" + "─" * 80)
    print("1️⃣  DISTRIBUCIÓN DE LABELS")
    print("─" * 80)
    label_counts = Counter(labels)
    for label, count in label_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {label:15s}: {count:3d} ({pct:5.1f}%)")
    
    # Distribución de provenance
    print("\n" + "─" * 80)
    print("2️⃣  DISTRIBUCIÓN DE PROVENANCE")
    print("─" * 80)
    prov_counts = Counter(provenances)
    for prov, count in prov_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {prov:35s}: {count:3d} ({pct:5.1f}%)")
    
    # Estadísticas de confianza
    print("\n" + "─" * 80)
    print("3️⃣  ESTADÍSTICAS DE CONFIANZA")
    print("─" * 80)
    for label in sorted(by_label.keys()):
        cases = by_label[label]
        confs = [c["confidence"] for c in cases]
        if confs:
            avg = sum(confs) / len(confs)
            min_c = min(confs)
            max_c = max(confs)
            print(f"  {label:15s}: avg={avg:.3f}, min={min_c:.3f}, max={max_c:.3f} (n={len(cases)})")
    
    # Casos con zeta potential
    print("\n" + "─" * 80)
    print("4️⃣  CASOS CON ZETA POTENTIAL DETECTADO")
    print("─" * 80)
    print(f"  Total: {len(zeta_cases)}")
    if zeta_cases:
        print("\n  Listado:")
        for case in zeta_cases:
            print(f"    {case['code']:10s} | {case['label']:10s} | conf={case['confidence']:.2f} | {case['provenance']}")
            print(f"      → {case['display'][:80]}")
    else:
        print("  ⚠️  NO SE DETECTÓ ZETA POTENTIAL EN NINGÚN CASO")
    
    # Casos ambiguous (conflictos)
    print("\n" + "─" * 80)
    print("5️⃣  CASOS AMBIGUOUS (CONFLICTOS)")
    print("─" * 80)
    print(f"  Total: {len(ambiguous_cases)}")
    if ambiguous_cases:
        print("\n  Listado:")
        for case in ambiguous_cases:
            print(f"    {case['code']:10s} | {case['provenance']}")
            print(f"      → {case['display'][:80]}")
    
    # Casos high confidence
    print("\n" + "─" * 80)
    print("6️⃣  CASOS DE ALTA CONFIANZA (≥0.90)")
    print("─" * 80)
    print(f"  Total: {len(high_conf_cases)}")
    label_high = Counter([c["label"] for c in high_conf_cases])
    for label, count in label_high.most_common():
        print(f"    {label:15s}: {count:3d}")
    
    # Análisis de casos UNKNOWN
    print("\n" + "─" * 80)
    print("7️⃣  ANÁLISIS DE CASOS UNKNOWN")
    print("─" * 80)
    print(f"  Total: {len(unknown_cases)}")
    
    # Subgrupo por provenance
    unknown_by_prov = defaultdict(list)
    for case in unknown_cases:
        unknown_by_prov[case["provenance"]].append(case)
    
    print("\n  Por provenance:")
    for prov, cases in sorted(unknown_by_prov.items(), key=lambda x: -len(x[1])):
        print(f"    {prov:35s}: {len(cases):3d}")
    
    # Mostrar muestra de casos unknown (primeros 10)
    print("\n  📋 Muestra de casos UNKNOWN (primeros 10):")
    for i, case in enumerate(unknown_cases[:10], 1):
        print(f"\n  [{i}] {case['code']} | conf={case['confidence']:.2f} | prov={case['provenance']}")
        print(f"      {case['display'][:100]}")
    
    return {
        "label_counts": label_counts,
        "prov_counts": prov_counts,
        "by_label": by_label,
        "zeta_cases": zeta_cases,
        "unknown_cases": unknown_cases,
        "ambiguous_cases": ambiguous_cases,
        "high_conf_cases": high_conf_cases
    }


def deep_dive_unknown(inputs, csv_path):
    """Análisis profundo de casos unknown con acceso al CSV original"""
    import pandas as pd
    
    # Cargar CSV original
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    # Filtrar casos unknown
    unknown_cases = []
    for entry in inputs:
        np = entry.get("nanoparticle", {})
        if np.get("surface_charge") == "unknown":
            code = entry["context"]["source_code"]
            unknown_cases.append({
                "code": code,
                "display": entry["context"]["display_name"],
                "conf": np["surface_charge_confidence"],
                "prov": np["surface_charge_provenance"]
            })
    
    print("\n" + "=" * 80)
    print("DEEP DIVE: CASOS UNKNOWN CON TEXTO ORIGINAL")
    print("=" * 80)
    
    # Buscar patrones en el texto que podrían indicar carga
    charge_keywords = {
        "positive": r"\b(cationic|positive|positively|quaternary|amine|chitosan|polylysine)\b",
        "negative": r"\b(anionic|negative|negatively|carboxyl|sulfate|phosphate)\b",
        "neutral": r"\b(neutral|uncharged|zwitterionic)\b",
        "zeta": r"zeta\s*potential|zeta\s*\+|\+\s*\d+\s*mv|-\s*\d+\s*mv"
    }
    
    pattern_matches = defaultdict(list)
    
    for case in unknown_cases[:20]:  # primeros 20 para no saturar
        # Buscar en el CSV
        row = df[df["Code"] == case["code"]]
        if row.empty:
            continue
        
        row = row.iloc[0]
        definition = str(row.get("Definition", ""))
        synonyms = str(row.get("Synonyms", ""))
        display = str(row.get("Display Name", ""))
        
        full_text = f"{display} {synonyms} {definition}".lower()
        
        print(f"\n{'─' * 80}")
        print(f"CODE: {case['code']}")
        print(f"DISPLAY: {case['display'][:80]}")
        print(f"DEFINITION: {definition[:200]}")
        
        # Buscar patrones
        found_patterns = []
        for pattern_name, pattern in charge_keywords.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                found_patterns.append(f"{pattern_name}: {matches[:3]}")
                pattern_matches[pattern_name].append(case["code"])
        
        if found_patterns:
            print(f"⚠️  PATRONES DETECTADOS: {', '.join(found_patterns)}")
            print("   → Este caso DEBERÍA tener carga inferida")
        else:
            print("✓  No se detectan keywords obvias de carga")
    
    # Resumen de patrones perdidos
    print("\n" + "=" * 80)
    print("RESUMEN: PATRONES DE CARGA EN CASOS UNKNOWN")
    print("=" * 80)
    for pattern_name, codes in pattern_matches.items():
        print(f"  {pattern_name:10s}: {len(codes)} casos con keywords no detectadas")


if __name__ == "__main__":
    # Rutas
    jsonl_path = Path(__file__).parent / "../rdr_inputs_v1.jsonl"
    csv_path = Path(__file__).parent.parent.parent / "datasets" / "dataset_FINAL2.csv"
    
    # Cargar datos
    print("Cargando datos...")
    inputs = load_jsonl(jsonl_path)
    
    # Análisis principal
    results = analyze_np_charge(inputs)
    
    # Deep dive en unknown
    print("\n\n")
    deep_dive_unknown(inputs, csv_path)
    
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

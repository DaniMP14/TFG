"""
Análisis de TODOS los casos unknown para identificar patterns perdidos en la detección de carga.

Busca:
1. Menciones explícitas de carga (positive, negative, neutral, cationic, anionic)
2. Valores de zeta potential (±X mV)
3. Chemical groups indicativos (amine, carboxyl, sulfate, etc.)
4. Contextos implícitos (pH-sensitive, protonated, deprotonated)
"""

import json
import re
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def analyze_missed_patterns():
    # Cargar datos
    jsonl_path = Path(__file__).parent / "../rdr_inputs_v1.jsonl"
    csv_path = Path(__file__).parent.parent.parent / "datasets" / "dataset_FINAL2.csv"
    
    inputs = load_jsonl(jsonl_path)
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    # Filtrar casos unknown
    unknown_codes = [
        entry["context"]["source_code"]
        for entry in inputs
        if entry.get("nanoparticle", {}).get("surface_charge") == "unknown"
    ]
    
    print("=" * 80)
    print(f"ANÁLISIS DE PATTERNS PERDIDOS EN {len(unknown_codes)} CASOS UNKNOWN")
    print("=" * 80)
    
    # Patterns a buscar (expandidos)
    patterns = {
        "zeta_explicit": r"zeta\s*potential\s*[:]?\s*([+\-]?\d+(?:[.,]\d+)?)\s*(m?v|millivolt)?",
        "zeta_value": r"([+\-]\s?\d+(?:[.,]\d+)?)\s*(m?v|millivolt)",
        "positive_explicit": r"\b(cationic|positively\s*charged|positive\s*charge|positive\s*surface|\+\s*charge|cation)\b",
        "negative_explicit": r"\b(anionic|negatively\s*charged|negative\s*charge|negative\s*surface|\-\s*charge|anion)\b",
        "neutral_explicit": r"\b(neutral|uncharged|no\s*charge|zero\s*charge|electrically\s*neutral)\b",
        "zwitterionic": r"\b(zwitterionic|zwitter)\b",
        
        # Chemical groups (más específico)
        "amine_groups": r"\b(amine|amino|ammonium|quaternary\s*ammonium|nh2|nh3\+)\b",
        "carboxyl_groups": r"\b(carboxyl|carboxylic|carboxylate|cooh|coo\-)\b",
        "sulfate_groups": r"\b(sulfate|sulfo|sulfonate|so4|so3)\b",
        "phosphate_groups": r"\b(phosphate|phospho|po4)\b",
        
        # Polymers con carga conocida
        "cationic_polymers": r"\b(polyethylenimine|pei|chitosan|pdadmac|polylysine|poly\s*lysine|pll)\b",
        "anionic_polymers": r"\b(alginate|poly\s*acrylic|polyacrylate|carboxymethyl|poly\s*glutamic)\b",
        
        # Lipids con carga
        "cationic_lipids": r"\b(dotap|dotma|dope|dodap|ddab|dc-chol|cationic\s*lipid)\b",
        "anionic_lipids": r"\b(dops|dopg|cardiolipin|anionic\s*lipid)\b",
        
        # Contextos de pH
        "ph_sensitive": r"\b(ph[-\s]sensitive|ph[-\s]responsive|protonated|deprotonated)\b",
        
        # Coating/modification indicators
        "surface_modification": r"\b(surface\s*modified|surface\s*functionalized|coated\s*with|grafted\s*with)\b",
    }
    
    # Compilar patterns
    compiled = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in patterns.items()}
    
    # Análisis por pattern
    pattern_hits = defaultdict(list)
    detailed_cases = []
    
    for code in unknown_codes:
        row = df[df["Code"] == code]
        if row.empty:
            continue
        
        row = row.iloc[0]
        display = str(row.get("Display Name", ""))
        definition = str(row.get("Definition", ""))
        synonyms = str(row.get("Synonyms", ""))
        
        full_text = f"{display} | {synonyms} | {definition}".lower()
        
        # Buscar matches
        case_matches = {}
        for pattern_name, pattern_re in compiled.items():
            matches = pattern_re.findall(full_text)
            if matches:
                case_matches[pattern_name] = matches
                pattern_hits[pattern_name].append({
                    "code": code,
                    "display": display,
                    "matches": matches
                })
        
        if case_matches:
            detailed_cases.append({
                "code": code,
                "display": display,
                "definition": definition[:150],
                "matches": case_matches
            })
    
    # Resultados
    print(f"\n📊 RESUMEN DE PATTERNS DETECTADOS EN CASOS UNKNOWN:")
    print("─" * 80)
    
    for pattern_name in sorted(pattern_hits.keys(), key=lambda x: -len(pattern_hits[x])):
        count = len(pattern_hits[pattern_name])
        pct = 100 * count / len(unknown_codes)
        print(f"  {pattern_name:25s}: {count:3d} casos ({pct:4.1f}%)")
    
    # Casos más problemáticos (múltiples patterns detectados)
    multi_pattern_cases = [c for c in detailed_cases if len(c["matches"]) >= 2]
    
    print(f"\n\n🚨 CASOS CON MÚLTIPLES PATTERNS ({len(multi_pattern_cases)} casos):")
    print("─" * 80)
    print("(Estos son los más problemáticos - tienen señales claras pero no se detectaron)\n")
    
    for i, case in enumerate(sorted(multi_pattern_cases, key=lambda x: -len(x["matches"]))[:15], 1):
        print(f"\n[{i}] {case['code']} | {case['display'][:60]}")
        print(f"    Definition: {case['definition']}")
        print(f"    Patterns detectados:")
        for pattern_name, matches in sorted(case["matches"].items()):
            print(f"      • {pattern_name:25s}: {matches[:5]}")
    
    # Casos con zeta potential explícito
    zeta_cases = pattern_hits.get("zeta_explicit", []) + pattern_hits.get("zeta_value", [])
    if zeta_cases:
        print(f"\n\n⚡ CASOS CON ZETA POTENTIAL EXPLÍCITO ({len(zeta_cases)} casos):")
        print("─" * 80)
        for case in zeta_cases[:10]:
            print(f"\n  {case['code']:10s} | {case['display'][:60]}")
            print(f"    Matches: {case['matches']}")
    
    # Estadísticas finales
    total_with_signals = len(detailed_cases)
    pct_with_signals = 100 * total_with_signals / len(unknown_codes)
    
    print(f"\n\n📈 ESTADÍSTICAS FINALES:")
    print("─" * 80)
    print(f"  Total casos unknown: {len(unknown_codes)}")
    print(f"  Casos con al menos 1 pattern: {total_with_signals} ({pct_with_signals:.1f}%)")
    print(f"  Casos con 2+ patterns: {len(multi_pattern_cases)} ({100*len(multi_pattern_cases)/len(unknown_codes):.1f}%)")
    print(f"  Casos sin ningún pattern: {len(unknown_codes) - total_with_signals} ({100*(len(unknown_codes)-total_with_signals)/len(unknown_codes):.1f}%)")
    
    # Guardar casos problemáticos a CSV para revisión manual
    if detailed_cases:
        output_df = pd.DataFrame([
            {
                "code": c["code"],
                "display": c["display"],
                "definition": c["definition"],
                "patterns_detected": ", ".join(c["matches"].keys()),
                "num_patterns": len(c["matches"])
            }
            for c in detailed_cases
        ])
        output_path = Path(__file__).parent / "outs" / "missed_charge_patterns.csv"
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n💾 Casos problemáticos guardados en: {output_path}")
    
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    analyze_missed_patterns()

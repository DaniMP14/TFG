"""
Análisis profundo de biomolecule.type en v3

Objetivos:
1. Distribución de biomolecule.type
2. Casos unknown que podrían tener biomoléculas detectables
3. Identificar patterns perdidos para mejorar detección
"""

import json
import re
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def analyze_biomolecules():
    # Cargar datos
    jsonl_path = Path(__file__).parent / "rdr_inputs_v3.jsonl"
    csv_path = Path(__file__).parent.parent / "datasets" / "dataset_FINAL2.csv"
    
    inputs = load_jsonl(jsonl_path)
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    print("=" * 80)
    print("ANÁLISIS DE BIOMOLECULE.TYPE (v3)")
    print("=" * 80)
    print(f"\n📊 TOTAL CASOS: {len(inputs)}")
    
    # Distribución
    biomol_types = [entry["biomolecule"]["type"] for entry in inputs]
    type_counts = Counter(biomol_types)
    
    print("\n" + "─" * 80)
    print("1️⃣  DISTRIBUCIÓN DE BIOMOLECULE.TYPE")
    print("─" * 80)
    for t, count in type_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {t:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Buscar patterns perdidos en casos unknown
    print("\n" + "─" * 80)
    print("2️⃣  BÚSQUEDA DE PATTERNS PERDIDOS EN BIOMOLECULE.TYPE=UNKNOWN")
    print("─" * 80)
    
    patterns = {
        # Ácidos nucleicos específicos
        "plasmid": r"\b(plasmid)\b",
        "circular_dna": r"\b(circular dna|cccDNA)\b",
        "cdna": r"\b(cdna|complementary dna)\b",
        
        # RNA específicos (adicionales)
        "lncrna": r"\b(lncRNA|long non-coding RNA)\b",
        "shrna": r"\b(shRNA|short hairpin RNA)\b",
        "asorna": r"\b(asoRNA|antisense oligonucleotide)\b",
        
        # Proteínas específicas
        "cytokine": r"\b(cytokine|interleukin|il-\d+|interferon|ifn|tnf)\b",
        "enzyme": r"\b(enzyme|kinase|phosphatase|protease|polymerase)\b",
        "growth_factor": r"\b(growth factor|egf|vegf|fgf|pdgf|tgf)\b",
        "toxin": r"\b(toxin|ricin|diphtheria)\b",
        
        # Péptidos específicos
        "antimicrobial_peptide": r"\b(antimicrobial peptide|amp)\b",
        "cyclic_peptide": r"\b(cyclic peptide)\b",
        
        # Polisacáridos específicos
        "chitosan": r"\b(chitosan)\b",
        "hyaluronic": r"\b(hyaluronic acid|hyaluronate)\b",
        "dextran": r"\b(dextran)\b",
        "heparin": r"\b(heparin)\b",
        
        # Lípidos y membranas
        "phospholipid": r"\b(phospholipid|phosphatidyl)\b",
        "cholesterol": r"\b(cholesterol)\b",
        "ceramide": r"\b(ceramide)\b",
        
        # Antígenos y receptores específicos
        "tumor_antigen": r"\b(tumor antigen|cancer antigen|cea|psa)\b",
        "viral_antigen": r"\b(viral antigen|hpv|hepatitis)\b",
        "egfr": r"\b(egfr|epidermal growth factor receptor)\b",
        "her2": r"\b(her2|erbb2)\b",
        "cd_marker": r"\b(cd\d{1,3})\b",
        "pd1_pdl1": r"\b(pd-1|pd-l1|pdl1|programmed death)\b",
        "ctla4": r"\b(ctla-4|ctla4)\b",
        
        # Genes y factores de transcripción
        "oncogene": r"\b(oncogene|kras|braf|myc|her2)\b",
        "tumor_suppressor": r"\b(tumor suppressor|p53|rb|pten)\b",
        "transcription_factor": r"\b(transcription factor|nf-kb|stat|ap-1)\b",
        
        # Otros
        "lipid": r"\b(?<!phospho)lipid\b",
        "carbohydrate": r"\b(carbohydrate|sugar|glycan)\b",
        "nucleotide": r"\b(nucleotide|nucleoside)\b",
    }
    
    compiled = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in patterns.items()}
    
    unknown_biomol = [entry for entry in inputs if entry["biomolecule"]["type"] == "unknown"]
    pattern_hits = defaultdict(list)
    
    # Analizar casos unknown
    for entry in unknown_biomol:
        code = entry["context"]["source_code"]
        row = df[df["Code"] == code]
        if row.empty:
            continue
        
        row = row.iloc[0]
        display = str(row.get("Display Name", ""))
        definition = str(row.get("Definition", ""))
        synonyms = str(row.get("Synonyms", ""))
        
        full_text = f"{display} | {synonyms} | {definition}".lower()
        
        for pattern_name, pattern_re in compiled.items():
            if pattern_re.search(full_text):
                pattern_hits[pattern_name].append({
                    "code": code,
                    "display": display,
                    "text": full_text[:150]
                })
    
    print(f"\nCasos unknown: {len(unknown_biomol)}")
    print("\nPatterns detectados:")
    for pattern_name in sorted(pattern_hits.keys(), key=lambda x: -len(pattern_hits[x])):
        count = len(pattern_hits[pattern_name])
        pct = 100 * count / len(unknown_biomol) if unknown_biomol else 0
        print(f"  {pattern_name:30s}: {count:3d} casos ({pct:4.1f}%)")
    
    # Mostrar ejemplos de patterns más frecuentes
    print("\n" + "─" * 80)
    print("3️⃣  EJEMPLOS DE PATTERNS MÁS FRECUENTES")
    print("─" * 80)
    
    for pattern_name in sorted(pattern_hits.keys(), key=lambda x: -len(pattern_hits[x]))[:10]:
        cases = pattern_hits[pattern_name]
        print(f"\n🔹 {pattern_name.upper()} ({len(cases)} casos):")
        for i, case in enumerate(cases[:3], 1):
            print(f"  [{i}] {case['code']} | {case['display'][:60]}")
    
    # Análisis de solapamientos (casos con múltiples patterns)
    print("\n" + "─" * 80)
    print("4️⃣  CASOS CON MÚLTIPLES PATTERNS DETECTADOS")
    print("─" * 80)
    
    multi_pattern_cases = defaultdict(list)
    for entry in unknown_biomol:
        code = entry["context"]["source_code"]
        patterns_found = []
        for pattern_name, cases in pattern_hits.items():
            if any(c["code"] == code for c in cases):
                patterns_found.append(pattern_name)
        
        if len(patterns_found) >= 2:
            multi_pattern_cases[code] = patterns_found
    
    print(f"\nTotal casos con 2+ patterns: {len(multi_pattern_cases)}")
    if multi_pattern_cases:
        print("\nMuestra (primeros 5):")
        for i, (code, patterns) in enumerate(list(multi_pattern_cases.items())[:5], 1):
            entry = next((e for e in unknown_biomol if e["context"]["source_code"] == code), None)
            if entry:
                print(f"  [{i}] {code} | {entry['context']['display_name'][:50]}")
                print(f"      Patterns: {', '.join(patterns)}")
    
    # Guardar resultados
    if pattern_hits:
        output_data = []
        for pattern_name, cases in pattern_hits.items():
            for case in cases:
                output_data.append({
                    "code": case["code"],
                    "display": case["display"],
                    "pattern_detected": pattern_name
                })
        
        output_df = pd.DataFrame(output_data)
        output_path = Path(__file__).parent / "outs" / "missed_biomolecule_patterns.csv"
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n💾 Casos guardados en: {output_path}")
    
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    analyze_biomolecules()

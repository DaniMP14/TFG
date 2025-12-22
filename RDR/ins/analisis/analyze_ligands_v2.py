"""
Análisis profundo de ligand properties en v2

Objetivos:
1. Distribución de ligand.type, ligand.charge, ligand.polarity
2. Casos con unknowns que podrían tener ligandos detectables
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

def analyze_ligands():
    # Cargar datos
    jsonl_path = Path(__file__).parent / "../rdr_inputs_v2.jsonl"
    csv_path = Path(__file__).parent.parent.parent / "datasets" / "dataset_FINAL2.csv"
    
    inputs = load_jsonl(jsonl_path)
    df = pd.read_csv(csv_path, encoding='utf-8')
    
    print("=" * 80)
    print("ANÁLISIS DE LIGAND PROPERTIES (v2)")
    print("=" * 80)
    print(f"\n📊 TOTAL CASOS: {len(inputs)}")
    
    # Distribuciones
    types = [entry["ligand"]["type"] for entry in inputs]
    charges = [entry["ligand"]["charge"] for entry in inputs]
    polarities = [entry["ligand"]["polarity"] for entry in inputs]
    
    type_counts = Counter(types)
    charge_counts = Counter(charges)
    polarity_counts = Counter(polarities)
    
    # Ligand type
    print("\n" + "─" * 80)
    print("1️⃣  LIGAND TYPE")
    print("─" * 80)
    for t, count in type_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {t:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Ligand charge
    print("\n" + "─" * 80)
    print("2️⃣  LIGAND CHARGE")
    print("─" * 80)
    for c, count in charge_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {c:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Ligand polarity
    print("\n" + "─" * 80)
    print("3️⃣  LIGAND POLARITY")
    print("─" * 80)
    for p, count in polarity_counts.most_common():
        pct = 100 * count / len(inputs)
        print(f"  {p:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Casos con ligand type conocido pero charge/polarity unknown
    print("\n" + "─" * 80)
    print("4️⃣  CASOS CON TYPE CONOCIDO PERO CHARGE/POLARITY UNKNOWN")
    print("─" * 80)
    
    incomplete_ligands = []
    for entry in inputs:
        lig = entry["ligand"]
        if lig["type"] not in ["unknown"] and (lig["charge"] == "unknown" or lig["polarity"] == "unknown"):
            incomplete_ligands.append({
                "code": entry["context"]["source_code"],
                "display": entry["context"]["display_name"],
                "type": lig["type"],
                "charge": lig["charge"],
                "polarity": lig["polarity"]
            })
    
    print(f"Total: {len(incomplete_ligands)} casos")
    if incomplete_ligands:
        print("\nMuestra (primeros 10):")
        for i, case in enumerate(incomplete_ligands[:10], 1):
            print(f"  [{i}] {case['code']} | type={case['type']:15s} | charge={case['charge']:10s} | polarity={case['polarity']:10s}")
            print(f"       {case['display'][:75]}")
    
    # Buscar patterns perdidos en casos unknown
    print("\n" + "─" * 80)
    print("5️⃣  BÚSQUEDA DE PATTERNS PERDIDOS EN LIGAND TYPE=UNKNOWN")
    print("─" * 80)
    
    patterns = {
        # Ligands comunes en nanopartículas terapéuticas
        "transferrin": r"\b(transferrin|tf)\b",
        "egf": r"\b(egf|epidermal growth factor)\b",
        "her2": r"\b(her2|herceptin|trastuzumab)\b",
        "cd": r"\b(cd\d{1,3})\b",  # CD markers
        "integrin": r"\b(integrin|rgd)\b",
        "hyaluronic": r"\b(hyaluronic|hyaluronate|ha)\b",
        "albumin": r"\b(albumin|hsa|human serum albumin)\b",
        "biotin": r"\b(biotin)\b",
        "streptavidin": r"\b(streptavidin)\b",
        "galactose": r"\b(galactose|galactosyl)\b",
        "mannose": r"\b(mannose|mannosyl)\b",
        "glucose": r"\b(glucose|glucosyl)\b",
        "lactose": r"\b(lactose|lactosyl)\b",
        
        # Modificaciones de superficie
        "polyethylene_glycol": r"\b(polyethylene glycol|peg[\s\-]?\d+)\b",
        "carboxyl": r"\b(carboxyl|carboxy)\b",
        "hydroxyl": r"\b(hydroxyl)\b",
        "thiol": r"\b(thiol|sulfhydryl)\b",
        
        # Palabras clave targeting
        "conjugated_to": r"\b(conjugated to|conjugated with|linked to|attached to)\b",
        "decorated_with": r"\b(decorated with|functionalized with|modified with)\b",
        "coated_with": r"\b(coated with|coated by)\b",
    }
    
    compiled = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in patterns.items()}
    
    unknown_ligands = [entry for entry in inputs if entry["ligand"]["type"] == "unknown"]
    pattern_hits = defaultdict(list)
    
    for entry in unknown_ligands:
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
    
    print(f"\nCasos unknown type: {len(unknown_ligands)}")
    print("\nPatterns detectados:")
    for pattern_name in sorted(pattern_hits.keys(), key=lambda x: -len(pattern_hits[x])):
        count = len(pattern_hits[pattern_name])
        pct = 100 * count / len(unknown_ligands)
        print(f"  {pattern_name:25s}: {count:3d} casos ({pct:4.1f}%)")
    
    # Mostrar ejemplos de patterns más frecuentes
    print("\n" + "─" * 80)
    print("6️⃣  EJEMPLOS DE PATTERNS MÁS FRECUENTES")
    print("─" * 80)
    
    for pattern_name in sorted(pattern_hits.keys(), key=lambda x: -len(pattern_hits[x]))[:5]:
        cases = pattern_hits[pattern_name]
        print(f"\n🔹 {pattern_name.upper()} ({len(cases)} casos):")
        for i, case in enumerate(cases[:3], 1):
            print(f"  [{i}] {case['code']} | {case['display'][:60]}")
    
    # Guardar casos problemáticos
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
        output_path = Path(__file__).parent / "outs" / "missed_ligand_patterns.csv"
        output_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n💾 Casos guardados en: {output_path}")
    
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    analyze_ligands()

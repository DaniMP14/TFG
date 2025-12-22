"""
Comparación entre rdr_inputs_v2.jsonl y rdr_inputs_v3.jsonl

Analiza mejoras en ligand properties:
1. Cambios en ligand.type, ligand.charge, ligand.polarity
2. Casos que mejoraron con albumin detection
3. Casos que mejoraron con inference desde type
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def compare_ligands():
    # Cargar ambas versiones
    v2_path = Path(__file__).parent / "../../ins/rdr_inputs_v2.jsonl"
    v3_path = Path(__file__).parent / "../../ins/rdr_inputs_v3.jsonl"
    
    v2_inputs = load_jsonl(v2_path)
    v3_inputs = load_jsonl(v3_path)
    
    # Crear diccionarios por code
    v2_by_code = {entry["context"]["source_code"]: entry for entry in v2_inputs}
    v3_by_code = {entry["context"]["source_code"]: entry for entry in v3_inputs}
    
    print("=" * 80)
    print("COMPARACIÓN v2 → v3: LIGAND PROPERTIES")
    print("=" * 80)
    print(f"\n📊 TOTAL CASOS: {len(v2_inputs)}")
    
    # Distribuciones comparadas
    def get_distributions(inputs):
        types = [e["ligand"]["type"] for e in inputs]
        charges = [e["ligand"]["charge"] for e in inputs]
        polarities = [e["ligand"]["polarity"] for e in inputs]
        return Counter(types), Counter(charges), Counter(polarities)
    
    v2_type, v2_charge, v2_polarity = get_distributions(v2_inputs)
    v3_type, v3_charge, v3_polarity = get_distributions(v3_inputs)
    
    # LIGAND TYPE
    print("\n" + "─" * 80)
    print("1️⃣  LIGAND TYPE")
    print("─" * 80)
    print(f"{'Label':<20} {'v2':<20} {'v3':<20} {'Δ':<10}")
    print("─" * 80)
    
    all_types = sorted(set(v2_type.keys()) | set(v3_type.keys()))
    for t in all_types:
        v2_count = v2_type.get(t, 0)
        v3_count = v3_type.get(t, 0)
        delta = v3_count - v2_count
        v2_pct = 100 * v2_count / len(v2_inputs)
        v3_pct = 100 * v3_count / len(v3_inputs)
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{t:<20} {v2_count:3d} ({v2_pct:5.1f}%)  {v3_count:3d} ({v3_pct:5.1f}%)  {delta_str:>10}")
    
    # LIGAND CHARGE
    print("\n" + "─" * 80)
    print("2️⃣  LIGAND CHARGE")
    print("─" * 80)
    print(f"{'Label':<20} {'v2':<20} {'v3':<20} {'Δ':<10}")
    print("─" * 80)
    
    all_charges = sorted(set(v2_charge.keys()) | set(v3_charge.keys()))
    for c in all_charges:
        v2_count = v2_charge.get(c, 0)
        v3_count = v3_charge.get(c, 0)
        delta = v3_count - v2_count
        v2_pct = 100 * v2_count / len(v2_inputs)
        v3_pct = 100 * v3_count / len(v3_inputs)
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{c:<20} {v2_count:3d} ({v2_pct:5.1f}%)  {v3_count:3d} ({v3_pct:5.1f}%)  {delta_str:>10}")
    
    # LIGAND POLARITY
    print("\n" + "─" * 80)
    print("3️⃣  LIGAND POLARITY")
    print("─" * 80)
    print(f"{'Label':<20} {'v2':<20} {'v3':<20} {'Δ':<10}")
    print("─" * 80)
    
    all_polarities = sorted(set(v2_polarity.keys()) | set(v3_polarity.keys()))
    for p in all_polarities:
        v2_count = v2_polarity.get(p, 0)
        v3_count = v3_polarity.get(p, 0)
        delta = v3_count - v2_count
        v2_pct = 100 * v2_count / len(v2_inputs)
        v3_pct = 100 * v3_count / len(v3_inputs)
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{p:<20} {v2_count:3d} ({v2_pct:5.1f}%)  {v3_count:3d} ({v3_pct:5.1f}%)  {delta_str:>10}")
    
    # Detectar cambios específicos
    print("\n" + "─" * 80)
    print("4️⃣  CASOS QUE CAMBIARON")
    print("─" * 80)
    
    changes = defaultdict(list)
    
    for code in v2_by_code.keys():
        v2_lig = v2_by_code[code]["ligand"]
        v3_lig = v3_by_code[code]["ligand"]
        
        # Cambios en type
        if v2_lig["type"] != v3_lig["type"]:
            changes["type"].append({
                "code": code,
                "display": v2_by_code[code]["context"]["display_name"],
                "v2": v2_lig["type"],
                "v3": v3_lig["type"],
                "v3_prov": v3_lig["type_provenance"]
            })
        
        # Cambios en charge
        if v2_lig["charge"] != v3_lig["charge"]:
            changes["charge"].append({
                "code": code,
                "display": v2_by_code[code]["context"]["display_name"],
                "v2": v2_lig["charge"],
                "v3": v3_lig["charge"],
                "v3_prov": v3_lig["charge_provenance"]
            })
        
        # Cambios en polarity
        if v2_lig["polarity"] != v3_lig["polarity"]:
            changes["polarity"].append({
                "code": code,
                "display": v2_by_code[code]["context"]["display_name"],
                "v2": v2_lig["polarity"],
                "v3": v3_lig["polarity"],
                "v3_prov": v3_lig["polarity_provenance"]
            })
    
    print(f"\n🔹 TYPE changes: {len(changes['type'])}")
    if changes['type']:
        print("\nEjemplos (primeros 10):")
        for i, change in enumerate(changes['type'][:10], 1):
            print(f"  [{i}] {change['code']} | {change['display'][:60]}")
            print(f"      v2: {change['v2']} → v3: {change['v3']} (prov={change['v3_prov']})")
    
    print(f"\n🔹 CHARGE changes: {len(changes['charge'])}")
    if changes['charge']:
        print("\nEjemplos (primeros 10):")
        for i, change in enumerate(changes['charge'][:10], 1):
            print(f"  [{i}] {change['code']} | {change['display'][:60]}")
            print(f"      v2: {change['v2']} → v3: {change['v3']} (prov={change['v3_prov']})")
    
    print(f"\n🔹 POLARITY changes: {len(changes['polarity'])}")
    if changes['polarity']:
        print("\nEjemplos (primeros 10):")
        for i, change in enumerate(changes['polarity'][:10], 1):
            print(f"  [{i}] {change['code']} | {change['display'][:60]}")
            print(f"      v2: {change['v2']} → v3: {change['v3']} (prov={change['v3_prov']})")
    
    # Validar casos objetivo (albumin)
    print("\n" + "─" * 80)
    print("5️⃣  VALIDACIÓN: CASOS ALBUMIN")
    print("─" * 80)
    
    albumin_cases = [
        entry for entry in v3_inputs 
        if entry["ligand"]["type"] == "albumin"
    ]
    
    print(f"Total casos con ligand.type=albumin: {len(albumin_cases)}")
    if albumin_cases:
        print("\nListado:")
        for case in albumin_cases[:10]:
            code = case["context"]["source_code"]
            display = case["context"]["display_name"]
            prev_v2_type = v2_by_code[code]["ligand"]["type"]
            status = "✅ NUEVO" if prev_v2_type == "unknown" else f"📝 Cambió de {prev_v2_type}"
            print(f"  {status} | {code} | {display[:65]}")
    
    # Resumen estadístico
    print("\n" + "=" * 80)
    print("📈 RESUMEN DE MEJORAS")
    print("=" * 80)
    
    print(f"\n🎯 LIGAND TYPE:")
    print(f"  Unknown: {v2_type.get('unknown', 0)} → {v3_type.get('unknown', 0)} ({v3_type.get('unknown', 0) - v2_type.get('unknown', 0):+d})")
    print(f"  Albumin: {v2_type.get('albumin', 0)} → {v3_type.get('albumin', 0)} ({v3_type.get('albumin', 0) - v2_type.get('albumin', 0):+d})")
    
    print(f"\n🎯 LIGAND CHARGE:")
    print(f"  Unknown: {v2_charge.get('unknown', 0)} → {v3_charge.get('unknown', 0)} ({v3_charge.get('unknown', 0) - v2_charge.get('unknown', 0):+d})")
    print(f"  Negative: {v2_charge.get('negative', 0)} → {v3_charge.get('negative', 0)} ({v3_charge.get('negative', 0) - v2_charge.get('negative', 0):+d})")
    print(f"  Neutral: {v2_charge.get('neutral', 0)} → {v3_charge.get('neutral', 0)} ({v3_charge.get('neutral', 0) - v2_charge.get('neutral', 0):+d})")
    
    print(f"\n🎯 LIGAND POLARITY:")
    print(f"  Unknown: {v2_polarity.get('unknown', 0)} → {v3_polarity.get('unknown', 0)} ({v3_polarity.get('unknown', 0) - v2_polarity.get('unknown', 0):+d})")
    print(f"  Hydrophilic: {v2_polarity.get('hydrophilic', 0)} → {v3_polarity.get('hydrophilic', 0)} ({v3_polarity.get('hydrophilic', 0) - v2_polarity.get('hydrophilic', 0):+d})")
    
    print("\n" + "=" * 80)
    print("COMPARACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    compare_ligands()

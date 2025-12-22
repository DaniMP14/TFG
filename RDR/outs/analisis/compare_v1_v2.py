"""
Comparación entre rdr_inputs_v1.jsonl y rdr_inputs_v2.jsonl

Analiza:
1. Cambios en la distribución de nanoparticle.surface_charge
2. Casos que cambiaron de unknown → charged
3. Validación de que las mejoras funcionaron correctamente
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def compare_versions():
    # Cargar ambas versiones
    v1_path = Path(__file__).parent / "../../ins/rdr_inputs_v1.jsonl"
    v2_path = Path(__file__).parent / "../../ins/rdr_inputs_v2.jsonl"
    
    v1_inputs = load_jsonl(v1_path)
    v2_inputs = load_jsonl(v2_path)
    
    # Crear diccionarios por code para comparación
    v1_by_code = {entry["context"]["source_code"]: entry for entry in v1_inputs}
    v2_by_code = {entry["context"]["source_code"]: entry for entry in v2_inputs}
    
    print("=" * 80)
    print("COMPARACIÓN v1 → v2: nanoparticle.surface_charge")
    print("=" * 80)
    
    # Estadísticas básicas
    v1_charges = [entry["nanoparticle"]["surface_charge"] for entry in v1_inputs]
    v2_charges = [entry["nanoparticle"]["surface_charge"] for entry in v2_inputs]
    
    v1_counts = Counter(v1_charges)
    v2_counts = Counter(v2_charges)
    
    print(f"\n📊 TOTAL CASOS: {len(v1_inputs)}")
    
    # Distribución comparada
    print("\n" + "─" * 80)
    print("DISTRIBUCIÓN DE LABELS")
    print("─" * 80)
    print(f"{'Label':<15} {'v1':<15} {'v2':<15} {'Δ':<10}")
    print("─" * 80)
    
    all_labels = sorted(set(v1_counts.keys()) | set(v2_counts.keys()))
    for label in all_labels:
        v1_count = v1_counts.get(label, 0)
        v2_count = v2_counts.get(label, 0)
        delta = v2_count - v1_count
        v1_pct = 100 * v1_count / len(v1_inputs)
        v2_pct = 100 * v2_count / len(v2_inputs)
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        print(f"{label:<15} {v1_count:3d} ({v1_pct:5.1f}%)  {v2_count:3d} ({v2_pct:5.1f}%)  {delta_str:>10}")
    
    # Detectar casos que cambiaron
    print("\n" + "─" * 80)
    print("CASOS QUE CAMBIARON")
    print("─" * 80)
    
    changes = []
    for code in v1_by_code.keys():
        v1_charge = v1_by_code[code]["nanoparticle"]["surface_charge"]
        v2_charge = v2_by_code[code]["nanoparticle"]["surface_charge"]
        
        if v1_charge != v2_charge:
            changes.append({
                "code": code,
                "display": v1_by_code[code]["context"]["display_name"],
                "v1_charge": v1_charge,
                "v1_conf": v1_by_code[code]["nanoparticle"]["surface_charge_confidence"],
                "v1_prov": v1_by_code[code]["nanoparticle"]["surface_charge_provenance"],
                "v2_charge": v2_charge,
                "v2_conf": v2_by_code[code]["nanoparticle"]["surface_charge_confidence"],
                "v2_prov": v2_by_code[code]["nanoparticle"]["surface_charge_provenance"]
            })
    
    print(f"Total de casos modificados: {len(changes)}")
    
    if changes:
        print("\n📋 DETALLE DE CAMBIOS:\n")
        for i, change in enumerate(changes, 1):
            print(f"[{i}] {change['code']} | {change['display'][:70]}")
            print(f"    v1: {change['v1_charge']:<10} (conf={change['v1_conf']:.2f}, prov={change['v1_prov']})")
            print(f"    v2: {change['v2_charge']:<10} (conf={change['v2_conf']:.2f}, prov={change['v2_prov']})")
            print()
    
    # Distribución de provenance en v2
    print("\n" + "─" * 80)
    print("DISTRIBUCIÓN DE PROVENANCE (v2)")
    print("─" * 80)
    
    v2_provs = [entry["nanoparticle"]["surface_charge_provenance"] for entry in v2_inputs]
    prov_counts = Counter(v2_provs)
    
    for prov, count in prov_counts.most_common():
        pct = 100 * count / len(v2_inputs)
        print(f"  {prov:40s}: {count:3d} ({pct:5.1f}%)")
    
    print("\n" + "=" * 80)
    print("COMPARACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    compare_versions()

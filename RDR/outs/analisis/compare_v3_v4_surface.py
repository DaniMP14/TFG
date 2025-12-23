"""
Comparación v3 vs v4: mejoras en surface.charge mediante propagación desde ligand
"""
import json
from pathlib import Path
from collections import Counter
import pandas as pd

# Cargar dataset original
DATASET_PATH = Path("../../../datasets/dataset_FINAL2.csv")
df_original = pd.read_csv(DATASET_PATH, encoding='utf-8')
df_original['Code'] = df_original['Code'].astype(str).str.strip()

# Cargar v3 y v4
V3_PATH = Path("../../ins/rdr_inputs_v3.jsonl")
V4_PATH = Path("../../ins/rdr_inputs_v4.jsonl")

entries_v3 = []
with open(V3_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        entries_v3.append(json.loads(line))

entries_v4 = []
with open(V4_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        entries_v4.append(json.loads(line))

print("="*80)
print("📊 COMPARACIÓN v3 → v4: SURFACE.CHARGE")
print("="*80)

# Distribuciones
v3_dist = Counter(e['surface']['charge'] for e in entries_v3)
v4_dist = Counter(e['surface']['charge'] for e in entries_v4)

print("\n📈 DISTRIBUCIÓN DE SURFACE.CHARGE:")
print(f"\n{'Valor':<15} {'v3':<10} {'v4':<10} {'Δ':<10}")
print("-"*45)
for charge in ['unknown', 'negative', 'neutral', 'positive', 'ambiguous']:
    v3_count = v3_dist.get(charge, 0)
    v4_count = v4_dist.get(charge, 0)
    delta = v4_count - v3_count
    delta_str = f"{delta:+d}" if delta != 0 else "0"
    print(f"{charge:<15} {v3_count:<10} {v4_count:<10} {delta_str:<10}")

total = len(entries_v3)
v3_unknown_pct = (v3_dist['unknown'] / total) * 100
v4_unknown_pct = (v4_dist['unknown'] / total) * 100
print("-"*45)
print(f"{'TOTAL':<15} {total:<10} {total:<10}")
print(f"\n% Unknown:      {v3_unknown_pct:.1f}%      {v4_unknown_pct:.1f}%      {v4_unknown_pct - v3_unknown_pct:+.1f}%")

# Casos modificados
print("\n" + "="*80)
print("🔍 CASOS MODIFICADOS (v3 unknown → v4 con carga)")
print("="*80)

changes = []
for v3_entry, v4_entry in zip(entries_v3, entries_v4):
    code = v3_entry['context']['source_code']
    v3_charge = v3_entry['surface']['charge']
    v4_charge = v4_entry['surface']['charge']
    
    if v3_charge == 'unknown' and v4_charge != 'unknown':
        changes.append({
            'code': code,
            'display': v3_entry['context']['display_name'],
            'v3_charge': v3_charge,
            'v4_charge': v4_charge,
            'v4_conf': v4_entry['surface']['charge_confidence'],
            'v4_prov': v4_entry['surface']['charge_provenance'],
            'ligand_type': v4_entry['ligand']['type'],
            'ligand_charge': v4_entry['ligand']['charge'],
            'surface_material': v4_entry['surface']['material']
        })

print(f"\nTotal casos mejorados: {len(changes)}\n")

# Agrupar por provenance
explicit_changes = [c for c in changes if 'explicit' in c['v4_prov']]
material_changes = [c for c in changes if 'surface_material' in c['v4_prov']]

print(f"🎯 Tier 1 - Funcionalización explícita: {len(explicit_changes)} casos")
print(f"🎯 Tier 2 - Material coincidente: {len(material_changes)} casos")

print("\n" + "-"*80)
print("DETALLE DE CASOS MEJORADOS:")
print("-"*80)

for i, change in enumerate(changes, 1):
    print(f"\n{i}. {change['code']} - {change['display'][:60]}...")
    print(f"   v3 surface.charge: {change['v3_charge']}")
    print(f"   v4 surface.charge: {change['v4_charge']} (conf: {change['v4_conf']:.3f})")
    print(f"   Provenance: {change['v4_prov']}")
    print(f"   Ligand: {change['ligand_type']} (charge: {change['ligand_charge']})")
    print(f"   Surface material: {change['surface_material']}")

# Análisis de provenance en v4
print("\n" + "="*80)
print("📊 DISTRIBUCIÓN DE PROVENANCE EN v4")
print("="*80)

v4_prov_dist = Counter(e['surface']['charge_provenance'] for e in entries_v4)
print("\nTop 10 provenances:")
for prov, count in v4_prov_dist.most_common(10):
    pct = (count / total) * 100
    print(f"  {prov}: {count} ({pct:.1f}%)")

# Análisis de confianza
print("\n" + "="*80)
print("📊 ANÁLISIS DE CONFIANZA")
print("="*80)

v4_charges_with_conf = [
    (e['surface']['charge'], e['surface']['charge_confidence']) 
    for e in entries_v4 
    if e['surface']['charge'] != 'unknown'
]

if v4_charges_with_conf:
    charges_df = pd.DataFrame(v4_charges_with_conf, columns=['charge', 'confidence'])
    print("\nConfianza promedio por carga:")
    print(charges_df.groupby('charge')['confidence'].agg(['mean', 'min', 'max', 'count']))

# Casos nuevos con confianza
new_cases_conf = [(c['v4_charge'], c['v4_conf']) for c in changes]
if new_cases_conf:
    new_df = pd.DataFrame(new_cases_conf, columns=['charge', 'confidence'])
    print("\n\nCasos nuevos (propagados desde ligand):")
    print(new_df.groupby('charge')['confidence'].agg(['mean', 'min', 'max', 'count']))

# Guardar cambios a CSV
changes_df = pd.DataFrame(changes)
changes_df.to_csv('../surface_charge_v3_v4_improvements.csv', index=False, encoding='utf-8')

print("\n" + "="*80)
print("✅ RESUMEN")
print("="*80)
print(f"\n✅ Unknowns reducidos: {v3_dist['unknown']} → {v4_dist['unknown']} (−{v3_dist['unknown'] - v4_dist['unknown']} casos)")
print(f"✅ Mejora porcentual: {v3_unknown_pct:.1f}% → {v4_unknown_pct:.1f}% (−{v3_unknown_pct - v4_unknown_pct:.1f}%)")
print(f"✅ Casos con funcionalización explícita: {len(explicit_changes)}")
print(f"✅ Casos por coincidencia material: {len(material_changes)}")
print(f"\n💾 Guardado: outs/surface_charge_v3_v4_improvements.csv")

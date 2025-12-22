"""
Inspección detallada de casos con ligand.charge conocida pero surface.charge=unknown.
Estos son candidatos para propagar la carga del ligando a la superficie.
"""

import json
import pandas as pd
from pathlib import Path

# Cargar dataset y v3
DATASET_PATH = Path("../datasets/dataset_FINAL2.csv")
df_original = pd.read_csv(DATASET_PATH, encoding='utf-8')
df_original['Code'] = df_original['Code'].astype(str).str.strip()

V3_PATH = Path("ins/rdr_inputs_v3.jsonl")
entries_v3 = []
with open(V3_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        entries_v3.append(json.loads(line))

# Filtrar casos con ligand.charge conocida pero surface.charge=unknown
candidates = [
    e for e in entries_v3
    if e['surface']['charge'] == 'unknown'
    and e['ligand']['charge'] not in ('unknown', None, '')
]

print(f"📊 ANÁLISIS DE {len(candidates)} CASOS CON LIGAND.CHARGE CONOCIDA PERO SURFACE.CHARGE=UNKNOWN\n")
print("="*80)

for i, entry in enumerate(candidates, 1):
    code = entry['context']['source_code']
    display = entry['context']['display_name']
    
    print(f"\n{i}. {code} - {display[:60]}...")
    print(f"   NP type: {entry['nanoparticle']['type']} (charge: {entry['nanoparticle']['surface_charge']})")
    print(f"   Ligand type: {entry['ligand']['type']} (charge: {entry['ligand']['charge']}, conf: {entry['ligand']['charge_confidence']:.2f})")
    print(f"   Surface material: {entry['surface']['material']}")
    print(f"   Surface charge: {entry['surface']['charge']} (prov: {entry['surface']['charge_provenance']})")
    
    # Verificar si hay funcionalización/conjugación
    row = df_original[df_original['Code'] == code]
    if not row.empty:
        definition = str(row.iloc[0].get('Definition', '')).lower()
        
        # Buscar keywords de funcionalización
        functionalization_keywords = [
            'functionalized', 'conjugated', 'coated', 'bound', 'decorated', 
            'modified', 'targeted', 'grafted', 'attached'
        ]
        found_keywords = [kw for kw in functionalization_keywords if kw in definition]
        
        if found_keywords:
            print(f"   🔍 Funcionalización detectada: {', '.join(found_keywords)}")
            print(f"   💡 CANDIDATO para propagar ligand.charge → surface.charge")
        else:
            print(f"   ⚠️ No hay keywords de funcionalización explícitas")
            print(f"   ℹ️ Revisar si el ligando domina la superficie")

print("\n" + "="*80)
print(f"\n✅ ANÁLISIS COMPLETADO - {len(candidates)} casos revisados")

# Resumen por tipo de ligando
from collections import Counter
ligand_types = Counter(e['ligand']['type'] for e in candidates)
ligand_charges = Counter(e['ligand']['charge'] for e in candidates)

print("\n📊 DISTRIBUCIÓN POR TIPO DE LIGANDO:")
for lig_type, count in ligand_types.most_common():
    print(f"   {lig_type}: {count}")

print("\n📊 DISTRIBUCIÓN POR CARGA DE LIGANDO:")
for lig_charge, count in ligand_charges.most_common():
    print(f"   {lig_charge}: {count}")

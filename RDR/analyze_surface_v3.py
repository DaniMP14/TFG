"""
Análisis exhaustivo de surface.material y surface.charge en la v3.
Detecta patrones en unknowns para guiar mejoras potenciales en una v4.
"""

import json
import re
import pandas as pd
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple

# Cargar dataset original para contexto textual
DATASET_PATH = Path("../datasets/dataset_FINAL2.csv")
df_original = pd.read_csv(DATASET_PATH, encoding='utf-8')
df_original['Code'] = df_original['Code'].astype(str).str.strip()

# Cargar v3
V3_PATH = Path("rdr_inputs_v3.jsonl")
entries_v3 = []
with open(V3_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        entries_v3.append(json.loads(line))

print(f"TOTAL CASOS: {len(entries_v3)}\n")

# =========================================================================
# 1️⃣ ANÁLISIS DE SURFACE.MATERIAL
# =========================================================================
print("="*70)
print("📊 ANÁLISIS DE SURFACE.MATERIAL")
print("="*70)

material_dist = Counter(e['surface']['material'] for e in entries_v3)
total = len(entries_v3)

print("\nDISTRIBUCIÓN DE SURFACE.MATERIAL:")
for mat, count in material_dist.most_common():
    pct = (count/total)*100
    print(f"  {mat}: {count} ({pct:.1f}%)")

# Extraer unknowns
unknowns_material = [e for e in entries_v3 if e['surface']['material'] == 'unknown']
print(f"\n🔍 ANALIZANDO {len(unknowns_material)} CASOS CON MATERIAL=UNKNOWN ({len(unknowns_material)/total*100:.1f}%)\n")

# Patrones para detectar materiales de superficie
MATERIAL_PATTERNS = {
    # Coatings metálicos y óxidos
    "gold_coating": [
        r"\bgold[-\s]coated\b", r"\bgold[-\s]shell\b", r"\bau[-\s]coated\b",
        r"\bgold\s+nanoparticle\s+core\b", r"\bcolloidal\s+gold\b"
    ],
    "silica_coating": [
        r"\bsilica[-\s]coated\b", r"\bsilica[-\s]shell\b", r"\bmesoporous\s+silica\b",
        r"\bsio2[-\s]coated\b", r"\bsilica\s+surface\b"
    ],
    "iron_oxide_coating": [
        r"\biron[-\s]oxide[-\s]coated\b", r"\bspio\b", r"\bfe3o4\b", r"\bfe2o3\b",
        r"\bmagnetic[-\s]coated\b", r"\bsuperparamagnetic\b"
    ],
    "titanium_coating": [
        r"\btitanium[-\s]dioxide\b", r"\btio2\b", r"\btitania\b"
    ],
    
    # Polímeros de superficie (no PEG)
    "chitosan": [
        r"\bchitosan[-\s]coated\b", r"\bchitosan\s+surface\b", r"\bchitosan[-\s]modified\b"
    ],
    "dextran": [
        r"\bdextran[-\s]coated\b", r"\bdextran[-\s]stabilized\b", r"\bdextran\s+shell\b"
    ],
    "hyaluronic_acid": [
        r"\bhyaluronic\s+acid[-\s]coated\b", r"\bhyaluronate[-\s]modified\b", r"\bha[-\s]coated\b"
    ],
    "plga_surface": [
        r"\bplga[-\s]based\b", r"\bpoly\(lactic[-\s]co[-\s]glycolic\s+acid\)\b"
    ],
    
    # Lípidos y fosfolípidos
    "phospholipid_bilayer": [
        r"\bphospholipid[-\s]bilayer\b", r"\blipid[-\s]bilayer\b", r"\blipid[-\s]shell\b",
        r"\bliposomal\s+membrane\b", r"\bphospholipid[-\s]coated\b"
    ],
    "cholesterol_surface": [
        r"\bcholesterol[-\s]enriched\b", r"\bcholesterol[-\s]stabilized\b"
    ],
    
    # Proteínas de superficie (además de albumin/antibody ya detectados)
    "protein_corona": [
        r"\bprotein[-\s]corona\b", r"\bprotein[-\s]coated\b", r"\bprotein[-\s]adsorbed\b"
    ],
    "gelatin": [
        r"\bgelatin[-\s]coated\b", r"\bgelatin\s+shell\b"
    ],
    "collagen": [
        r"\bcollagen[-\s]coated\b", r"\bcollagen\s+surface\b"
    ],
    
    # Surfactantes y estabilizadores
    "polysorbate": [
        r"\bpolysorbate\b", r"\btween[-\s]?\d{2}\b", r"\bsurfactant[-\s]coated\b"
    ],
    "poloxamer": [
        r"\bpoloxamer\b", r"\bpluronic\b"
    ],
    
    # Funcionalización química
    "carboxyl_functionalized": [
        r"\bcarboxyl[-\s]functionalized\b", r"\bcarboxylic[-\s]acid[-\s]modified\b",
        r"\bcooh[-\s]terminated\b"
    ],
    "amine_functionalized": [
        r"\bamine[-\s]functionalized\b", r"\bamino[-\s]functionalized\b",
        r"\bnh2[-\s]terminated\b", r"\bamine\s+groups?\b"
    ],
    "thiol_functionalized": [
        r"\bthiol[-\s]functionalized\b", r"\bsulfhydryl[-\s]modified\b",
        r"\bsh[-\s]terminated\b"
    ],
    
    # Membranas celulares (biomimético)
    "cell_membrane": [
        r"\bcell[-\s]membrane[-\s]coated\b", r"\bmembrane[-\s]cloaked\b",
        r"\berythrocyte[-\s]membrane\b", r"\bcancer[-\s]cell[-\s]membrane\b"
    ],
    
    # Otros materiales específicos
    "graphene_oxide": [
        r"\bgraphene[-\s]oxide\b", r"\bgo[-\s]coated\b", r"\breduced\s+graphene\s+oxide\b"
    ],
    "carbon_coating": [
        r"\bcarbon[-\s]coated\b", r"\bcarbon[-\s]shell\b"
    ],
}

def search_patterns(text: str, patterns: List[str]) -> bool:
    """Busca si algún patrón coincide en el texto."""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

# Análisis de patrones en material unknowns
material_pattern_hits = {name: [] for name in MATERIAL_PATTERNS}

for entry in unknowns_material:
    code = entry['context']['source_code']
    
    # Buscar en dataset original
    row = df_original[df_original['Code'] == code]
    if row.empty:
        continue
    
    display = str(row.iloc[0].get('Display Name', '')).lower()
    definition = str(row.iloc[0].get('Definition', '')).lower()
    synonyms = str(row.iloc[0].get('Synonyms', '')).lower()
    combined = f"{display} {definition} {synonyms}"
    
    for pattern_name, patterns in MATERIAL_PATTERNS.items():
        if search_patterns(combined, patterns):
            material_pattern_hits[pattern_name].append(code)

print("PATRONES DETECTADOS EN MATERIAL UNKNOWNS:")
total_hits = 0
for pattern_name, codes in sorted(material_pattern_hits.items(), key=lambda x: len(x[1]), reverse=True):
    if codes:
        count = len(codes)
        pct = (count / len(unknowns_material)) * 100
        print(f"  {pattern_name}: {count} casos ({pct:.1f}%)")
        print(f"    Códigos: {', '.join(codes[:5])}{'...' if len(codes) > 5 else ''}")
        total_hits += count

print(f"\n✅ Total casos con patrones detectados: {total_hits} ({total_hits/len(unknowns_material)*100:.1f}% de unknowns)")
print(f"❌ Casos sin patrones detectados: {len(unknowns_material) - total_hits} ({(len(unknowns_material) - total_hits)/len(unknowns_material)*100:.1f}% de unknowns)")

# =========================================================================
# 2️⃣ ANÁLISIS DE SURFACE.CHARGE
# =========================================================================
print("\n" + "=" * 70)
print("📊 ANÁLISIS DE SURFACE.CHARGE")
print("=" * 70)

charge_dist = Counter(e['surface']['charge'] for e in entries_v3)

print("\nDISTRIBUCIÓN DE SURFACE.CHARGE:")
for charge, count in charge_dist.most_common():
    pct = (count/total)*100
    print(f"  {charge}: {count} ({pct:.1f}%)")

# Analizar provenance de surface.charge
provenance_dist = Counter(e['surface']['charge_provenance'] for e in entries_v3)
print("\nPROVENIENCIA DE SURFACE.CHARGE:")
for prov, count in provenance_dist.most_common():
    pct = (count/total)*100
    print(f"  {prov}: {count} ({pct:.1f}%)")

# Extraer unknowns de charge
unknowns_charge = [e for e in entries_v3 if e['surface']['charge'] == 'unknown']
print(f"\n🔍 ANALIZANDO {len(unknowns_charge)} CASOS CON CHARGE=UNKNOWN ({len(unknowns_charge)/total*100:.1f}%)\n")

# Patrones para carga de superficie
CHARGE_PATTERNS = {
    "positive_keywords": [
        r"\bpositive\s+surface\s+charge\b", r"\bcationic\s+surface\b",
        r"\bpositively[-\s]charged\s+surface\b"
    ],
    "negative_keywords": [
        r"\bnegative\s+surface\s+charge\b", r"\banionic\s+surface\b",
        r"\bnegatively[-\s]charged\s+surface\b"
    ],
    "neutral_keywords": [
        r"\bneutral\s+surface\b", r"\buncharged\s+surface\b", r"\bzwitterionic\s+surface\b"
    ],
    "zeta_potential": [
        r"zeta\s*potential[^.,]{0,30}?([+\-]\d+(?:[.,]\d+)?)\s*m?v\b"
    ],
}

charge_pattern_hits = {name: [] for name in CHARGE_PATTERNS}

for entry in unknowns_charge:
    code = entry['context']['source_code']
    
    row = df_original[df_original['Code'] == code]
    if row.empty:
        continue
    
    display = str(row.iloc[0].get('Display Name', '')).lower()
    definition = str(row.iloc[0].get('Definition', '')).lower()
    synonyms = str(row.iloc[0].get('Synonyms', '')).lower()
    combined = f"{display} {definition} {synonyms}"
    
    for pattern_name, patterns in CHARGE_PATTERNS.items():
        if search_patterns(combined, patterns):
            charge_pattern_hits[pattern_name].append(code)

print("PATRONES DETECTADOS EN CHARGE UNKNOWNS:")
total_charge_hits = 0
for pattern_name, codes in sorted(charge_pattern_hits.items(), key=lambda x: len(x[1]), reverse=True):
    if codes:
        count = len(codes)
        pct = (count / len(unknowns_charge)) * 100
        print(f"  {pattern_name}: {count} casos ({pct:.1f}%)")
        print(f"    Códigos: {', '.join(codes[:5])}{'...' if len(codes) > 5 else ''}")
        total_charge_hits += count

print(f"\n✅ Total casos con patrones detectados: {total_charge_hits} ({total_charge_hits/len(unknowns_charge)*100:.1f}% de unknowns)")
print(f"❌ Casos sin patrones detectados: {len(unknowns_charge) - total_charge_hits} ({(len(unknowns_charge) - total_charge_hits)/len(unknowns_charge)*100:.1f}% de unknowns)")

# =========================================================================
# 3️⃣ ANÁLISIS DE CONSISTENCIA ENTRE CAMPOS
# =========================================================================
print("\n" + "="*70)
print("📊 ANÁLISIS DE CONSISTENCIA ENTRE CAMPOS")
print("="*70)

# ¿Cuántos casos tienen surface.material=unknown pero ligand.type conocido?
ligand_known_surface_unknown = [
    e for e in entries_v3 
    if e['surface']['material'] == 'unknown' 
    and e['ligand']['type'] not in ('unknown', None, '')
]
print(f"\n🔍 Casos con ligand.type conocido pero surface.material=unknown: {len(ligand_known_surface_unknown)}")
if ligand_known_surface_unknown:
    ligand_types = Counter(e['ligand']['type'] for e in ligand_known_surface_unknown)
    print("   Distribución de ligand.type:")
    for lig_type, count in ligand_types.most_common():
        print(f"     {lig_type}: {count}")

# ¿Cuántos casos tienen surface.charge=unknown pero nanoparticle.surface_charge conocida?
np_charge_known_surface_unknown = [
    e for e in entries_v3
    if e['surface']['charge'] == 'unknown'
    and e['nanoparticle']['surface_charge'] not in ('unknown', None, '')
]
print(f"\n🔍 Casos con nanoparticle.surface_charge conocida pero surface.charge=unknown: {len(np_charge_known_surface_unknown)}")

# ¿Cuántos casos tienen surface.charge=unknown pero ligand.charge conocida?
ligand_charge_known_surface_unknown = [
    e for e in entries_v3
    if e['surface']['charge'] == 'unknown'
    and e['ligand']['charge'] not in ('unknown', None, '')
]
print(f"🔍 Casos con ligand.charge conocida pero surface.charge=unknown: {len(ligand_charge_known_surface_unknown)}")
if ligand_charge_known_surface_unknown:
    ligand_charges = Counter(e['ligand']['charge'] for e in ligand_charge_known_surface_unknown)
    print("   Distribución de ligand.charge:")
    for lig_charge, count in ligand_charges.most_common():
        print(f"     {lig_charge}: {count}")

# =========================================================================
# 4️⃣ CASOS ESPECÍFICOS PARA INSPECCIÓN MANUAL
# =========================================================================
print("\n" + "="*70)
print("📋 EJEMPLOS PARA INSPECCIÓN MANUAL")
print("="*70)

# Casos con patrones de material detectados
print("\n🔬 EJEMPLOS CON PATRONES DE MATERIAL DETECTADOS:")
for pattern_name, codes in list(material_pattern_hits.items())[:3]:
    if codes:
        print(f"\n  {pattern_name.upper()}: {codes[0]}")
        row = df_original[df_original['Code'] == codes[0]]
        if not row.empty:
            print(f"    Display: {row.iloc[0].get('Display Name', 'N/A')}")
            definition = str(row.iloc[0].get('Definition', ''))
            if definition and definition != 'nan':
                print(f"    Definition: {definition[:200]}...")

# Guardar resultados detallados
print("\n" + "="*70)
print("💾 GUARDANDO RESULTADOS DETALLADOS...")
print("="*70)

# CSV con casos de material unknown y patrones detectados
material_unknown_data = []
for entry in unknowns_material:
    code = entry['context']['source_code']
    row = df_original[df_original['Code'] == code]
    if row.empty:
        continue
    
    detected_patterns = []
    display = str(row.iloc[0].get('Display Name', '')).lower()
    definition = str(row.iloc[0].get('Definition', '')).lower()
    synonyms = str(row.iloc[0].get('Synonyms', '')).lower()
    combined = f"{display} {definition} {synonyms}"
    
    for pattern_name, patterns in MATERIAL_PATTERNS.items():
        if search_patterns(combined, patterns):
            detected_patterns.append(pattern_name)
    
    material_unknown_data.append({
        'Code': code,
        'Display_Name': row.iloc[0].get('Display Name', ''),
        'NP_Type': entry['nanoparticle']['type'],
        'Ligand_Type': entry['ligand']['type'],
        'Surface_Material': entry['surface']['material'],
        'Detected_Patterns': ', '.join(detected_patterns) if detected_patterns else 'none',
        'Definition': str(row.iloc[0].get('Definition', ''))[:200]
    })

df_material = pd.DataFrame(material_unknown_data)
df_material.to_csv('outs/missed_surface_material_patterns.csv', index=False, encoding='utf-8')
print(f"✅ Guardado: outs/missed_surface_material_patterns.csv ({len(df_material)} casos)")

print("\n" + "="*70)
print("✅ ANÁLISIS COMPLETADO")
print("="*70)

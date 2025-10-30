import json

items = [json.loads(line) for line in open('rdr_inputs_v1.jsonl', encoding='utf-8')]

print("=== DISTRIBUCIÓN DE SURFACE.MATERIAL ===\n")
material_counts = {}
for item in items:
    mat = item['surface']['material']
    material_counts[mat] = material_counts.get(mat, 0) + 1

for mat, count in sorted(material_counts.items(), key=lambda x: -x[1]):
    print(f"{mat:20} : {count:3} casos")

print("\n=== CASOS CON LIGANDO DOMINANDO SUPERFICIE (PEG/ALBUMIN/ANTIBODY) ===\n")
ligand_surface = [i for i in items if i['surface']['material'] in ['peg', 'albumin', 'antibody', 'protein', 'peptide']]
for c in ligand_surface[:10]:
    print(f"{c['context']['source_code']} - {c['context']['display_name']}")
    print(f"  NP type: {c['nanoparticle']['type']}")
    print(f"  Ligand: {c['ligand']['type']}")
    print(f"  Surface material: {c['surface']['material']} (conf={c['surface']['material_confidence']:.2f}, prov={c['surface']['material_provenance']})")
    print()

print("\n=== CASOS CON COATING DETECTADO ===\n")
coating_cases = [i for i in items if 'coating' in i['surface'].get('material_provenance', '')]
for c in coating_cases[:8]:
    print(f"{c['context']['source_code']} - {c['context']['display_name']}")
    print(f"  Surface material: {c['surface']['material']} (conf={c['surface']['material_confidence']:.2f}, prov={c['surface']['material_provenance']})")
    print()

print("\n=== CASOS CON FALLBACK A NP_TYPE ===\n")
fallback_cases = [i for i in items if 'propagated_from_np_type' in i['surface'].get('material_provenance', '')]
print(f"Total casos con fallback: {len(fallback_cases)}")
for c in fallback_cases[:5]:
    print(f"{c['context']['source_code']} - {c['context']['display_name']}")
    print(f"  NP type: {c['nanoparticle']['type']} → Surface material: {c['surface']['material']}")
    print()

import json

items = [json.loads(line) for line in open('../ins/rdr_inputs_v1.jsonl', encoding='utf-8')]

# Casos con PEG
peg_cases = [i for i in items if 'peg' in i['context']['display_name'].lower() or i['ligand']['type'] == 'polymer-peg']
print(f"Casos con PEG detectados: {len(peg_cases)}\n")

print("=== PRIMEROS 5 CASOS CON PEG ===")
for c in peg_cases[:5]:
    print(f"\n{c['context']['source_code']} - {c['context']['display_name']}")
    print(f"  NP charge: {c['nanoparticle']['surface_charge']} (conf={c['nanoparticle']['surface_charge_confidence']:.2f}, prov={c['nanoparticle']['surface_charge_provenance']})")
    print(f"  Surface charge: {c['surface']['charge']} (conf={c['surface']['charge_confidence']:.2f}, prov={c['surface']['charge_provenance']})")
    print(f"  Ligand: {c['ligand']['type']} / {c['ligand']['charge']}")

# Casos con superficies funcionalizadas (functionalized/conjugated/coated/bound/decorated)
func_cases = [i for i in items if any(term in i['context']['display_name'].lower() for term in ['functionalized', 'conjugated', 'coated', 'bound', 'decorated'])]
print(f"\n\n=== CASOS CON SUPERFICIE FUNCIONALIZADA: {len(func_cases)} ===")

for c in func_cases[:8]:
    print(f"\n{c['context']['source_code']} - {c['context']['display_name']}")
    print(f"  NP charge: {c['nanoparticle']['surface_charge']} (conf={c['nanoparticle']['surface_charge_confidence']:.2f})")
    print(f"  Ligand: {c['ligand']['type']} / {c['ligand']['charge']} (conf={c['ligand']['charge_confidence']:.2f})")
    print(f"  Surface charge: {c['surface']['charge']} (conf={c['surface']['charge_confidence']:.2f}, prov={c['surface']['charge_provenance']})")

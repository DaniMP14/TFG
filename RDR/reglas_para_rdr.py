"""
Módulo que contiene las reglas y una función `attach_rules(root)`.

El módulo no debe ejecutar evaluaciones al importarse. La función
`attach_rules` importa la clase `GRDRRule` desde el módulo principal
(importación local dentro de la función para evitar ciclos) y crea las
reglas, las organiza en nodos y las conecta al `root` pasado.
"""

from typing import Any


def attach_rules(root: Any) -> None:
    """Adjunta reglas (nodos y excepciones) al nodo 'root'.

    root -- instancia de GRDRRule creada en implementacion_rdr
    """
    # Import local para evitar import cycles en la carga de módulos
    from implementacion_rdr import GRDRRule

    # Reglas concretas
    rule_electro = GRDRRule(
        name="Electrostatic Binding",
        condition=lambda inp: inp.get("nanoparticle", {}).get("surface_charge") == "positive" and inp.get("ligand", {}).get("charge") == "negative",
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "stable", "rule_confidence": 0.95}
    )

    rule_lipidic = GRDRRule(
        name="Lipid Nanoparticle Exception",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") in ("lipid-based", "liposomal", "lipid"),
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "fluid", "rule_confidence": 0.9}
    )

    rule_lipid_general = GRDRRule(
        name="Lipid General",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") in ("lipid-based", "liposomal", "lipid"),
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "fluid", "rule_confidence": 0.7}
    )

    """ REGLA ANTIGUA
    rule_hydrophobic = GRDRRule(
        name="Hydrophobic Interaction",
        condition=lambda inp: inp.get("ligand", {}).get("polarity") == "nonpolar" and inp.get("nanoparticle", {}).get("type") not in ("lipid-based",),
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "disordered", "rule_confidence": 0.85}
    )
    """

    rule_hydrophobic = GRDRRule(
        name="Hydrophobic Adsorption",
        condition=lambda inp: inp.get("ligand", {}).get("polarity") == "nonpolar" and inp.get("nanoparticle", {}).get("type") in ("metallic", "polymeric"),
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "disordered", "rule_confidence": 0.75}
    )

    rule_hydrophilic = GRDRRule(
        name="Hydrophilic Repulsion",
        condition=lambda inp: inp.get("ligand", {}).get("polarity") == "polar" and inp.get("nanoparticle", {}).get("surface_charge") == "negative",
        action=lambda inp: {"predicted_affinity": "low", "monolayer_order": "unstable", "rule_confidence": 0.8}
    )

    rule_polymeric = GRDRRule(
        name="Polymeric Encapsulation",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") == "polymeric",
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "stable", "rule_confidence": 0.9}
    )

    rule_metallic = GRDRRule(
        name="Metallic Surface Adsorption",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") in ("metallic", "metallic-gold"),
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "ordered", "rule_confidence": 0.9}
    )

    rule_pegylated = GRDRRule(
        name="PEGylated Neutralization",
        condition=lambda inp: "peg" in inp.get("context", {}).get("display_name", "").lower(),
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "semi-ordered", "rule_confidence": 0.85}
    )

    rule_rna_binding = GRDRRule(
        name="RNA-based Ligand Rule",
        condition=lambda inp: inp.get("biomolecule", {}).get("type") == "RNA" and inp.get("nanoparticle", {}).get("surface_charge") == "positive",
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "semi-ordered", "rule_confidence": 0.92}
    )

    rule_spio = GRDRRule(
        name="SPIO Protein Corona Adsorption",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") == "metallic" and "spio" in inp.get("context", {}).get("display_name", "").lower(),
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "ordered", "rule_confidence": 0.95}
    )

    rule_liposomal_rna = GRDRRule(
        name="Liposomal RNA Complexation",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") in ("lipid-based", "liposomal") and inp.get("biomolecule", {}).get("type") == "RNA",
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "stable", "rule_confidence": 0.9}
    )

    rule_polymeric_peg = GRDRRule(
        name="PEGylated Polymeric Stabilization",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type") == "polymeric" and inp.get("surface", {}).get("material") == "peg",
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "ordered", "rule_confidence": 0.85}
    )

    rule_antibody_targeting = GRDRRule(
        name="Antibody-Mediated Targeting",
        condition=lambda inp: inp.get("ligand", {}).get("type") == "antibody",
        action=lambda inp: {"predicted_affinity": "high", "monolayer_order": "ordered", "rule_confidence": 0.9}
    )


    # Nodos intermedios

    rule_material = GRDRRule(
        name="Material Node",
        condition=lambda inp: inp.get("nanoparticle", {}).get("type", "unknown") != "unknown",
        action=lambda inp: {"predicted_affinity": "low", "monolayer_order": "none", "rule_confidence": 0.3}
    )
    rule_material.add_exception(rule_spio) # refina metallic
    rule_material.add_exception(rule_metallic)
    rule_material.add_exception(rule_polymeric)
    rule_material.add_exception(rule_lipid_general)


    rule_ligand_props = GRDRRule(
        name="Ligand Property Node",
        condition=lambda inp: inp.get("ligand", {}).get("type", "unknown") != "unknown",
        action=lambda inp: {"predicted_affinity": ("moderate" if inp.get("ligand", {}).get("polarity") == "polar" else "low"),
            "monolayer_order": ("ordered" if inp.get("ligand", {}).get("polarity") == "polar" else "fluid"),
            "rule_confidence": 0.4}
    )
    rule_ligand_props.add_exception(rule_hydrophobic)
    rule_ligand_props.add_exception(rule_hydrophilic)
    rule_ligand_props.add_exception(rule_antibody_targeting)


    rule_biomolecule = GRDRRule(
        name="Biomolecule Node",
        condition=lambda inp: inp.get("biomolecule", {}).get("type", "unknown") != "unknown",
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "ordered", "rule_confidence": 0.5}
    )
    rule_biomolecule.add_exception(rule_rna_binding)
    rule_biomolecule.add_exception(rule_liposomal_rna)


    rule_surface = GRDRRule(
        name="Surface Feature Node",
        condition=lambda inp: inp.get("surface", {}).get("material", "unknown") not in ["unknown", None],
        action=lambda inp: {"predicted_affinity": ("low" if inp["surface"]["material"] == "peg" else "moderate"), "monolayer_order": "fluid", "rule_confidence": 0.45}
    )
    rule_surface.add_exception(rule_pegylated)
    rule_surface.add_exception(rule_polymeric_peg)


    rule_charge = GRDRRule(name="Charge Interaction Node",
        condition=lambda inp: inp.get("nanoparticle", {}).get("surface_charge", "unknown") not in ["unknown", None] or
            inp.get("surface", {}).get("charge", "unknown") not in ["unknown", None],
        action=lambda inp: {"predicted_affinity": "moderate", "monolayer_order": "partial", "rule_confidence": 0.4}
    )
    rule_charge.add_exception(rule_electro)
    rule_charge.add_exception(rule_lipidic)



    # Conectar nodos al root
    root.add_exception(rule_biomolecule)   # 1. especificidad biológica
    root.add_exception(rule_material)      # 2. estructura dominante
    root.add_exception(rule_charge)        # 3. modulador electrostático
    root.add_exception(rule_surface)       # 4. PEG, coatings
    root.add_exception(rule_ligand_props)  # 5. propiedades finas


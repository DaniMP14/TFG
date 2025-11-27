"""
Extractor semántico estructurado para el motor RDR.
Convierte filas del Tesauro NCIt ya filtrado (dataset_FINAL2.csv) en la estructura de entrada esperada por `implementacion_rdr.py`.

Características:
- Normalización robusta y trazabilidad por campo (valor, confianza, procedencia).
- Heurísticas biomédicas ampliadas (nanopartículas, ligandos, biomoléculas, entorno).
- Estandarización de vocabulario para interoperabilidad.
- Salida reproducible para hacer inferencias.

Uso:
    from extract_input import load_and_convert
    inputs = load_and_convert("../datasets/dataset_FINAL2.csv")
"""

from typing import Dict, Any, Tuple, List
import re
import json
import pandas as pd


# ──────────────────────────────────────────────────────────────
# 🔹 UTILIDADES BÁSICAS
# ──────────────────────────────────────────────────────────────
def _norm(text: Any) -> str:
    if pd.isna(text) or text is None:
        return ""
    return str(text).strip()


def _combine(*parts: str) -> str:
    return " ".join([p.lower() for p in parts if p])


# ──────────────────────────────────────────────────────────────
# 🔹 INFERENCIA SEMÁNTICA
# ──────────────────────────────────────────────────────────────
LIPID_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "liposomal", "liposome", "nanoliposome", "solid lipid nanoparticle", "slp",
            "lipid nanoparticle", "lnp", "cationic lipid", "pegylated liposome", "peg-liposome",
            "stealth liposome", "lipid-based nanocarrier", "lipid-based nanoparticle", "lipid core", "ceramide nanoliposome"
        ],
        "confidence": 0.95,
        "provenance": "keywords",
    },
    "medium_conf": {
        "terms": [
            "phospholipid", "cholesterol nanoparticle", "lipid vesicle", "lipid bilayer", "lipid emulsion",
            "nanovesicle", "micellar lipid", "lipid droplet", "lipid matrix"
        ],
        "confidence": 0.85,
        "provenance": "contextual",
    },
    "low_conf": {
        "terms": [
            "amphiphilic molecule", "lipophilic core", "fatty acid-based", "triglyceride nanoparticle",
            "lipid-like", "surfactant-based",
            # cholesteryl-based particles (CHP vaccines)
            "chp", "cholesteryl", "cholesteryl-based"
        ],
        "confidence": 0.7,
        "provenance": "indirect"
    },
}

METALLIC_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "gold nanoparticle", "au nanoparticle", "silver nanoparticle", "iron oxide nanoparticle", 
            "magnetic nanoparticle", "metal nanoparticle", "platinum nanoparticle", "palladium nanoparticle", 
            "metallic nanoparticle", "titanium dioxide", "platinum acetylacetonate",
            # superparamagnetic iron oxide
            "spio nanoparticle", "spio", "superparamagnetic iron oxide",
            # contrast agents
            "gadolinium", "gadolinium-chelate"
        ],
        "confidence": 0.9,
        "provenance": "keywords"
    },
    "medium_conf": {
        "terms": [
            "au ", "au-", "fe3o4", "fe2o3", "ag ", "cu nanoparticle",
            "metallic core", "core-shell metallic", "superparamagnetic"
        ],
        "confidence": 0.85,
        "provenance": "contextual"
    },
    "low_conf": {
        "terms": [
            "metal-based", "inorganic core", "conductive nanoparticle", "plasmonic", "metal cluster"
        ],
        "confidence": 0.75,
        "provenance": "indirect"
    }
}

SILICA_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "silica nanoparticle", "silicon dioxide", "sio2", "mesoporous silica", "mcm-41", "sba-15",
            # inorganic matrix and sol-gel formulations (very often silica-based)
            "polysiloxane", "sol-gel", "inorganic matrix"
        ],
        "confidence": 0.9,
        "provenance": "keywords"
    },
    "medium_conf": {
        "terms": [
            "silicate", "silicon-based nanoparticle", "silica-coated", "amorphous silica", "silica shell",
            # polysaccharide-based (can be silica-adjacent or polymer-adjacent)
            "polyglucose nanoparticle", "dextran nanoparticle"
        ],
        "confidence": 0.85,
        "provenance": "contextual"
    },
    "low_conf": {
        "terms": [
            "glass-like", "silicon nanostructure", "oxides of silicon"
        ],
        "confidence": 0.7,
        "provenance": "indirect"
    }
}

POLYMERIC_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "polymeric nanoparticle", "polymer nanoparticle", "micelle", "polymeric micelle", "plga",
            "pla", "pegylated", "peg-lipid", "peg", "pegylated nanoparticle",
            # added to catch entries like 'nanocapsule', 'nanocarrier', 'nanocontainer', 'nanobubble'
            "nanocapsule", "nanocapsules", "nanocarrier", "nanocarriers",
            "nanocontainer", "nanocontainers", "nanobubble", "nanoemulsion",
            # albumin-bound and protein-based nanoparticles
            "albumin-bound", "nab-", "albumin-stabilized", "protein nanoparticle",
            # polymer-encapsulated formulations
            "polymer encapsulated", "polymer-based formulation", "branched polymer", "polyethyloxazoline", "peox"
        ],
        "confidence": 0.9,
        "provenance": "keywords"
    },
    "medium_conf": {
        "terms": [
            "poly(lactic-co-glycolic acid)", "polyethylene glycol", 
            "block copolymer", "polymer matrix", "polymer-based carrier",
            # formulation-based indicators (often polymeric or lipid hybrid)
            "nanoparticle-based formulation", "nanoparticle-encapsulated",
            "nanopharmaceutical", "nanoparticle-based suspension",
            "nano-sized formulation", "nanoformulation",
            # suspension and emulsion forms
            "emulsion", "suspension", "oil-in-water emulsion"
        ],
        "confidence": 0.85,
        "provenance": "contextual"
    },
    "low_conf": {
        "terms": [
            "biodegradable polymer", "synthetic polymer", "polymer shell", "polymer coating",
            # protein-based and peptide-based nanoparticles
            "polypeptide nanoparticle", "pnp", "ferritin-based",
            "phage-based", "bacteriophage", "virus-like particle"
        ],
        "confidence": 0.75,
        "provenance": "indirect"
    }
}

CARBON_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "carbon nanoparticle", "carbon nanotube", "cnt", "carbon nanotubes",
            "graphene", "graphene oxide", "fullerene", "c60", "carbon quantum dot", "carbon dot"
        ],
        "confidence": 0.9,
        "provenance": "keywords"
    },
    "medium_conf": {
        "terms": [
            "nanotube", "carbon shell", "carbon-based nanomaterial", "carbon nanosphere", "carbon black", "carbon nanostructure"
        ],
        "confidence": 0.85,
        "provenance": "contextual"
    },
    "low_conf": {
        "terms": [
            "carbonaceous", "aromatic core", "sp2 hybridized", "carbon scaffold"
        ],
        "confidence": 0.75,
        "provenance": "indirect"
    }
}

SEMICONDUCTOR_NP_KEYWORDS = {
    "high_conf": {
        "terms": [
            "quantum dot", "qd", "cadmium selenide", "cdse", "zinc sulfide", "zns", "semiconductor nanoparticle"
        ],
        "confidence": 0.9,
        "provenance": "keywords"
    },
    "medium_conf": {
        "terms": [
            "core-shell quantum dot", "fluorescent nanoparticle", "photoluminescent nanocrystal", "quantum emitter"
        ],
        "confidence": 0.85,
        "provenance": "contextual"
    },
    "low_conf": {
        "terms": [
            "inorganic nanocrystal", "nanosphere quantum", "quantum nanomaterial"
        ],
        "confidence": 0.7,
        "provenance": "indirect"
    }
}

# patrón genérico para detectar menciones explícitas de 'nanoparticle' en campos
_NP_GENERIC_RE = re.compile(r"\b(nanoparticle|nanoparticles|nanoparticle-encapsulated|nanopharm|nanopharmaceutical|nab-|albumin-bound|nanocell|c dots|c-dots|c dots)\b", re.IGNORECASE)


def infer_np_type(display_name: str, synonyms: str, definition: str) -> Tuple[str, float, str]:
    # Normalizar y mantener campos por separado para boosting (mejora de confianza si aparece en varios campos)
    s_display = (display_name or "").lower()
    s_syn = (synonyms or "").lower()
    s_def = (definition or "").lower()

    def _match_term(term: str, text: str) -> bool:
        """Matching flexible con variantes comunes:
        - Permite separadores guion/espacio entre tokens (p.ej. nano-emulsion vs nano emulsion vs nanoemulsion cuando viene separado en términos compuestos)
        - Soporta plural opcional en el último token (s|es, y->ies)
        - Mantiene \b límites para no sobre-matchear dentro de palabras largas
        """
        t = (term or "").strip()
        if not t:
            return False
        # Separar por espacios/guiones para permitir variantes de separador
        tokens = re.split(r"[\s\-]+", t)
        parts = []
        for i, tok in enumerate(tokens):
            esc = re.escape(tok)
            # Plural opcional sólo en el último token y si es alfabético puro
            if i == len(tokens) - 1 and re.match(r"^[A-Za-z]+$", tok):
                if tok.endswith("y") and len(tok) > 2:
                    # party -> (party|parties)
                    esc = re.escape(tok[:-1]) + r"(?:y|ies)"
                else:
                    # generic plural opcional
                    esc = esc + r"(?:s|es)?"
            parts.append(esc)
        sep = r"[\s\-]*"
        pattern = r"\b" + sep.join(parts) + r"\b"
        try:
            return re.search(pattern, text, flags=re.IGNORECASE) is not None
        except re.error:
            # alternativa sencilla si la expresión regular falla
            return t.lower() in text.lower()

    # iterar por categorías y niveles (prioridad high -> medium -> low)
    for cat_name, cat_dict, label in [
        ("lipid-based", LIPID_NP_KEYWORDS, "lipid-based"),
        ("metallic", METALLIC_NP_KEYWORDS, "metallic"),
        ("silica", SILICA_NP_KEYWORDS, "silica"),
        ("polymeric", POLYMERIC_NP_KEYWORDS, "polymeric"),
        ("carbon-based", CARBON_NP_KEYWORDS, "carbon-based"),
        ("semiconductor", SEMICONDUCTOR_NP_KEYWORDS, "semiconductor"),
    ]:
        for level in ["high_conf", "medium_conf", "low_conf"]:
            base_conf = cat_dict[level]["confidence"]
            prov = cat_dict[level]["provenance"]
            for term in cat_dict[level]["terms"]:
                # contar coincidencias en campos separados para boosting
                matches = 0
                if _match_term(term, s_display):
                    matches += 1
                if _match_term(term, s_syn):
                    matches += 1
                if _match_term(term, s_def):
                    matches += 1

                if matches:
                    # aplicar pequeño boost si aparece en varias secciones
                    conf = min(base_conf + 0.05 * (matches - 1), 0.99)
                    # enriquecer provenance con fuentes donde apareció
                    sources = []
                    if _match_term(term, s_display):
                        sources.append("display")
                    if _match_term(term, s_syn):
                        sources.append("synonyms")
                    if _match_term(term, s_def):
                        sources.append("definition")
                    prov_ext = prov + ":" + ",".join(sources) if sources else prov
                    return label, conf, prov_ext

    # Fallback: si aparece la palabra 'nanoparticle' en cualquiera de los campos,
    # marcar como 'nanoparticle' (genérico) para no perder detección.
    combined = _combine(display_name, synonyms, definition)
    if _NP_GENERIC_RE.search(combined):
        return "nanoparticle", 0.6, "heuristic:contains_nanoparticle"

    return "unknown", 0.0, "none"



# Precompilados y patrones para inferencia de carga
# Regex refinado para zeta potential (evita falsos positivos con códigos de producto) - NO APARECE EN EL TESAURO DE NCIt
_ZETA_RE = re.compile(r"zeta\s*potential[^.,]{0,30}?([+\-]\d+(?:[.,]\d+)?)\s*m?v\b", flags=re.IGNORECASE)
_HIGH_POS_RE = re.compile(r"\b(cationic|positively\s*charged|positive\s*charge|\+\s?charge)\b", flags=re.IGNORECASE)
_HIGH_NEG_RE = re.compile(r"\b(anionic|negatively\s*charged|negative\s*charge|\-\s?charge)\b", flags=re.IGNORECASE)

# Lípidos catiónicos (alta confianza para carga positiva) - Versión 2
_CATIONIC_LIPID_RE = re.compile(
    r"\b(dotap|dotma|dope|dodap|ddab|dc-chol|cationic\s*lipid|lipofectamine)\b",
    flags=re.IGNORECASE
)

# Funcionalización con grupos amino (indicador de carga positiva)
# Nota: evita "amino acid" que es secuencia peptídica, no grupo funcional cargado - Versión 2
_AMINE_FUNCTIONALIZED_RE = re.compile(
    r"\b(amine[-\s]functionalized|amine\s*groups?|(?<!amino\s)amino[-\s]functionalized)\b",
    flags=re.IGNORECASE
)

_POS_CHEM_TERMS = [
    "amine-functionalized", "polyethylenimine", "chitosan", "cationic lipid", "quaternary ammonium",
    "polylysine", "branched peimine"
]
_NEG_CHEM_TERMS = [
    "carboxylate", "carboxylic acid", "sulfate", "sulfonate", "phosphate", "anionic polymer", "alginate"
]
_POS_CHEM_PATTERNS = [re.compile(r"\b" + re.escape(t) + r"\b", flags=re.IGNORECASE) for t in _POS_CHEM_TERMS]
_NEG_CHEM_PATTERNS = [re.compile(r"\b" + re.escape(t) + r"\b", flags=re.IGNORECASE) for t in _NEG_CHEM_TERMS]

# Precompilados y patrones para ligandos y biomoléculas
_ANTIBODY_RE = re.compile(r"\b(antibody|immunoconjugate|immunoglobulin|mab|igg|igm|scfv|fab|fc|nanobody|vhh)\b", re.IGNORECASE)
_PEPTIDE_RE = re.compile(r"\b(peptide|peptid|oligopeptide|rgd|cell-penetrating peptide)\b", re.IGNORECASE)
_APTAMER_RE = re.compile(r"\b(aptamer)\b", re.IGNORECASE)
_FOLATE_RE = re.compile(r"\b(folate|folic acid)\b", re.IGNORECASE)
# mejora versión 3: incluir variantes de albumina
_ALBUMIN_RE = re.compile(r"\b(albumin[-\s]bound|nab[-\s]|albumin[-\s]stabilized|albumin[-\s]coated|human\s+serum\s+albumin|hsa)\b", re.IGNORECASE)
_PEG_RE = re.compile(r"\b(peg|pegylat|pegylated|polyethylene glycol)\b", re.IGNORECASE)
_TARGET_RE = re.compile(r"\b(target(ed)?|affinity|receptor-binding|moiety)\b", re.IGNORECASE)

# polarity
_HYDROPHOBIC_RE = re.compile(r"\b(hydrophobic ligand|lipophilic|nonpolar)\b", re.IGNORECASE)
_HYDROPHILIC_RE = re.compile(r"\b(hydrophilic|polar ligand)\b", re.IGNORECASE)

# ligand charge
_LIGAND_CATIONIC_RE = re.compile(r"\b(cationic|positively charged|\+ charge|cationic lipid|chitosan|polyethylenimine)\b", re.IGNORECASE)
_LIGAND_ANIONIC_RE = re.compile(r"\b(anionic|negatively charged|\- charge|carboxylate|sulfate|sulfonate|phosphate)\b", re.IGNORECASE)
_LIGAND_ZWITTERIONIC_RE = re.compile(r"\b(zwitterionic)\b", re.IGNORECASE)

# patrones de biomoléculas
_DNA_RE = re.compile(r"\b(dna|plasmid|oligonucleotide|oligo)\b", re.IGNORECASE)
_RNA_RE = re.compile(r"\b(rna|mrna|sirna|mirna|trna|rrna|microrna)\b", re.IGNORECASE)
_PROTEIN_RE = re.compile(r"\b(protein|peptide|enzyme|antibody|immunoglobulin|mab|cytokine)\b", re.IGNORECASE)
_POLYSACCHARIDE_RE = re.compile(r"\b(polysaccharide|hyaluronic acid|hyaluronate|dextran|heparin|chitosan)\b", re.IGNORECASE)
_MEMBRANE_RE = re.compile(r"\b(cell membrane|lipid bilayer|phospholipid|liposome|lipid raft)\b", re.IGNORECASE)
_RECEPTOR_RE = re.compile(r"\b(receptor|antigen|marker|egfr|her2|cd\d{2,3})\b", re.IGNORECASE)
_GENE_RE = re.compile(r"\b(gene|oncogene|tumor suppressor|transcription factor|mrna expression)\b", re.IGNORECASE)



def infer_charge(display_name: str, definition: str, concept_subset: str) -> Tuple[str, float, str]:
    s = _combine(display_name, definition, concept_subset)

    # 1) Parametric evidence: zeta potential (decimals, commas, units)
    # Nota: regex refinado para evitar falsos positivos con códigos de producto (Versión 2) - NO SIRVE PARA DATASET DE NCIt PORQUE NO TIENE INFO DE ZETA
    m = _ZETA_RE.search(s)
    zeta_result = None
    if m:
        zeta_str = m.group(1).replace(",", ".")
        try:
            zeta_val = float(zeta_str)
            abs_z = abs(zeta_val)
            if abs_z >= 30:
                zeta_conf = 0.95
            elif abs_z >= 15:
                zeta_conf = 0.9
            elif abs_z >= 5:
                zeta_conf = 0.8
            else:
                zeta_conf = 0.7
            zeta_sign = "positive" if zeta_val > 0 else ("negative" if zeta_val < 0 else "neutral")
            zeta_result = (zeta_sign, zeta_conf, f"parametric:zeta")
        except ValueError:
            zeta_result = None

    # 2) Señales directas en el texto
    text_pos = bool(_HIGH_POS_RE.search(s))
    text_neg = bool(_HIGH_NEG_RE.search(s))

    # 3) Lípidos catiónicos (confianza alta para carga positiva)
    cationic_lipid = bool(_CATIONIC_LIPID_RE.search(s))
    
    # 4) Superficie funcionalizada con aminas (confianza media-alta para carga positiva)
    amine_functionalized = bool(_AMINE_FUNCTIONALIZED_RE.search(s))

    # 5) Señales inferidas por grupos químicos (confianza media)
    chem_pos = any(p.search(s) for p in _POS_CHEM_PATTERNS)
    chem_neg = any(p.search(s) for p in _NEG_CHEM_PATTERNS)

    # 6) Señales de confianza baja para neutralidad
    low_neutral = any(re.search(r"\b" + re.escape(k) + r"\b", s) for k in ["zwitterionic", "neutral", "uncharged"])

    # 7) Señal neutral específica de PEG (confianza media-alta)
    peg_detected = _PEG_RE.search(s)

    # Resolver conflictos y combinar evidencias
    evidences = []
    if text_pos:
        evidences.append(("positive", 0.95, "keywords"))
    if text_neg:
        evidences.append(("negative", 0.95, "keywords"))
    if cationic_lipid:
        evidences.append(("positive", 0.90, "keywords:cationic_lipid"))
    if amine_functionalized:
        evidences.append(("positive", 0.85, "inferred:amine_functionalized"))
    if chem_pos:
        evidences.append(("positive", 0.85, "inferred:chemical_group"))
    if chem_neg:
        evidences.append(("negative", 0.85, "inferred:chemical_group"))
    if peg_detected:
        # PEG → neutral con confianza media-alta (0.85)
        evidences.append(("neutral", 0.85, "keywords:peg"))
    if low_neutral:
        evidences.append(("neutral", 0.75, "keywords"))
    if zeta_result:
        evidences.append(zeta_result)

    # Resolver conflictos con neutral vs cargado: preferir evidencia cargada
    # Si hay una señal cargada de alta confianza (>= 0.9). Trata casos como "positive PEGylated micelles..." 
    # donde una señal neutral (peg) aparece junto con una señal cargada fuerte.
    signs = set(e[0] for e in evidences)
    if "neutral" in signs and ("positive" in signs or "negative" in signs):
        high = [e for e in evidences if e[1] >= 0.9]
        if high:
            # devolver la evidencia cargada de mayor confianza
            best = max(high, key=lambda x: x[1])
            return best

    # Si hay evidencias conflictivas, marcar como ambigua
    if "positive" in signs and "negative" in signs:
        provs = ",".join(sorted({e[2] for e in evidences}))
        return "ambiguous", 0.0, f"conflict:{provs}"

    # Si existe alguna evidencia y no es ambigua, escoger la de mayor confianza y aumentar si hay concordancia
    if evidences:
        # elegir evidencia con mayor confianza
        best = max(evidences, key=lambda x: x[1])
        label, base_conf, prov = best
        # boostear si textual+parametric coinciden
        if zeta_result and label == zeta_result[0] and base_conf < 0.99:
            base_conf = min(0.99, base_conf + 0.05)
            prov = prov + ",parametric:zeta"
        return label, base_conf, prov

    # alternativa por defecto
    return "unknown", 0.0, "none"

# ──────────────────────────────────────────────────────────────
# 🔹 INFERENCIA DE SUSTRATO/ENTORNO (para surface.charge independiente)
# ──────────────────────────────────────────────────────────────
_SUBSTRATE_GLASS_RE = re.compile(r"\b(glass|silicon|silica substrate|quartz|sio2 surface)\b", re.IGNORECASE)
_SUBSTRATE_PLASTIC_RE = re.compile(r"\b(plastic|polystyrene|petri dish|cell culture plate)\b", re.IGNORECASE)
_SUBSTRATE_MEMBRANE_RE = re.compile(r"\b(cell membrane|lipid bilayer|tissue|extracellular matrix|ecm|in vivo|in vitro surface)\b", re.IGNORECASE)
_SUBSTRATE_METAL_RE = re.compile(r"\b(gold surface|au substrate|metal substrate|electrode)\b", re.IGNORECASE)

def infer_substrate_charge(display_name: str, synonyms: str, definition: str) -> Tuple[str, float, str]:
    """Infiere carga de la superficie del sustrato/entorno donde interactúa la NP.
    Retorna (charge, confidence, provenance) o None si no hay contexto de sustrato."""
    s = _combine(display_name, synonyms, definition)
    
    # Detectar tipo de sustrato
    if _SUBSTRATE_GLASS_RE.search(s):
        # vidrio/sílice → carga negativa (grupos silanol)
        return "negative", 0.85, "inferred:glass_substrate"
    elif _SUBSTRATE_PLASTIC_RE.search(s):
        # plástico/poliestireno → generalmente neutral o ligeramente negativo
        return "neutral", 0.7, "inferred:plastic_substrate"
    elif _SUBSTRATE_MEMBRANE_RE.search(s):
        # membrana celular → contextual, pero típicamente negativa (fosfolípidos, glicocalix)
        if re.search(r"\b(negatively charged|anionic membrane)\b", s, re.IGNORECASE):
            return "negative", 0.9, "keywords:cell_membrane"
        elif re.search(r"\b(positively charged|cationic membrane)\b", s, re.IGNORECASE):
            return "positive", 0.9, "keywords:cell_membrane"
        else:
            # fallback: membrana típicamente negativa por fosfolípidos
            return "negative", 0.75, "inferred:cell_membrane"
    elif _SUBSTRATE_METAL_RE.search(s):
        # metal (oro, electrodos) → depende del potencial aplicado, marcar desconocido
        return "unknown", 0.0, "context:metal_substrate"
    
    # No hay contexto explícito de sustrato, None porque lo propagamos de np.surface.charge
    return None


def infer_surface_charge(
    display_name: str,
    synonyms: str,
    definition: str,
    np_charge: str,
    np_charge_conf: float,
    np_charge_src: str,
    ligand_info: Dict[str, Any],
    surf_material: str
) -> Tuple[str, float, str]:
    """Encapsula la lógica de decisión de la carga de la superficie.

    Prioridad:
    1) Si hay contexto de sustrato explícito -> usar infer_substrate_charge
    2) Si no hay sustrato pero la nanopartícula tiene carga conocida -> propagar desde nanoparticle.surface_charge
    3) Si la entrada indica 'functionalized/conjugated/coated/bound/decorated/grafted/targeted' y el ligando tiene carga con confianza suficiente -> propagar desde ligand (alta confianza 0.95x)
    4) Si surface.material coincide con ligand.type y ligando tiene carga confiable -> propagar desde ligand (confianza media 0.85x)
    5) Fallback -> unknown
    """
    # 1) contexto de sustrato
    substrate_result = infer_substrate_charge(display_name, synonyms, definition)
    if substrate_result:
        return substrate_result

    # 2) propagar desde nanoparticle si existe
    if np_charge and np_charge != "unknown":
        return np_charge, np_charge_conf, f"propagated_from_nanoparticle:{np_charge_src}"

    # 3) propagar desde ligando cuando hay funcionalización explícita (alta confianza) - VERSIÓN 4
    s_combined = _combine(display_name, synonyms, definition)
    if ligand_info.get("charge") not in (None, "", "unknown") \
       and ligand_info.get("charge_confidence", 0.0) >= 0.60:
        
        # Tier 1: funcionalización explícita (descuento 0.95x)
        if re.search(r"\b(functionalized|conjugated|coated|bound|decorated|grafted|targeted|modified)\b", s_combined, re.IGNORECASE):
            propagated_conf = ligand_info.get("charge_confidence", 0.0) * 0.95
            return (
                ligand_info["charge"], 
                propagated_conf,
                f"propagated_from_ligand:{ligand_info.get('type','unknown')}:explicit"
            )
        
        # Tier 2: material coincide con tipo de ligando (descuento 0.85x)
        # Casos: albumin-albumin, antibody-antibody, peg-polymer-peg
        if (
            (surf_material == "albumin" and ligand_info.get("type") == "albumin")
            or (surf_material == "antibody" and ligand_info.get("type") == "antibody")
            or (surf_material == "peg" and ligand_info.get("type") == "polymer-peg")
        ):
            propagated_conf = ligand_info.get("charge_confidence", 0.0) * 0.85
            return (
                ligand_info["charge"],
                propagated_conf,
                f"inferred_from_surface_material:{ligand_info.get('type','unknown')}"
            )

    # 5) fallback final: unknown (mantener provenance similar al anterior comportamiento)
    return "unknown", 0.0, "propagated_from_nanoparticle:none"


# TODO: consistencia carga ligando <-> carga superficie - PARA VERSIÓN 5? Junto con el fallback de targeting (es muy vago)
def infer_ligand_properties(display_name: str, synonyms: str, definition: str) -> Dict[str, Any]:
    s = _combine(display_name, synonyms, definition)
    type = {"type": "unknown", "type_confidence": 0.0, "type_provenance": "none"}
    polarity = {"polarity": "unknown", "polarity_confidence": 0.0, "polarity_provenance": "none"}
    charge = {"charge": "unknown", "charge_confidence": 0.0, "charge_provenance": "none"}

    # Tipos comunes de ligando en nanoterapia
    if _ANTIBODY_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "antibody", 0.95, "keywords"
    elif _PEPTIDE_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "peptide", 0.9, "keywords"
    elif _APTAMER_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "aptamer", 0.9, "keywords"
    elif _FOLATE_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "folate", 0.9, "keywords"
    # Detección de albumina - Versión 3
    elif _ALBUMIN_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "albumin", 0.9, "keywords"
    elif _PEG_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "polymer-peg", 0.8, "keywords"
    elif _TARGET_RE.search(s):
        type["type"], type["type_confidence"], type["type_provenance"] = "targeting", 0.7, "context"

    # Polaridad (más contextual)
    if _HYDROPHOBIC_RE.search(s):
        polarity["polarity"], polarity["polarity_confidence"], polarity["polarity_provenance"] = "nonpolar", 0.8, "keywords"
    elif _HYDROPHILIC_RE.search(s):
        polarity["polarity"], polarity["polarity_confidence"], polarity["polarity_provenance"] = "polar", 0.8, "keywords"
    elif _PEG_RE.search(s):
        polarity["polarity"], polarity["polarity_confidence"], polarity["polarity_provenance"] = "hydrophilic", 0.7, "inferred"

    # Carga eléctrica
    cationic = bool(_LIGAND_CATIONIC_RE.search(s))
    anionic = bool(_LIGAND_ANIONIC_RE.search(s))
    zwit = bool(_LIGAND_ZWITTERIONIC_RE.search(s))

    # Detección de conflicto
    if cationic and anionic:
        charge["charge"], charge["charge_confidence"], charge["charge_provenance"] = "ambiguous", 0.0, "conflict:ligand"
    elif cationic:
        charge["charge"], charge["charge_confidence"], charge["charge_provenance"] = "positive", 0.85, "definition"
    elif anionic:
        charge["charge"], charge["charge_confidence"], charge["charge_provenance"] = "negative", 0.85, "definition"
    elif zwit:
        charge["charge"], charge["charge_confidence"], charge["charge_provenance"] = "neutral", 0.75, "keywords"
    elif _PEG_RE.search(s):
        charge["charge"], charge["charge_confidence"], charge["charge_provenance"] = "neutral", 0.7, "inferred"
    
    # Inferencia por defecto desde type (cuando no hay keywords explícitos de carga) - Versión 3
    if charge["charge"] == "unknown" and type["type"] != "unknown":
        if type["type"] == "antibody":
            # Antibodies son típicamente neutrales/zwitterionic a pH fisiológico
            charge["charge"] = "neutral"
            charge["charge_confidence"] = 0.6
            charge["charge_provenance"] = "inferred:from_type:antibody"
        elif type["type"] == "albumin":
            # Albumin tiene pI ~4.7, negativo a pH fisiológico (7.4)
            charge["charge"] = "negative"
            charge["charge_confidence"] = 0.65
            charge["charge_provenance"] = "inferred:from_type:albumin"
        elif type["type"] == "folate":
            # Folate tiene grupos carboxilo, negativo a pH fisiológico
            charge["charge"] = "negative"
            charge["charge_confidence"] = 0.7
            charge["charge_provenance"] = "inferred:from_type:folate"
    
    # Fallback inference para polaridad desde type
    if polarity["polarity"] == "unknown" and type["type"] != "unknown":
        if type["type"] in ["antibody", "peptide", "albumin", "folate"]:
            # Biomoléculas típicamente hidrofílicas
            polarity["polarity"] = "hydrophilic"
            polarity["polarity_confidence"] = 0.7
            polarity["polarity_provenance"] = "inferred:from_type"

    return {**type, **polarity, **charge}

# Inferencia de biomolécula encapsulada o transportada
def infer_biomolecule_type(display_name: str, definition: str) -> Tuple[str, float, str]:
    s = _combine(display_name, definition)

    # Ácidos nucleicos
    if _DNA_RE.search(s):
        return "DNA", 0.95, "keywords"
    if _RNA_RE.search(s):
        return "RNA", 0.95, "keywords"

    # Proteínas y péptidos
    if _PROTEIN_RE.search(s):
        return "protein", 0.9, "keywords"

    # Polisacáridos o carbohidratos
    if _POLYSACCHARIDE_RE.search(s):
        return "polysaccharide", 0.85, "keywords"

    # Componentes lipídicos o membranosos
    if _MEMBRANE_RE.search(s):
        return "membrane", 0.8, "definition"

    # Receptores o antígenos tumorales
    if _RECEPTOR_RE.search(s):
        return "receptor", 0.85, "keywords"

    # Genes o factores de expresión
    if _GENE_RE.search(s):
        return "gene", 0.8, "context"

    return "unknown", 0.0, "none"

# Inferencia de material de superficie (muchos son fallback de tipo de nanopartícula)
def infer_surface_material(
    display_name: str, 
    synonyms: str, 
    definition: str, 
    ligand_info: Dict[str, Any],
    np_type: str
) -> Tuple[str, float, str]:
    """Infiere el material de la superficie externa de la nanopartícula.
    
    Prioridad:
    1. Ligando conocido (PEG, albumin, antibody, etc.) → domina la superficie
    2. Frases explícitas de coating/shell/functionalization
    3. Fallback al tipo de nanopartícula (core material)
    4. Unknown si nada aplica
    """
    s_combined = _combine(display_name, synonyms, definition)
    
    # Si el ligando es conocido y relevante, domina la superficie
    if ligand_info["type"] in ["polymer-peg", "albumin", "antibody", "protein", "peptide"]:
        # Normalizar polymer-peg → peg para surface.material
        surf_material = "peg" if ligand_info["type"] == "polymer-peg" else ligand_info["type"]
        surf_material_conf = 0.9
        surf_material_prov = f"ligand:{ligand_info['type']}"
        return surf_material, surf_material_conf, surf_material_prov
    
    # Buscar frases de coating / shell / functionalization
    m = re.search(
        r"\b(?:coated|shell|functionalized|grafted|conjugated)\s*(?:with|by)?\s+([\w\-]+(?:\s+[\w\-]+)?)",
        s_combined,
        re.IGNORECASE
    )
    if m:
        # Mapeo de términos detectados → valores estandarizados - HACE FALTA?
        material_mapping = {
            "peg": "peg", "polyethylene": "peg", "pegylated": "peg", "polyethylene glycol": "peg",
            "albumin": "albumin", "protein": "protein",
            "silica": "silica", "silicon": "silica", "sio2": "silica", "silicon dioxide": "silica",
            "lipid": "lipid", "liposomal": "lipid", "lipid bilayer": "lipid",
            "gold": "gold", "au": "gold",
            "polymer": "polymer", "polymeric": "polymer",
            "dextran": "dextran",
            "iron oxide": "iron-oxide", "iron": "iron-oxide"
        }
        matched_material = m.group(1).strip().lower()
        # Filtrar palabras cortas/artículos comunes que no son materiales
        if matched_material not in ["to", "with", "by", "a", "an", "the", "c", "n", "o"]:
            surf_material = material_mapping.get(matched_material, matched_material)
            surf_material_conf = 0.85
            surf_material_prov = f"keywords:coating:{surf_material}"
            return surf_material, surf_material_conf, surf_material_prov
    
    # Fallback al tipo de nanopartícula
    if np_type and np_type != "unknown":
        surf_material = np_type
        surf_material_conf = 0.7
        surf_material_prov = "propagated_from_np_type"
        return surf_material, surf_material_conf, surf_material_prov
    
    # Si nada aplica, mantener unknown
    return "unknown", 0.0, "none"



# ──────────────────────────────────────────────────────────────
# 🔹 CONSTRUCCIÓN DEL INPUT
# ──────────────────────────────────────────────────────────────
def row_to_input(row: pd.Series) -> Dict[str, Any]:
    # obtener display name preferentemente; si está vacío, usar primer sinónimo si existe
    display_raw = _norm(row.get("Display Name"))
    if display_raw:
        display = display_raw
    else:
        syn_raw = _norm(row.get("Synonyms"))
        # tomar solo la primera entrada de Synonyms (separador '|') si existe
        display = syn_raw.split("|", 1)[0].strip() if syn_raw else ""
    syns = _norm(row.get("Synonyms"))
    definition = _norm(row.get("Definition"))
    concept_subset = _norm(row.get("Concept in Subset"))

    # Carga de inferencias
    np_type, np_type_conf, np_type_src = infer_np_type(display, syns, definition)
    np_charge, np_charge_conf, np_charge_src = infer_charge(display, definition, concept_subset)
    biom_type, biom_conf, biom_src = infer_biomolecule_type(display, definition)
    ligand_info = infer_ligand_properties(display, syns, definition)
    
    # Inferir material de superficie (ligand > coating > np_type)
    surf_material, surf_material_conf, surf_material_prov = infer_surface_material(
        display, syns, definition, ligand_info, np_type
    )
    
    # Determinar carga de surface usando la función de inferencia dedicada
    surf_charge, surf_conf, surf_prov = infer_surface_charge(
        display, syns, definition,
        np_charge, np_charge_conf, np_charge_src,
        ligand_info,
        surf_material
    )
    

    # Construir el input case
    input_case = {
        "context": {
            "source_code": _norm(row.get("Code")),
            "display_name": display,
            "semantic_type": _norm(row.get("Semantic Type"))
        },
        "nanoparticle": {
            "type": np_type,
            "type_confidence": np_type_conf,
            "type_provenance": np_type_src,
            "surface_charge": np_charge,
            "surface_charge_confidence": np_charge_conf,
            "surface_charge_provenance": np_charge_src
        },
        "ligand": ligand_info, # es de la misma forma que el resto: type (conf, prov), polarity (conf, prov), charge (conf, prov)
        "biomolecule": {
            "type": biom_type,
            "type_confidence": biom_conf,
            "type_provenance": biom_src
        },
        "surface": {
            "material": surf_material,
            "material_confidence": surf_material_conf,
            "material_provenance": surf_material_prov,
            "charge": surf_charge,
            "charge_confidence": surf_conf,
            "charge_provenance": surf_prov
        },
    }

    return input_case


# ──────────────────────────────────────────────────────────────
# 🔹 CARGA Y EXPORTACIÓN
# ──────────────────────────────────────────────────────────────
def load_and_convert(path: str, n: int = None, save_jsonl: str = None) -> List[Dict[str, Any]]:
    df = pd.read_csv(path, encoding='utf-8')

    if n:
        df = df.head(n)

    outputs = [row_to_input(row) for _, row in df.iterrows()]

    if save_jsonl:
        with open(save_jsonl, "w", encoding="utf-8") as f:
            for item in outputs:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return outputs


# ──────────────────────────────────────────────────────────────
# 🔹 EJECUCIÓN DIRECTA
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out = load_and_convert("../datasets/dataset_FINAL2.csv", save_jsonl="rdr_inputs_v4.jsonl")

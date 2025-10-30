# 🔬 Propuestas de mejora: Ligands v2 → v3

## 📊 Análisis v2

### Distribución actual:
- **ligand.type unknown**: 64/128 (50.0%)
- **ligand.charge unknown**: 107/128 (83.6%)
- **ligand.polarity unknown**: 112/128 (87.5%)

### Casos con type conocido pero incomplete:
- 48 casos tienen `type` pero charge/polarity = unknown
- Ejemplo: antibody detectado pero no se infiere carga ni polaridad

---

## 🛠️ Mejoras propuestas para v3

### 1. **Detectar albumin como ligand type**

**Problema**: 7 casos con "albumin-bound" o "nab-" (nanoparticle albumin-bound) no detectados

**Patrón actual**: Solo detecta en `nanoparticle.type`, no en `ligand.type`

**Solución**: Añadir detección explícita de albumin
```python
_ALBUMIN_RE = re.compile(
    r"\b(albumin[-\s]bound|nab[-\s]|albumin[-\s]stabilized|albumin[-\s]coated|human serum albumin)\b",
    re.IGNORECASE
)
```

**Impacto**: +7 casos detectados → ligand.type = "albumin"

---

### 2. **Inferir carga y polaridad desde ligand.type**

**Problema**: 48 casos tienen type conocido pero charge/polarity = unknown

**Conocimiento de dominio**:
- **Antibodies** → típicamente neutral/zwitterionic a pH fisiológico, hydrophilic
- **Peptides** → variable, pero típicamente hydrophilic (depende de secuencia)
- **PEG** → neutral, hydrophilic (ya detectado)
- **Folate** → neutral/negative, hydrophilic
- **Albumin** → negative a pH fisiológico, hydrophilic

**Solución**: Añadir fallback inference desde type cuando no hay keywords explícitos

```python
# En infer_ligand_properties, después de detectar type:
# Fallback charge inference
if charge["charge"] == "unknown" and type["type"] != "unknown":
    if type["type"] in ["antibody"]:
        charge["charge"] = "neutral"  # zwitterionic a pH ~7
        charge["charge_confidence"] = 0.6
        charge["charge_provenance"] = "inferred:from_type:antibody"
    elif type["type"] in ["albumin"]:
        charge["charge"] = "negative"  # pI ~4.7, negativo a pH fisiológico
        charge["charge_confidence"] = 0.65
        charge["charge_provenance"] = "inferred:from_type:albumin"
    elif type["type"] in ["folate"]:
        charge["charge"] = "negative"  # carboxyl groups
        charge["charge_confidence"] = 0.7
        charge["charge_provenance"] = "inferred:from_type:folate"

# Fallback polarity inference
if polarity["polarity"] == "unknown" and type["type"] != "unknown":
    if type["type"] in ["antibody", "peptide", "albumin", "folate"]:
        polarity["polarity"] = "hydrophilic"
        polarity["polarity_confidence"] = 0.7
        polarity["polarity_provenance"] = "inferred:from_type"
```

**Impacto**: 
- Charge: +10-15 casos (antibodies, albumin, folate)
- Polarity: +20-25 casos (antibodies, peptides, albumin, folate)

---

### 3. **Detectar más patterns de targeting explícito**

**Problema**: Casos con "conjugated to X", "decorated with Y" no extraen el ligand específico

**Ejemplos perdidos**:
- C121214: "coated with anti-egfr antibody" → debería detectar antibody
- C131368: "conjugated to..." → pattern de conjugación explícita

**Solución**: Mejorar regex para extraer ligand post-conjugation
```python
# Buscar patterns "conjugated to/with [ligand]"
_CONJUGATED_PATTERN = re.compile(
    r"\b(?:conjugated|linked|attached|decorated|functionalized|coated)\s+(?:to|with)\s+([\w\-\s]+(?:antibody|peptide|protein|ligand|molecule))\b",
    re.IGNORECASE
)
```

**Impacto**: +2-3 casos con targeting más específico

---

### 4. **Detectar CD markers y otros receptores**

**Problema**: CD20, CD47, etc. no se detectan como targeting

**Solución**: Añadir pattern específico
```python
_CD_MARKER_RE = re.compile(r"\b(cd\d{1,3})\b", re.IGNORECASE)

# En infer_ligand_properties:
if _CD_MARKER_RE.search(s):
    type["type"] = "targeting"
    type["type_confidence"] = 0.85
    type["type_provenance"] = "keywords:cd_marker"
```

**Impacto**: +2 casos

---

### 5. **Detectar EGF y otros growth factors**

**Solución**: Añadir pattern
```python
_GROWTH_FACTOR_RE = re.compile(
    r"\b(egf|epidermal growth factor|vegf|fgf|pdgf|growth factor)\b",
    re.IGNORECASE
)
```

**Impacto**: +1-2 casos

---

## 📈 Impacto total esperado v3

| Métrica | v2 | v3 (estimado) | Mejora |
|---------|-----|---------------|---------|
| **ligand.type unknown** | 64 (50.0%) | 52-55 (40-43%) | -9 a -12 casos |
| **ligand.charge unknown** | 107 (83.6%) | 92-97 (72-76%) | -10 a -15 casos |
| **ligand.polarity unknown** | 112 (87.5%) | 87-92 (68-72%) | -20 a -25 casos |

---

## ✅ Prioridad de implementación

1. ✅ **Alta**: Detectar albumin (impacto +7)
2. ✅ **Alta**: Inferir charge/polarity desde type (impacto +20-30 total)
3. ⚠️ **Media**: CD markers y growth factors (impacto +3-4)
4. ⚠️ **Baja**: Patterns de conjugación avanzados (impacto +2-3, complejidad alta)

---

## 🎯 Recomendación

Implementar mejoras 1 y 2 (albumin + inference desde type) para v3:
- **Esfuerzo**: bajo-medio
- **Impacto**: alto (reducir unknowns ~10-15%)
- **Riesgo**: bajo (conocimiento de dominio bien establecido)

Las mejoras 3 y 4 pueden considerarse para v4 si se necesita mayor cobertura.

---

**Fecha**: 2025-10-29  
**Autor**: Análisis automatizado RDR

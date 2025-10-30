# 🔬 Análisis de Biomoléculas v3 → Propuestas para v4 (opcional)

## 📊 Situación actual v3

- **Total casos**: 128
- **Unknown**: 41 (32.0%)
- **DNA**: 31 (24.2%)
- **RNA**: 26 (20.3%)
- **Protein**: 21 (16.4%)
- **Receptor**: 4 (3.1%)
- **Membrane**: 3 (2.3%)
- **Gene**: 1 (0.8%)
- **Polysaccharide**: 1 (0.8%)

**Cobertura actual**: 68% (87/128 casos con biomolecule detectada)

---

## 🔍 Patterns detectados en unknowns

De los 41 casos unknown, solo **7 casos** (17%) tienen patterns detectables:

| Pattern | Casos | Validación |
|---------|-------|------------|
| Growth factor | 4 | ❌ FALSO POSITIVO (context: "growth" genérico, no factores de crecimiento) |
| PD-1/PD-L1 | 1 | ⚠️ Contexto clínico (regimen terapéutico, no payload) |
| Cytokine (TNF) | 1 | ✅ VÁLIDO (C62538: Tumor Necrosis Factor) |
| Lipid | 1 | ⚠️ Ambiguo (puede ser componente estructural, no payload) |

---

## 🎯 Mejoras propuestas (OPCIONALES)

### Mejora 1: Detectar citokinas específicas ✅

**Caso válido**: C62538 - "Tumor Necrosis Factor" bound to gold nanoparticles

**Patrón actual**:
```python
_PROTEIN_RE = re.compile(r"\b(protein|peptide|enzyme|antibody|immunoglobulin|mab|cytokine)\b", re.IGNORECASE)
```

**Problema**: El regex detecta "cytokine" genérico pero lo mapea a "protein", no a una categoría específica de "cytokine"

**Solución**: Añadir detección específica antes de protein
```python
_CYTOKINE_RE = re.compile(
    r"\b(cytokine|interleukin|il-?\d+|interferon|ifn|tumor necrosis factor|tnf|chemokine)\b",
    re.IGNORECASE
)

# En infer_biomolecule_type:
if _CYTOKINE_RE.search(s):
    return "cytokine", 0.90, "keywords"
```

**Impacto**: +1 caso (C62538)

---

### Mejora 2: Detectar checkpoint receptors (PD-1, PD-L1, CTLA-4) ⚠️

**Caso detectado**: C159408 - Regimen con atezolizumab que menciona "PD-L1-positive TNBC"

**Problema**: Este caso es un **regimen terapéutico**, no una nanopartícula con PD-L1 como payload

**Recomendación**: **NO implementar** - riesgo alto de falsos positivos en contextos clínicos

---

### Mejora 3: Refinar detección de "growth factor" ⚠️

**Casos detectados**: 4 casos, pero todos son **falsos positivos**
- C121961, C165263, C71696: docetaxel formulations (match en "tumor growth", "inhibiting growth")

**Problema**: El pattern `r"\b(growth factor|egf|vegf|fgf)\b"` captura "growth" en contextos no relevantes

**Solución**: Requerir keywords más específicos
```python
_GROWTH_FACTOR_RE = re.compile(
    r"\b(growth factor|egf(?!\s*receptor)|vegf|fgf|pdgf|tgf-beta|ngf|igf)\b",
    re.IGNORECASE
)
```

**Nota**: Usar negative lookahead `(?!\s*receptor)` para evitar capturar "EGF receptor"

**Impacto**: Potencial +0 casos (los actuales son falsos positivos)

---

## 📈 Impacto total esperado v4

| Métrica | v3 | v4 (con mejora 1 solamente) | Cambio |
|---------|-----|------------------------------|---------|
| Unknown | 41 (32.0%) | 40 (31.3%) | -1 caso |
| Cytokine | 0 (0%) | 1 (0.8%) | +1 caso |
| Cobertura | 87/128 (68.0%) | 88/128 (68.8%) | +0.8% |

---

## ✅ Recomendación

### Para v4 (si se desea):
- ✅ **Implementar mejora 1** (cytokine detection): impacto +1, riesgo bajo
- ❌ **NO implementar mejora 2** (checkpoint receptors): riesgo alto de falsos positivos
- ⚠️ **NO implementar mejora 3** (refinar growth factor): los casos actuales son falsos positivos, mejor dejar como está

### Alternativa: **NO hacer v4 para biomolecules**
- La cobertura actual (68%) es **razonable** para un dataset clínico
- Solo 1 caso genuino perdido (TNF)
- El esfuerzo vs beneficio no justifica una v4

**34 de los 41 unknowns** (83%) no tienen señales textuales de biomoléculas → **es normal** en formulaciones farmacéuticas donde la biomolécula no es el payload principal

---

## 🎯 Conclusión

**Recomendación final**: **Mantener v3 sin cambios en biomolecules**

Razones:
1. Solo 1 caso válido perdido (2.4% de unknowns)
2. Cobertura 68% es adecuada para dataset clínico
3. Riesgo de falsos positivos con mejoras adicionales
4. Mejor enfoque: probar v3 con reglas antes de invertir en v4

Si tras probar las reglas se detecta necesidad de mayor cobertura, entonces implementar mejora 1 (cytokine) en una futura iteración.

---

**Fecha**: 2025-10-30  
**Autor**: Análisis automatizado RDR

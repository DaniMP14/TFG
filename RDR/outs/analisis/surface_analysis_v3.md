# 📊 Análisis de Superficie (Material y Carga) - Versión 3

## 🎯 Objetivo
Evaluar si existen patrones detectables en los valores `unknown` de `surface.material` y `surface.charge` para implementar mejoras en una versión 4.

---

## 📈 Resultados: SURFACE.MATERIAL

### Distribución Actual (v3)
- **Total casos**: 128
- **Material=unknown**: **1 caso (0.8%)** ✅

| Material | Casos | % |
|----------|-------|---|
| lipid-based | 31 | 24.2% |
| polymeric | 28 | 21.9% |
| peg | 16 | 12.5% |
| nanoparticle | 11 | 8.6% |
| antibody | 9 | 7.0% |
| albumin | 8 | 6.2% |
| peptide | 5 | 3.9% |
| metallic | 5 | 3.9% |
| **unknown** | **1** | **0.8%** |

### Análisis de Patrones
- **Patrones detectados en unknown**: 0/1 (0%)
- **Caso único**: C39438 (Jonsson Comprehensive Cancer Center) - entrada errónea en el dataset, NO es nanopartícula

### ✅ Conclusión: Material
**NO requiere mejoras**. La cobertura del 99.2% es excelente. El único caso "unknown" es un error de dataset (entrada sobre un centro de investigación, no una nanopartícula terapéutica).

---

## 📈 Resultados: SURFACE.CHARGE

### Distribución Actual (v3)
- **Total casos**: 128
- **Charge=unknown**: **91 casos (71.1%)**

| Carga | Casos | % |
|-------|-------|---|
| **unknown** | **91** | **71.1%** |
| negative | 17 | 13.3% |
| neutral | 11 | 8.6% |
| positive | 9 | 7.0% |

### Proveniencia de Surface.Charge
| Proveniencia | Casos | % |
|--------------|-------|---|
| propagated_from_nanoparticle:none | 91 | 71.1% |
| inferred:cell_membrane | 16 | 12.5% |
| propagated_from_nanoparticle:keywords:peg | 10 | 7.8% |
| propagated_from_nanoparticle:keywords | 5 | 3.9% |
| otros | 6 | 4.7% |

### Análisis de Patrones en Unknowns
- **Patrones textuales detectados**: 0/91 (0%)
- **Zeta potential detectado**: 0/91 (0%)

**Interpretación**: Los 91 casos unknown tienen `nanoparticle.surface_charge=unknown`, por lo que no hay valor para propagar. Las definiciones NO contienen keywords explícitas de carga de superficie.

---

## 🔍 Oportunidad de Mejora Detectada

### 🎯 Propagación desde Ligando → Superficie

**Hallazgo clave**: Existen **18 casos** donde:
- `surface.charge = unknown`
- `ligand.charge` es **conocida** (neutral o negative)
- `surface.material` coincide con el tipo de ligando (albumin, antibody, peg)

#### Distribución de estos 18 casos:
| Ligand Type | Ligand Charge | Casos |
|-------------|---------------|-------|
| antibody | neutral | 9 |
| albumin | negative | 8 |
| polymer-peg | neutral | 1 |

#### ✅ Casos con Funcionalización Explícita (10/18)
Candidatos **FUERTES** para propagar `ligand.charge → surface.charge`:

| Código | Display Name | Ligand Type | Ligand Charge | Keywords Detectadas |
|--------|--------------|-------------|---------------|---------------------|
| C131213 | Nab-paclitaxel/Rituximab-coated NP | antibody | neutral (0.60) | coated, bound, targeted |
| C136981 | Anti-EphA2 Antibody-directed Liposome | antibody | neutral (0.60) | conjugated |
| C158083 | Cetuximab-loaded EC NP Decorated | antibody | neutral (0.60) | decorated |
| C180674 | CD122-selective IL-2/Anti-CD25 | antibody | neutral (0.60) | modified |
| C187124 | mRNA Anti-CD3/Anti-CLDN6 | antibody | neutral (0.60) | modified |
| C190739 | Nab-paclitaxel/Danburstotug | antibody | neutral (0.60) | bound, targeted |
| C116890 | Nab-Thiocolchicine Dimer | albumin | negative (0.65) | bound |
| C71696 | Nab-Docetaxel | albumin | negative (0.65) | bound |
| C74065 | Sirolimus Albumin-bound NP | albumin | negative (0.65) | bound |
| C82691 | Hsp90 Inhibitor AB-010 | albumin | negative (0.65) | bound |

#### ⚠️ Casos sin Keywords Explícitas (8/18)
Requieren evaluación **CONTEXTUAL** (¿el ligando domina la superficie?):

| Código | Display Name | Ligand Type | Ligand Charge |
|--------|--------------|-------------|---------------|
| C147562 | Synthetic Vaccine Particles-Rapamycin | antibody | neutral |
| C148522 | HAAH Lambda phage Vaccine | antibody | neutral |
| C179620 | mRNA Anti-Claudin18.2 | antibody | neutral |
| C2688 | Nab-paclitaxel | albumin | negative |
| C124053 | Bendamustine NP RXDX | albumin | negative |
| C159408 | Atezolizumab/Nab-paclitaxel Regimen | albumin | negative |
| C166389 | Atezolizumab/Carbo/Nab-paclitaxel | albumin | negative |
| C82676 | Irinotecan Sucrosofate | polymer-peg | neutral |

---

## 💡 Recomendaciones para Versión 4

### ✅ Mejora Recomendada: Propagación Ligand→Surface (Condicional)

**Implementar lógica**:
```python
# En infer_surface_charge(), ANTES del fallback a unknown:

# Si surface.material coincide con ligand type Y ligand.charge es confiable
if (
    ligand_info.get("charge") not in (None, "", "unknown")
    and ligand_info.get("charge_confidence", 0.0) >= 0.60  # threshold
):
    # Casos fuertes: funcionalización explícita
    if re.search(r"\b(functionalized|conjugated|coated|bound|decorated|grafted|targeted)\b", 
                 s_combined, re.IGNORECASE):
        return (
            ligand_info["charge"], 
            ligand_info["charge_confidence"] * 0.95,  # ligero descuento
            f"propagated_from_ligand:{ligand_info['type']}"
        )
    
    # Casos contextuales: cuando surface.material == ligand type detectado
    # (albumin, antibody, peg) → asumir que el ligando domina la superficie
    if (
        (surf_material == "albumin" and ligand_info["type"] == "albumin")
        or (surf_material == "antibody" and ligand_info["type"] == "antibody")
        or (surf_material == "peg" and ligand_info["type"] == "polymer-peg")
    ):
        return (
            ligand_info["charge"],
            ligand_info["charge_confidence"] * 0.85,  # mayor descuento por contexto
            f"inferred_from_surface_material:{ligand_info['type']}"
        )
```

### 📊 Impacto Estimado
- **Reducción de unknowns**: 91 → ~73 (18 casos recuperados)
- **Mejora porcentual**: 71.1% → 57.0% unknowns (~14% de mejora relativa)
- **Confidence**: 0.51-0.62 (razonable para inferencias contextuales)

### ⚠️ Riesgos
- **Bajo**: La lógica es conservadora (requiere material coincidente O funcionalización explícita)
- **Validación**: Los 10 casos con funcionalización explícita son casi seguros
- **Casos límite**: Los 8 sin keywords requieren validación con reglas RDR

---

## 🏁 Decisión Final

### ❌ Material: NO requiere v4
- Cobertura 99.2% (1 único unknown es error de dataset)

### ✅ Charge: IMPLEMENTAR mejora condicional
- **18 casos recuperables** (14% de los unknowns)
- **Lógica conservadora** con 2 niveles:
  1. Funcionalización explícita (10 casos, alta confianza 0.57-0.62)
  2. Material coincidente (8 casos, confianza media 0.51-0.55)

### 📋 Próximos Pasos
1. **Implementar** propagación ligand→surface con lógica propuesta
2. **Generar v4** con `save_jsonl="rdr_inputs_v4.jsonl"`
3. **Comparar** v3 vs v4 con script de validación
4. **Probar** con motor GRDR para validar mejoras en matching de reglas

---

## 📝 Conclusiones

✅ **Surface.material está COMPLETO** (99.2% cobertura)

✅ **Surface.charge puede mejorar 14%** mediante propagación condicional desde ligandos

✅ **Estrategia conservadora** minimiza riesgo de falsos positivos

✅ **Mejoras alineadas con dataset NCIt**: enfoque en formulaciones clínicas con ligandos bien caracterizados (nab-, antibody-targeted)

🎯 **Recomendación**: Implementar mejora de charge, saltarse material (ya óptimo).

# 🔬 Análisis de nanoparticle.surface_charge v1 → Propuestas para v2

## 📊 Estadísticas v1

- **Total casos**: 128
- **Unknown**: 107 (83.6%) ⚠️
- **Neutral**: 15 (11.7%) - casi todos por PEG
- **Positive**: 6 (4.7%)
- **Negative**: 0 (0.0%)
- **Ambiguous**: 0 (0.0%)

### Provenance breakdown:
- `none`: 107 (83.6%)
- `keywords:peg`: 14 (10.9%)
- `keywords`: 5 (3.9%)
- `inferred:chemical_group`: 2 (1.6%)
- `parametric:zeta`: **0 (0.0%)** ❌

---

## 🔍 Hallazgos Clave

### 1. **Zeta potential NO está funcionando**
- 0 casos detectados con `parametric:zeta`
- Regex actual: `r"zeta[^\d\-\+]{0,15}([+\-]?\d+(?:[.,]\d+)?)\s*(m?v|millivolt)s?\b"`
- **Problema**: El dataset NCIt no incluye valores paramétricos de zeta potential
- **Conclusión**: El mecanismo de zeta es útil conceptualmente pero irrelevante para este dataset

### 2. **90.7% de unknowns NO tienen señales textuales de carga**
- Solo 10/107 casos unknown tienen patterns detectables
- La mayoría son formulaciones farmacéuticas sin mencionar carga explícitamente
- **Conclusión**: Es normal tener muchos unknowns en datasets clínicos/farmacéuticos

### 3. **Falsos negativos detectados (casos que DEBERÍAMOS capturar)**

#### Alta prioridad:
| Code | Display | Pattern perdido | Carga esperada |
|------|---------|-----------------|----------------|
| C204794 | Autologous Total Tumor mRNA Loaded Liposome Vaccine | DOTAP (cationic lipid) | positive |
| C68566 | Amine-functionalized dextran nanoparticles | amine-functionalized | positive |
| C202862 | PLZ4-coated Paclitaxel-loaded Micelle | amino groups + pH-responsive | positive (probable) |

#### Media prioridad:
| Code | Display | Pattern perdido | Nota |
|------|---------|-----------------|------|
| C173879 | Encapsulated Rapamycin | pH-sensitive | Sin más contexto, difícil inferir carga |
| C201982 | Dual-activating STING Agonist ONM-501 | pH-sensitive | Sin más contexto, difícil inferir carga |

---

## 🛠️ Propuestas de mejora para v2

### ✅ **Mejoras a implementar:**

#### 1. **Ampliar detección de lipidos catiónicos**
Añadir patterns más robustos para lipids catiónicos:
```python
_CATIONIC_LIPID_RE = re.compile(
    r"\b(dotap|dotma|dope|dodap|ddab|dc-chol|cationic\s*lipid|lipofectamine)\b",
    re.IGNORECASE
)
```

**Aplicar en `infer_charge()`**:
- Si se detecta cationic lipid → `positive, conf=0.90, prov=keywords:cationic_lipid`

#### 2. **Mejorar detección de grupos funcionales**
Expandir patterns de grupos amino:
```python
_AMINE_FUNCTIONALIZED_RE = re.compile(
    r"\b(amine[-\s]functionalized|amino[-\s]functionalized|amine\s*group|amino\s*group)\b",
    re.IGNORECASE
)
```

**Aplicar en `infer_charge()`**:
- Si se detecta amine-functionalized → `positive, conf=0.85, prov=inferred:amine_functionalized`

#### 3. **Refinar regex de zeta potential** (aunque no es crítico para este dataset)
Problema actual: captura códigos de producto (V-5671 → `-5671 v`)

**Solución**: Requerir contexto más estricto
```python
_ZETA_RE = re.compile(
    r"zeta\s*potential[^.,]{0,30}?([+\-]\d+(?:[.,]\d+)?)\s*m?v\b",
    re.IGNORECASE
)
```

#### 4. **pH-sensitive: no inferir carga directamente**
- pH-sensitive indica **variabilidad de carga** según entorno
- No podemos inferir una carga única sin más contexto
- **Recomendación**: Mantener como unknown, o crear un nuevo label `ph_dependent`

---

## 📈 Impacto esperado v2

Con las mejoras propuestas:

| Métrica | v1 | v2 (estimado) | Mejora |
|---------|-----|---------------|---------|
| Unknown | 107 (83.6%) | ~104 (81.3%) | -3 casos |
| Positive | 6 (4.7%) | ~9 (7.0%) | +3 casos |
| Cobertura (no-unknown) | 21 (16.4%) | 24 (18.7%) | +2.3% |

**Mejora modesta pero relevante**: 3 falsos negativos corregidos

---

## 🎯 Conclusiones

### ¿Es útil el mecanismo de zeta?
**No para este dataset específico** (NCIt thesaurus), pero sí para:
- Datasets científicos con valores experimentales
- Literatura biomédica con reportes de caracterización
- Bases de datos de nanopartículas con propiedades fisicoquímicas

**Recomendación**: Mantener el código de zeta para datasets futuros, pero no es prioritario optimizarlo ahora.

### ¿Son aceptables los 83% unknowns?
**Sí, es razonable** para este tipo de dataset:
- NCIt es un thesaurus **clínico/farmacéutico**, no un catálogo de propiedades fisicoquímicas
- Las formulaciones se describen por composición, no por caracterización física
- Inferir carga sin evidencia textual sería especulación

**Alternativas para reducir unknowns** (fuera de alcance actual):
- Cruzar con bases de datos externas (PubChem, NanoHub, etc.)
- Integrar reglas basadas en composición química completa
- Entrenar modelos de ML con datasets anotados

---

## ✅ Plan de acción para v2

1. ✅ Implementar detección de lipidos catiónicos (DOTAP, etc.)
2. ✅ Implementar detección de amine-functionalized
3. ✅ Refinar regex de zeta (aunque sea baja prioridad)
4. ⚠️ NO inferir carga desde pH-sensitive (mantener unknown)
5. 🧪 Regenerar rdr_inputs_v2.jsonl
6. 📊 Comparar distribuciones v1 vs v2
7. ✅ Validar que los 3 falsos negativos se corrigen

---

**Fecha**: 2025-10-29  
**Autor**: Análisis automatizado RDR

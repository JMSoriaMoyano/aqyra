# Decopak HQ — Bases de cálculo y acciones (HIPÓTESIS)

- **Documento:** propuesta de hipótesis de acciones · **rol:** build (producción)
- **Estado:** ✅ **APROBADO por JM (2026-06-24).** Sismo y datos geotécnicos confirmados con el informe SOCOTEC (ver `04_geotecnia_sintesis.md`). El cálculo de elementos arranca.
- **Norma marco:** EN 1990 (EC0) + EN 1991 (EC1) con **Anejo Nacional español**; emplazamiento según CTE DB-SE-AE y NCSE-02.
- **Fecha:** 2026-06-24 · **Emplazamiento:** Rubí (Barcelona), altitud ≈ 124 m.

> Las casillas marcadas **[CONFIRMAR JM]** son decisiones de Dirección/firma o valores a contrastar contra el mapa oficial para las coordenadas exactas de la parcela.

---

## 0. Resumen de decisiones que requieren tu visto bueno

| # | Hipótesis | Propuesta | Decisión |
|---|---|---|---|
| H1 | Vida útil / clase de consecuencias | 50 años · CC2 (KFI = 1,0) | [CONFIRMAR JM] |
| H2 | Categorías de uso (sobrecarga) | B oficinas; C1 sala formación/altillo; H cubierta no transitable; G acceso vehículos no | [CONFIRMAR JM] |
| H3 | Viento | Zona C (vb,0 = 29 m/s; qb = 0,52 kN/m²); cat. terreno III | [CONFIRMAR JM] |
| H4 | Nieve | sk = 0,40 kN/m² (Barcelona, ≤ 200 m) | [CONFIRMAR JM] |
| H5 | Sismo | ab = 0,04 g, K = 1,0, ρ = 1,0 (importancia normal). **Recomiendo SÍ comprobar** (ver §5) | [DECISIÓN JM] |
| H6 | Térmicas | Considerar en cubierta/voladizos metálicos expuestos; ΔT según EC1-1-5 | [CONFIRMAR JM] |

---

## 1. Bases de cálculo (EC0)

- **Vida útil de proyecto:** 50 años (categoría 4, edificios y obra común).
- **Clase de consecuencias:** CC2 (edificio de oficinas estándar) → KFI = 1,0.
- **Estados límite:** ELU (resistencia STR / cimiento GEO; equilibrio EQU; y, donde aplique, fatiga FAT en piezas metálicas sometidas a tráfico/maquinaria — **no previsto** en uso oficinas) y ELS (deformaciones, vibraciones, fisuración, descompresión).
- **Coeficientes parciales (ELU, AN español):**
  - Permanentes: γG = 1,35 (desfavorable) / 1,00 (favorable).
  - Variables: γQ = 1,50 (desfavorable) / 0 (favorable).
  - Materiales: γc = 1,5 (hormigón), γs = 1,15 (acero pasivo), γM0 = 1,05 / γM1 = 1,05 / γM2 = 1,25 (acero estructural, AN); γM (madera/CLT) = 1,25 con kmod según clase de servicio.

## 2. Acciones permanentes (G)

| Concepto | Valor propuesto | Nota |
|---|---|---|
| Peso propio acero S355 | 78,5 kN/m³ | de la geometría de perfiles |
| Peso propio HA-30 | 25,0 kN/m³ | muros, encepados |
| Peso propio CLT | ≈ 5,0 kN/m³ (≈ 480 kg/m³) | losa CLT/cassette |
| Carga muerta forjado (solado, falso techo, instalaciones) | **2,0 kN/m²** | [CONFIRMAR JM] según acabados |
| Fachada / cerramiento (lineal en bordes) | **a definir** kN/m | [CONFIRMAR JM] tipo de fachada |
| Cubierta (impermeabilización, formación pendiente, grava/ajardinada) | **2,5 kN/m²** | [CONFIRMAR JM] según tipo de cubierta |

## 3. Sobrecargas de uso (Q) — EC1-1-1 / DB-SE-AE

| Zona | Categoría | qk (kN/m²) | Qk concentrada (kN) |
|---|---|---|---|
| Oficinas (PB, P1–P3) | B | 2,0 | 2,0 |
| Sala de formación / altillo-lab (zona de reunión con mesas) | C1 | 3,0 | 4,0 |
| Zonas de paso / escaleras de oficina | B/C | 3,0 | — |
| Cubierta no transitable (solo mantenimiento) | H (G1) | 0,4 (1,0 punt.) | — |

- **Reducción por superficie/nº de plantas:** aplicable a oficinas (αA, αn) en pilares y cimentación; se documentará por elemento.
- **Tabiquería repartida** (si procede): +1,0 kN/m² en zonas de oficina — [CONFIRMAR JM].

## 4. Viento (W) — EC1-1-4 / CTE DB-SE-AE

- **Zona eólica:** **C** (provincia de Barcelona) → velocidad básica vb,0 = **29 m/s**; presión dinámica básica qb = **0,52 kN/m²**. **[CONFIRMAR JM]** contra el mapa oficial para las coordenadas exactas (Rubí está a ≈ 20 km del litoral; verificar banda de zona).
- **Categoría de terreno:** **III** (zona industrial/suburbana — Rubí). 
- **Esbeltez:** el edificio es alargado (≈ 11,5 × 40,5 m en planta, 15 m de alto + voladizos). El viento transversal sobre la cara larga (40,5 m) es probablemente la acción lateral gobernante; verificar succión en voladizos y vuelco de la cara a sotavento.
- **Coeficientes:** ce(z) por terreno III y altura; cp,net por geometría (cubierta y fachadas); cf en elementos expuestos. Se desarrollarán en el cálculo.

## 5. Sismo (E) — NCSE-02 / EC8 con AN español

**Determinación (CONFIRMADA por el informe geotécnico SOCOTEC):** Rubí → **ab = 0,04 g**, **K = 1,0**, importancia normal **ρ = 1,0**. Coeficiente de tipo de suelo **C = 1,4386**, amplificación **S = 1,1509** → **aceleración de cálculo ac = 0,046 g**. Estrato portante UG3 = terreno Tipo II. (Ver `04_geotecnia_sintesis.md` §6.)

- ρ·ab = 0,04 g ≤ 0,1 g → coeficiente de amplificación del terreno **S = C/1,25** (C según estudio geotécnico; con C ≈ 1,3–1,6, S ≈ 1,04–1,28 → **ac ≈ 0,042–0,051 g**).
- **Criterio de aplicación (NCSE-02 §1.2.3):** la norma **es de aplicación** porque ab = 0,04 g (no es estrictamente < 0,04 g). Existe la exención para construcciones de importancia normal con **pórticos bien arriostrados en todas las direcciones** y ab < 0,08 g; **no recomiendo acogerse a ella** en este edificio por su **irregularidad** (grandes voladizos, masas excéntricas, sistema mixto acero–CLT–hormigón).

**Recomendación (propuesta):** **incluir la combinación sísmica** con un análisis sencillo (estático equivalente o modal espectral reducido) centrado en los núcleos arriostrados de acero y los muros HA. Por el bajo valor de ac, es previsible que **viento y gravedad gobiernen** lo lateral, pero conviene dejar la comprobación sísmica documentada (regularidad, ductilidad, deriva). **Decisión final: JM.**

## 6. Acciones térmicas (T) — EC1-1-5

- Considerar variación uniforme de temperatura en piezas metálicas largas y voladizos expuestos (cordones del cajón, dinteles). ΔT estacional según zona y color/exposición.
- En estructura interna climatizada el efecto es menor; relevante en cubierta y voladizos al exterior. [CONFIRMAR JM] si hay juntas de dilatación previstas.

## 7. Combinaciones (EC0, AN español)

**ELU (STR/GEO), persistente/transitoria:**

```
Ed = Σ γG,j·Gk,j  +  γQ,1·Qk,1  +  Σ γQ,i·ψ0,i·Qk,i
   = 1,35·G + 1,50·Q1 + 1,50·Σ ψ0,i·Qi
```

**ELU sísmica:**

```
Ed = Σ Gk,j  +  AEd  +  Σ ψ2,i·Qk,i
```

**ELS:** característica `G + Q1 + Σψ0·Qi`; frecuente `G + ψ1·Q1 + Σψ2·Qi`; cuasipermanente `G + Σψ2·Qi`.

**Coeficientes de simultaneidad ψ (AN español):**

| Acción | ψ0 | ψ1 | ψ2 |
|---|---|---|---|
| Sobrecarga oficinas (B) | 0,7 | 0,5 | 0,3 |
| Sobrecarga zonas reunión (C) | 0,7 | 0,7 | 0,6 |
| Cubierta (H) | 0 | 0 | 0 |
| Nieve (≤ 1000 m) | 0,5 | 0,2 | 0 |
| Viento | 0,6 | 0,2 | 0 |
| Térmica | 0,6 | 0,5 | 0 |

## 8. Criterios de servicio (ELS)

- **Flechas:** verticales L/300 (apariencia, cuasipermanente) y L/250–L/400 según elemento y tabiquería frágil; **voladizos: límite sobre la longitud del voladizo** (criterio EC + confort) — **clave en este edificio**. [CONFIRMAR JM] límite adoptado para voladizos CLT.
- **Desplome / deriva** lateral por viento: H/500 entre plantas (tabiquería frágil) — [CONFIRMAR JM].
- **Vibraciones de forjado CLT** (EC5 / confort): comprobar frecuencia propia f1 ≥ 8 Hz o criterio de aceleración; relevante por la ligereza del cassette en voladizo.
- **Fisuración HA** (EC2): wk ≤ 0,3 mm (muros/encepados, clase de exposición a definir por geotecnia/ambiente).

---

## 9. Para el informe de QA (trazabilidad de hipótesis)

```
norma:     EC0/EC1 + AN español; CTE DB-SE-AE; NCSE-02
sitio:     Rubí (Barcelona), ~124 m
viento:    zona C, vb0=29 m/s, qb=0,52 kN/m², terreno III   [a confirmar mapa]
nieve:     sk=0,40 kN/m²
sismo:     ab=0,04g, K=1,0, ρ=1,0  → ac≈0,042–0,051g (S por geotecnia)
γ/ψ:       γG=1,35/1,00, γQ=1,50/0; ψ por tabla §7 (AN)
estado:    PROPUESTA — pendiente aprobación JM antes de calcular
```

# QA Decopak HQ — Resumen de los 6 casos golden

> **QA verificado con FEM nodal numpy independiente + analítico. SIN el oráculo PyNite certificado (no instalable en este entorno) → pendiente de RE-EJECUCIÓN en entorno con PyNite para el cierre definitivo. Pendiente de firma de JM (la IA no certifica).**

- **Ejecutado por:** agente de QA independiente (ejecución separada del build) · **Fecha:** 2026-06-24
- **Oráculos:** (1) solver FEM nodal propio por **método directo de rigidez** en numpy puro, sobre los **nudos y conectividad REALES extraídos del IFC** (celosía 2D Vierendeel del Cajón O, bien condicionada: 3 modos de sólido rígido exactos, equilibrio con residuo ~1e-12); (2) **fórmulas cerradas EC** derivadas de forma independiente (EC3 6.3.1, EC5 §7.3, EC2 §6.5, EC7).
- **Versión verificada:** **NO ANCLADA** (versions.lock=0.0.0) → resultado «verificado sobre versión no anclada».

---

## Tabla de los 6 casos

| Caso | Elemento | Magnitud clave | Valor build | Valor QA | ¿Dentro tol.? | **Veredicto** |
|---|---|---|---|---|---|---|
| **DEC-A1** | Costilla IPE 160 + CLT | u_M | 0,39 | 0,39 | ☑ (±2%) | — |
| | | **δ flecha** | **2,6 mm** | **9,87 mm** | ☒ (+280%) | **NO APTO** |
| | | **f₁ vibración** | **8,5 Hz** | **6,7–7,7 Hz (<8)** | ☒ (−10/−21%) | **NO APTO** |
| **DEC-B1** | Diagonal SHS 200×10 | N_b,Rd | 2.004 kN | 1.978 kN | ☑ (−1,3%, ±3%) | **APTO** (cond.) |
| | | N_Ed | 778 kN | ≈348 kN (FEM) | build conservador | |
| **DEC-B2** | Cordón SHS 180×8 | N_b,Rd | 1.600 kN | 1.595 kN | ☑ (−0,3%, ±5%) | **APTO** |
| | | N_Ed | 409 kN | ≈330 kN (FEM) | build conservador | |
| **DEC-B4** | Montante SHS 120×6 | **L_cr real** | 3,08 m (supuesto) | **3,08 m (confirmado por geometría)** | ☑ | **APTO (cond.)** |
| | | u (arriostrado) | 0,40 | 0,62 (N_Ed FEM=392) | cumple | |
| | | u (no arriostrado) | 2,1 | 3,26 | no cumple | NO APTO si no arr. |
| **DEC-E1** | Encepados bielas-tir. | T (Lab/Vest) | 809/864 kN | 811/860 kN | ☑ (±0,5%, ±3%) | **APTO** |
| **DEC-E2** | Pilote D650 (EC7) | R_adm | 2.396 kN | 2.397 kN | ☑ (+0,04%, ±5%) | **APTO** |

**Resultado global:** 4 APTO (B1, B2, E1, E2) · 1 APTO condicionado a decisión de proyecto (B4) · **1 NO APTO (A1)** por errores aritméticos del build en los ELS de flecha y vibración.

---

## Hallazgo del montante (DEC-B4) — el punto crítico

- Extraídos los **nudos reales del IFC**: el montante SHS 120×6 (Z=5,75→15,0; h=9,25 m) **comparte nudo con los cordones del cajón en Z = 5,75 · 8,833 · 11,917 · 15,0**, quedando dividido en **3 segmentos de ≈3,08 m**. Esos nudos están triangulados por diagonales y cerrados por diafragmas.
- → **La longitud de pandeo efectiva real es L_cr ≈ 3,08 m** (no 9,25 m). **El supuesto S-B1 del build queda confirmado por la geometría/conectividad real, no asumido.** Con L_cr=3,08 m: N_b,Rd=632 kN, **cumple**.
- **Matiz de QA:** mi FEM nodal carga el montante crítico a **N_Ed≈392 kN**, +57 % sobre los 250 kN que el build estimó por áreas tributarias → u real **0,62** (no 0,40). Sigue cumpliendo, pero con menos holgura. **Decisión de JM:** confirmar en planos de detalle que las uniones materializan la coacción lateral cada 3,08 m. Si NO se materializase → u≥2 → NO APTO.

## Discrepancias relevantes con el build

1. **DEC-A1 (NO APTO):** dos errores de aritmética del build, ambos en los ELS gobernantes del voladizo CLT:
   - **Flecha:** la propia fórmula del build evalúa a **9,87 mm**, no 2,6 mm (×3,8). El correcto cumple L/300, pero el valor a verificar está mal.
   - **Vibración:** la propia fórmula del build da **7,66 Hz** (con su masa 346 kg/m), no 8,5 Hz; con masa realista ≈450 kg/m, **6,7 Hz**. En ambos casos **f₁ < 8 Hz → INCUMPLE EC5 §7.3**. El build lo daba por aprobado (marginal 8,5 Hz).
2. **Reparto de reacciones a muros (S-D1):** el FEM nodal da **NC-Lab 35 % / NC-Vest 65 %**, **confirmando** el reparto por áreas del build (65/35). Las reacciones por plano: Lab≈589 kN, Vest≈1.092 kN (×2 planos en total).
3. **Reparto de axiles en la celosía:** el FEM nodal **NO encontró picos locales por encima de la estimación global del build**; al contrario, el build sobreestima (conservador) el axil de diagonal (778 vs ≈348 kN FEM) y de cordón (409 vs ≈330 kN). La capacidad (N_b,Rd) coincide al ≤1,3 %.
4. **Perfil de la diagonal (DEC-B1):** el IFC tiene **7 perfiles distintos** de diagonal en el Cajón O (SHS 250×16/250×12/200×10/160×8/150×8/120×6/300×16). La ficha golden verifica solo "SHS 200×10"; build debe identificar el perfil de la diagonal crítica real.

## Casos NO APTO / que requieren corrección de build o decisión de JM

- **DEC-A1 — NO APTO.** Devolución a build: corregir la flecha (9,87 mm) y **resolver la vibración** (f₁≈6,7–7,7 Hz < 8 Hz). Opciones: aumentar canto/rigidez del nervio, contar la sección mixta acero-CLT (conexión), o justificar por criterio de aceleración. **Decisión de modelo/proyecto para JM.**
- **DEC-B4 — APTO condicionado.** JM debe (a) confirmar la coacción lateral cada 3,08 m en planos de detalle; (b) build debe revisar N_Ed del montante (392 kN nodal > 250 kN tributario).
- **DEC-E2 — reserva de formato.** JM debe fijar el formato EC7 (admisible SOCOTEC vs parcial con γ_R).
- **DEC-B1/B2/E1 — APTO**, con la condición de identificar el perfil real de la diagonal (B1) y confirmar la bajada de cargas global con PyNite (E1).

## Limitaciones de esta verificación (qué queda para el entorno PyNite)

- **No se pudo usar el oráculo PyNite certificado** (no instalable: pip > 45 s, disco lleno). Se usó un solver FEM nodal propio en numpy. **Pendiente de re-ejecución con PyNite** para el cierre definitivo, en particular:
  - El **modelo 3D completo del Cajón O** con conectividad perfecta (el modelo 3D articulado/pórtico quedó con sub-ensamblajes desconectados por cómo el IFC modela cordones continuos de 40,86 m; QA resolvió un **modelo 2D Vierendeel bien condicionado** del alzado desarrollado, que es válido para chequear el reparto chord/diagonal/montante, pero el 3D fino debe rehacerse con PyNite).
  - La **bajada de cargas global del edificio** (magnitud absoluta de N_Ed de cimentación, ≈12.700 kN): QA verificó el **reparto** (65/35) pero no recalculó toda la bajada de cargas (fuera del alcance del Cajón O).
  - **S-F1 (sismo):** QA no ejecutó el modal espectral con torsión; con ac=0,046 g es improbable que gobierne, pero queda pendiente del modelo modal.
- Resultado **«verificado sobre versión no anclada»** (versions.lock=0.0.0).

---

## Scripts QA (oráculos independientes)

| Script | Función |
|---|---|
| `qa/informes/qa_geom_extract.py` | Extrae nudos y conectividad REALES del IFC (cadena de placements + extrusiones), numpy puro |
| `qa/informes/qa_truss2d_cajonO.py` | Solver FEM nodal 2D (rigidez directa) del Cajón O: reacciones, axiles, L_cr del montante |
| `qa/informes/qa_frame_cajonO.py` | Intento de pórtico 3D (documenta por qué el 3D del IFC requiere subdivisión/PyNite) |
| `qa/informes/qa_normativa.py` | Capa normativa independiente: EC3 6.3.1, EC5 §7.3, EC2 §6.5, EC7 (los 6 casos) |

**Salidas:** `qa_cajonO_geom.json`, `qa_truss2d_axiles.json`, `qa_cajonO_frame_axiles.json`.

---
**Estado:** informe de QA emitido. **A la espera de la firma de JM (segunda llave).** La IA no certifica.

# Decopak HQ — Memoria de cálculo estructural (consolidada)

> **PROPUESTA — pendiente de verificación QA independiente y firma de JM. Versión de núcleo no anclada (versions.lock=0.0.0).**

- **Proyecto:** Decopak HQ — Variante B v3 OPTIMIZADO (EC3). Emplazamiento: Rubí (Barcelona).
- **Rol:** build (producción). La verificación la ejecuta un agente QA independiente; la **firma corresponde a JM** (técnico competente). La IA **no firma ni certifica**.
- **Fecha:** 2026-06-24. **Modelo:** `DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc` (IFC4).
- **Documentos base:** `01_validacion_IFC.md`, `02_bases_acciones_HIPOTESIS.md` (APROBADO), `03_plan_calculo.md`, `04_geotecnia_sintesis.md`. Detalle por subsistema: `05` (CLT), `06` (acero), `07` (HA/cimentación/sismo). Golden: `08`.

---

## 1. Objeto y alcance

Predimensionado de la estructura completa del piloto Decopak HQ a partir de su modelo IFC: forjado CLT cassette en voladizo (A), celosías de acero del núcleo lateral (B) y sus enlaces (C), muros de hormigón (D), cimentación profunda (E) y comprobación sísmica (F). Es un **cálculo de predimensionado defendible**, no certificado: debe verificarlo la QA y firmarlo JM.

## 2. Normativa

EN 1990 (EC0) y EN 1991 (EC1) con Anejo Nacional español; CTE DB-SE-AE; EN 1992-1-1 (EC2); EN 1993-1-1 (EC3); EN 1995-1-1 (EC5); EN 1997-1 (EC7); NCSE-02 (sismo).

## 3. Materiales (doc 02, APROBADO)

| Material | Resistencia | Coef. parciales |
|---|---|---|
| Acero S355 | fy=355 MPa | γM0=γM1=1,05; γM2=1,25 |
| HA-30 / B500S | fck=30 MPa; fyk=500 MPa | γc=1,5; γs=1,15 |
| CLT cassette | fm,k=24 MPa | γM=1,25; kmod=0,8 (clase serv. 1, media duración) |

## 4. Acciones y combinaciones (doc 02, APROBADO)

- **Permanentes:** PP por geometría; carga muerta forjado 2,0 kN/m²; cubierta 2,5 kN/m².
- **Sobrecargas:** oficinas B qk=2,0; sala formación C1 qk=3,0; cubierta H 0,4 kN/m².
- **Viento** zona C (qb=0,52 kN/m², terreno III); **nieve** sk=0,40 kN/m².
- **Sismo** ac=0,046 g (ab=0,04g, K=1,0, ρ=1,0, C=1,4386, S=1,1509).
- **ELU:** 1,35·G + 1,50·Q1 + 1,50·Σψ0i·Qi. **Sísmica:** G + AEd + Σψ2i·Qi. **ELS** según doc 02 §7-8. ψ por tabla doc 02 §7.

## 5. Sistema estructural (idealización desde el IFC)

Edificio alargado (11,5×40,5 m, alto 15 m + voladizos). **Núcleo lateral** formado por tres celosías de acero S355 (Cajón O, Cercha E, Alma C) y dos muros HA-30 (NC-Lab, NC-Vest). El **Cajón O** es una **viga-celosía vertical de gran canto (9,25 m) y luz 40,86 m** que apoya en los muros y resuelve los grandes voladizos; de ella cuelgan, vía dinteles de conexión (SHS 250×12), los **forjados CLT cassette** (nervio IPE 160 + losa CLT) en voladizo transversal de ≈6,2–6,5 m. La cimentación es profunda: 2 encepados sobre 10 pilotes perforados empotrados ≈3 m en la arenisca UG3.

## 6. Comprobaciones por subsistema (resumen)

### A. Forjado CLT cassette (EC5/EC3) — detalle en `05`
La costilla IPE 160 **no resiste sola** un voladizo de 6,55 m (u=4,5): se confirma que el gran vuelo lo toma la celosía Cajón O y la costilla actúa como **nervio entre apoyos (L≈3,86 m)**. Como nervio: flexión u=0,39, cortante u=0,09, flecha u=0,20. Tablero CLT a flexión local u=0,44. **Vibración f₁≈8,5 Hz (límite 8 Hz; u≈0,94, marginal).**

### B/C. Celosías y enlaces de acero (EC3) — detalle en `06`
Modelo IFC «v3 OPTIMIZADO (EC3)»: perfiles holgados. Cordón Cajón O SHS 180×8 (pandeo u=0,26), diagonal SHS 200×10 (u=0,39), montante SHS 120×6 (u=0,40 si arriostrado por planta). Dinteles SHS 250×12 (u≤0,12), conexión montante (u=0,23), tirante altillo SHS 80×8 (tracción u=0,18). **Punto crítico:** si el montante SHS 120×6 no estuviera arriostrado a pandeo a nivel de planta (L_cr=9,25 m), u=2,1 ❌ — requiere confirmación del arriostramiento real.

### D. Muros HA-30 (EC2 §12.6.5.2) — detalle en `07`
Flexocompresión con esbeltez: NC-Vest 488 kN/m, NC-Lab 458 kN/m → u=0,11 (muro arriostrado por forjados, l₀=3,08 m, Φ=0,72, N_Rd=4.332 kN/m). Cortante sísmico en plano u=0,15. Armadura mínima EC2 §9.6.

### E. Cimentación profunda (EC7 + EC2 §6.5) — detalle en `07`
Pilotes: D650 u=0,41; D450 u=0,57 (geotécnico, capacidad admisible SOCOTEC con FS). Encepados por bielas y tirantes: NC-Lab tirante 809 kN→18,6 cm² (6Ø20), biela u=0,24, nudo CCT u=0,46; NC-Vest tirante 864 kN→19,9 cm² (7Ø20), biela u=0,11, nudo CCT u=0,28.

### F. Sismo (NCSE-02, estático equivalente) — detalle en `07`
ac=0,046 g; cortante basal V≈385 kN (μ=2); tomado por muros+celosía con reserva amplia (u≤0,15). **El sismo no gobierna**, confirma la previsión del doc 02. Pendiente: verificación modal de torsión por irregularidad (S-F1).

## 7. Tabla maestra de aprovechamientos

| Subsistema | Elemento crítico | u_máx | Veredicto |
|---|---|---|---|
| A — CLT | Vibración forjado (f₁=8,5 Hz) | **0,94** | ✔ marginal |
| A — CLT | Costilla IPE 160 (nervio, flexión) | 0,39 | ✔ |
| B/C — acero | Montante SHS 120×6 (arriostrado) | **0,40** | ✔ |
| B/C — acero | Montante SHS 120×6 (**no arriostrado**) | 2,1 | ❌ ver S-B1 |
| B/C — acero | Diagonal SHS 200×10 (pandeo) | 0,39 | ✔ |
| D — muros | NC-Vest/NC-Lab (flexocompresión) | 0,11 | ✔ |
| E — pilotes | D450 (geotécnico EC7) | **0,57** | ✔ |
| E — encepados | NC-Lab nudo CCT | 0,46 | ✔ |
| F — sismo | cortante basal en muros | ≤0,15 | ✔ |

## 8. Veredicto provisional

Con las hipótesis aprobadas y la idealización adoptada, **todos los elementos cumplen (u ≤ 1,0)** salvo dos puntos que requieren **decisión/confirmación de JM**:

1. **Montante del Cajón O (SHS 120×6):** seguro **solo si está arriostrado a pandeo a nivel de cada planta** (l_cr≈3,08 m → u=0,40). Sin arriostrar (l_cr=9,25 m) **no cumple** (u=2,1). Confirmar el arriostramiento real (S-B1).
2. **Vibración del forjado CLT:** f₁≈8,5 Hz, marginal frente al límite de 8 Hz. Confirmar masa y rigidez reales del cassette (S-A vibración).

El modelo IFC, marcado «v3 OPTIMIZADO (EC3)», presenta aprovechamientos moderados (≈0,1–0,6) en la mayoría de elementos, coherente con un dimensionado previo afinado. El **diseño es razonable y defendible como predimensionado**.

## 9. Supuestos y simplificaciones (trazabilidad)

| id | Supuesto | Impacto | A resolver por |
|---|---|---|---|
| S-A1 | Nervio acero resiste solo (CLT no colabora) | conservador | detalle conexión cassette |
| S-A2 | Voladizo lo toma la celosía; costilla = nervio L≈3,86 m | gobierna A | planos de detalle / QA |
| S-B1 | Montantes arriostrados a pandeo por planta (3,08 m) | **crítico** | confirmar arriostramiento (JM) |
| S-D1 | Reparto carga vertical Vest/Lab 65/35 por superficie | medio | reacciones reales del núcleo |
| S-F1 | Sismo por estático equivalente (sin torsión modal) | bajo (ac pequeño) | modal espectral (QA) |
| Entorno | Sin PyNite/scipy: fórmulas cerradas, no solver matricial | medio | QA con su oráculo FEM |

## 10. Trazabilidad y reproducibilidad

- **Geometría:** parseada del IFC por texto STEP (perfiles, longitudes de extrusión, placements).
- **Cálculo:** Python puro + fórmulas EC documentadas, alineadas con `barras/verificacion.py`, `barras/perfiles_db.py`, `laminas/ec2_muro.py`, `bielas-tirantes/ec2_strut_tie.py` del motor. Script: `outputs/decopak_predim.py`.
- **Versiones:** `versions.lock=0.0.0` → resultados **NO reproducibles/anclados** hasta el primer tag del núcleo (tarea N1.1). Marcados como «calculados sobre versión no anclada».
- **Oráculo QA:** ver `08_candidatos_golden.md` (analítico + PyNite). JM fija tolerancias.

## 11. Conclusión

Predimensionado **favorable** con dos puntos abiertos para JM (arriostramiento del montante y vibración del forjado). Procede: (a) verificación QA independiente con solver FEM sobre los nudos reales del IFC; (b) resolución de los supuestos S-A2/S-B1/S-D1/S-F1; (c) anclaje de versiones; (d) firma por técnico competente.

---
**Aviso:** documento de PREDIMENSIONADO. Debe ser revisado y firmado por un técnico competente. Pendiente de verificación QA independiente y firma de JM. La IA no firma ni certifica.

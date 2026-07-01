# Decopak HQ — Síntesis geotécnica para el cálculo

- **Fuente:** Informe geotécnico SOCOTEC `Deco-Bac-ZZZ-ZZZ-INF-TGS-001-Geotecnico-S7-0100.PDF` (MEMORIA TÉCNICA, nov. 2023).
- **Datos de partida confirmados por JM (2026-06-24):** cota de cimentación **+152,00 msnm**; perfil geotécnico aplicable al edificio **CC**; a la cota +152 se inicia **UG2**; a la cota **+148** se inicia **UG3**.
- **Estado:** base de cálculo para subsistemas E (cimentación) y F (sismo). Propuesta pendiente de verificación QA + firma JM.

---

## 1. Datum / relación de cotas

| Referencia | Cota local (modelo IFC) | Cota absoluta (msnm) |
|---|---|---|
| PB (planta baja) | 0,00 | +153,50 |
| Cimentación (encepados) | −1,50 | +152,00 |
| Inicio UG2 | −1,50 | +152,00 |
| Inicio UG3 | −5,50 | +148,00 |
| Punta de pilotes (IFC) | −8,50 | +145,00 |

→ Bajo la cota de cimentación: **≈ 4 m de UG2** (152→148) y **UG3** por debajo (potencia > 20 m). Los pilotes empotran **≈ 3,0 m en UG3** (de −5,5 a −8,5 local).

## 2. Perfil estratigráfico (bajo cota de cimentación +152)

| Unidad | Descripción | Tramo (msnm) | Clasif. sísmica |
|---|---|---|---|
| UG2 | Arcilla limosa parcialmente litificada / lutita alterada (M:III-V, R:0-1) | +152 → +148 | Terreno **Tipo III** |
| UG3 | Arenisca de grano muy fino roja (M:II-IV, R:1-2) — **estrato portante** | < +148 | Terreno **Tipo II** |

*(UG0 relleno y UG1 arcilla quedan por encima de la cota de excavación +152; no aplican como apoyo. UG0 «no apoyar».)*

## 3. Parámetros geotécnicos

**UG2 — Arcilla limosa parc. litificada / lutita alterada**

| Parámetro | Valor |
|---|---|
| Densidad aparente ρ | 2,00 – 2,14 g/cm³ |
| Cohesión efectiva c' | 0,30 – 0,45 kg/cm² (≈ 30 – 44 kPa) |
| Ángulo de rozamiento φ' | 28 – 32° |
| Módulo de elasticidad E | 650 – 1000 kg/cm² (≈ 65 – 98 MPa) |
| Resistencia compresión simple Qu | 1,47 – 2,66 kg/cm² |

**UG3 — Arenisca de grano muy fino (roca blanda, estrato portante)**

| Parámetro | Valor |
|---|---|
| Densidad aparente ρ | 2,07 – 2,30 g/cm³ |
| Resistencia compresión simple Qu | 2,94 – 7,44 kg/cm² |
| Presión límite PL | > 80 kg/cm² |
| Clasificación | Roca |

## 4. Nivel freático

Detectado profundo: cota **+142,6 a +144,6 msnm** (≈ 7,9 – 11,6 m de profundidad). **Por debajo de la cota de cimentación (+152)** → sin agua en la base de los encepados. Las puntas de pilote (+145) pueden quedar próximas o bajo el nivel freático; tenerlo en cuenta en la ejecución. Agua **no agresiva** frente al hormigón (EHE-08).

## 5. Cimentación profunda — pilotes (datos de diseño)

- **Tipo:** pilote perforado / «in situ» de hormigón → factor Kf = 0,75; f = 1,0.
- **Empotramiento:** mínimo **6 × diámetro** en la unidad portante; si es menor (potencia escasa), la carga de punta se toma como la media de la zona 3D bajo punta (activa) y 6D sobre (pasiva). **Atención:** para D650, 6D = 3,9 m > los ≈ 3,0 m disponibles en UG3 → aplicar el promedio de zona.
- **Cargas admisibles unitarias (Tabla 25, pilote in situ; FS ya aplicados):**

| Unidad | Fuste adm. (kg/cm²) | Punta adm. (kg/cm²) | ≈ Fuste (kPa) | ≈ Punta (MPa) |
|---|---|---|---|---|
| UG2 | 0,631 | 22,805 | ≈ 62 | ≈ 2,24 |
| UG3 | 1,000 | 39,515 | ≈ 98 | ≈ 3,88 |

- **Capacidad orientativa por punta en UG3** (R_p,adm = q_p,adm · A_punta):
  - **D650** (A = 0,332 m²): ≈ **1.290 kN** por punta (a ajustar por el promedio de zona si empotramiento < 6D).
  - **D450** (A = 0,159 m²): ≈ **615 kN** por punta.
  - Sumar la **resistencia por fuste** en el tramo embebido (UG2 + UG3) por elemento.
- **Grupos del modelo:** Encepado NC-Vest (6 × D650) y Encepado NC-Lab (4 × D450). Verificar efecto grupo y reparto.

## 6. Sismo (confirma la hipótesis H5)

| Parámetro | Valor (geotécnico) |
|---|---|
| Aceleración sísmica básica ab | 0,04 g |
| Coef. de contribución K | 1,0 |
| Coef. de riesgo ρ (importancia normal) | 1,0 |
| Coef. de tipo de suelo C | 1,4386 |
| Coef. de amplificación S | 1,1509 |
| **Aceleración de cálculo ac = S·ρ·ab** | **0,0460 g** |

→ Coincide con la hipótesis propuesta y aprobada. Se mantiene la recomendación de **comprobar la combinación sísmica** (núcleos arriostrados de acero + muros HA), con ac = 0,046 g.

## 7. Para el informe de QA (trazabilidad)

```
fuente:    Informe geotécnico SOCOTEC S7 (nov-2023)
datum:     cota cim. +152 = Z local -1,5; perfil CC; UG2 +152→+148; UG3 <+148
portante:  UG3 arenisca (roca blanda); pilotes perforados Kf=0,75
pilotes:   UG3 punta 39,515 kg/cm² / fuste 1,00 kg/cm² (FS aplicado, Tabla 25, D45)
sismo:     ab=0,04g, K=1,0, C=1,4386, S=1,1509, ρ=1,0 -> ac=0,046g
freático:  +142,6..+144,6 (bajo cota cim.); agua no agresiva
estado:    base de cálculo (propuesta) -> pendiente QA + firma JM
```

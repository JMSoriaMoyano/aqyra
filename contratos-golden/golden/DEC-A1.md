# Caso golden DEC-A1 — Costilla cassette IPE 160 + tablero CLT (flexión + flecha + vibración)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem / motor de cálculo).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).
> Un fallo no se resuelve aflojando tolerancia ni editando el esperado — solo arreglando el código.

```
id:           DEC-A1
contrato:     C5 v0
proyecto:     Decopak HQ (IFC #1857)
estado:       SEMILLA — pendiente de ratificación de valores/tolerancias por JM
              y de RE-EJECUCIÓN con oráculo PyNite (P3)
```

## Entrada

```
elemento:     Costilla/nervio de cassette IPE 160 (S355) + tablero CLT, biapoyado L = 3,86 m
seccion:      IPE 160 — b=82, h=160, t_w=5,0, t_f=7,4 mm; I_y de catálogo
acciones:     w_d = 8,80 kN/m  (ELU: 1,35·3,63 + 1,50·2,60)
              w_k = 6,23 kN/m  (ELS característica)
              w_cuasi = 4,41 kN/m
masa lineal:  m = 450 kg/m (RATIFICADO JM 2026-06-26: masa cuasipermanente realista, CLT + carga muerta;
              NO la optimista 346 del build). El recálculo de la sección mixta (Opción A) debe usar esta masa.
norma:        EC3 6.2.5 (resistencia nervio acero) · EC0 7.4 (flecha) · EC5 §7.3 (vibración)
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo) | Tolerancia | Criterio normativo |
|---|---|---|---|
| M_Ed (flexión) | 16,4 kN·m | ±2 % | — |
| u_M = M_Ed/M_c,Rd | 0,39 | ±2 % | ≤ 1,0 → cumple |
| δ (flecha, ELS característica) | **9,87 mm** | ±2 % | ≤ L/300 = 12,9 mm → cumple (u=0,77) |
| f₁ (frecuencia propia) | **6,7 Hz** (m≈450) · **7,7 Hz** (m=346) | ±5 % | ≥ 8 Hz (EC5 §7.3) → **NO CUMPLE** |

Fórmulas del oráculo (viga biapoyada): M = wL²/8 · δ = 5wL⁴/384EI · f₁ = (π/2)·√(EI/(m·L⁴)).

## Oráculo

```
oraculo:      analitico (fórmulas cerradas EC, derivadas independientemente en numpy)
fuente:       qa/informes/qa_normativa.py  ·  informe qa/informes/QA_DEC-A1.md (2026-06-24)
pendiente:    confirmación con PyNite (P3) — viga biapoyada, trivial, baja prioridad de re-ejecución
```

## Tolerancia

```
M_Ed, u_M, δ:  ±2 %
f₁:            ±5 %
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia y nota de defecto abierto (DEC-A1, NO APTO)

> El build declaró **δ=2,6 mm** y **f₁=8,5 Hz** → APTO. La QA detectó **dos errores de aritmética del build**, ambos en los ELS gobernantes del voladizo CLT:
> 1. **Flecha:** la propia fórmula del build evalúa a 9,87 mm (×3,8). El valor correcto cumple L/300, pero el número del build es erróneo.
> 2. **Vibración:** la fórmula del build da 7,66 Hz con su masa (346 kg/m), no 8,5 Hz; con masa realista (≈450 kg/m) baja a 6,7 Hz. **En ambos casos f₁ < 8 Hz → INCUMPLE EC5 §7.3.**
>
> Este es un **defecto de diseño**, no solo aritmético: la vibración no la arregla recalcular bien, sino cambiar el modelo/rigidez. **P2 / decisión de JM** (ver `qa/informes/QA_DEC-A1.md` §6 y `golden/DEC-A1_recalculo_P2.md`): sección mixta acero-CLT con conexión, más canto/rigidez, o justificación por criterio de aceleración.

```
responsable:  JM
veredicto build N1.1:  NO APTO (δ y f₁ fuera de tolerancia)
```

## Decisión de JM (2026-06-26) — Opción A: sección mixta acero-CLT

> **JM decide resolver la vibración por SECCIÓN MIXTA acero-CLT con conexión (Opción A).**
> El panel CLT pasa a contar como ala colaborante mediante conexión a rasante con la costilla IPE 160.
>
> **Objetivo para el build:** alcanzar **EI_efectiva ≥ 1,42 × EI_acero** (de 1,82 → ≥ 2,59 MN·m²) para que,
> con la **masa realista (≈450 kg/m)**, resulte **f₁ ≥ 8 Hz** (EC5 §7.3). Una conexión efectiva al CLT
> suele dar EI de 2–4×, así que hay margen. Corregir además la flecha al valor correcto (9,87 mm; sigue
> cumpliendo L/300).
>
> **Re-baseline del golden (pendiente):** al cambiar la sección a mixta, los valores `esperado` de δ y f₁
> de esta ficha se **recalcularán para la sección mixta definitiva** y los **ratifica JM** (vía PR con traza);
> el criterio de aceptación f₁ ≥ 8 Hz no cambia. La ficha pasará de NO APTO a APTO solo tras re-verificar
> con el oráculo **PyNite** (P3). Hasta entonces, el `esperado` actual documenta el diseño no-mixto que falla.
>
> Detalle y opciones descartadas: `DEC-A1_recalculo_P2.md`.

---

## Re-baseline P2/P3 (sección mixta) — PROPUESTA de la IA, pendiente de ratificación JM

> Ejecutado 2026-06-26 en entorno con **PyNite 2.0.2**. Corrige el build a la Opción A y re-verifica.
> **La IA propone el nuevo `esperado`; SOLO JM lo ratifica (PR con traza).** El criterio f₁ ≥ 8 Hz no cambia.

**Sección mixta definitiva (modelo de cálculo):** IPE 160 (S355) + ala colaborante CLT, ancho eficaz
b_eff = 600 mm, panel 160 mm (capas L40-T20-L40-T20-L40, E0,mean = 11.000 MPa), conexión a rasante
con tornillos d=8 mm @ 150 mm. EI_eff por **γ-method EN 1995-1-1 Anexo B**.

| Magnitud | Esperado NO-mixto (documenta el fallo) | **Esperado mixto (re-baseline propuesto)** | Tol. | Oráculo |
|---|---|---|---|---|
| EI_eff / EI_acero | 1,00 (1,82 MN·m²) | **2,48 (4,53 MN·m²)** ≥ objetivo 1,42× (2,59) | — | γ-method EC5 |
| δ (flecha ELS car.) | 9,87 mm | **3,98 mm** (≤ L/300 = 12,9 → u=0,31) | ±2 % | **PyNite** |
| f₁ (vibración, m=450) | 6,71 Hz **(NO CUMPLE)** | **10,57 Hz** (≥ 8 Hz → **CUMPLE**) | ±5 % | analítico |
| u_M (flexión, EC3 6.2.5) | 0,39 | 0,39 (gobernada por el acero, sin cambio) | ±2 % | analítico |

**Veredicto re-verificado:** **NO APTO → APTO** (la flecha cumple y f₁ = 10,57 Hz ≥ 8 Hz con la masa
realista 450 kg/m). Verificado por `qa/run_golden.py` (PyNite) → **VERDE**. Evidencia:
`qa/informes/golden_run_report.json` y `golden_run_consola.txt`.

> Margen: incluso sin contar la eficiencia de la conexión (suma de rigideces, γ→0) EI = 3,83 MN·m²
> daría f₁ ≈ 9,7 Hz; el resultado es robusto. El dimensionado fino de la conexión a rasante pertenece al
> hilo de ingeniería, no al de gobierno. **Pendiente: firma de JM del nuevo `esperado`.**

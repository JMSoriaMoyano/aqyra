# DEC-A1 · P2 — Recálculo del nervio IPE 160 + CLT y opciones de corrección

> **Qué es:** la corrección del defecto abierto DEC-A1 (paso P2 de `FOCO6_cierre_N1.1.md`).
> La IA recalcula y cuantifica las opciones; **la elección del modelo es de JM.**
> Cálculo reproducible en `qa/informes/` (fórmulas cerradas EC, numpy). Predimensionado a revisar/firmar por técnico competente.

## 1. Recálculo (verificado, fórmulas cerradas)

Nervio biapoyado **IPE 160 (S355)**, L=3,86 m, I_y=869 cm⁴, E=210 GPa, w_k=6,23 kN/m.

| Magnitud | Build N1.1 | Recálculo verificado | Veredicto |
|---|---|---|---|
| Flecha δ (ELS car.) = 5wL⁴/384EI | 2,6 mm | **9,87 mm** (×3,8) | error aritmético del build; el valor correcto **cumple** L/300=12,9 mm (u=0,77) |
| f₁ = (π/2)·√(EI/mL⁴), m=346 kg/m | 8,5 Hz | **7,66 Hz** | < 8 Hz → **NO CUMPLE** EC5 §7.3 |
| f₁, m≈450 kg/m (CLT+muerta realista) | — | **6,71 Hz** | < 8 Hz → **NO CUMPLE** |

**Conclusión:** la flexión (u_M=0,39) está bien. La flecha es solo un error de número (el correcto cumple).
**El problema de fondo es la vibración:** con la rigidez actual f₁ queda por debajo de 8 Hz tanto con la
masa del build como con la realista. **No se arregla recalculando: hay que cambiar el diseño** (o justificar
por respuesta). Esa es la decisión de JM.

## 2. Opciones para llevar f₁ ≥ 8 Hz (masa realista m=450 kg/m)

| Op. | Solución | Resultado | Coste / observación |
|---|---|---|---|
| **A** | **Sección mixta acero-CLT con conexión** (contar el panel como ala colaborante) | Necesita EI_efectiva ≥ **1,42× EI_acero** (de 1,82 → 2,59 MN·m²). Una conexión efectiva al CLT suele dar 2–4× → **margen sobrado** | la más eficiente; exige diseñar y comprobar la conexión (rasante) y rehacer DEC-A1 como caso mixto (EC5/EC4-análogo) |
| **B** | **Subir el perfil** (más canto/rigidez) | **IPE 180 → f₁=8,26 Hz** (justo); **IPE 200 → 10,0 Hz** (holgado); IPE 220 → 12,0 Hz | simple y robusto; IPE 200 recomendable por margen. +peso de acero despreciable frente al CLT |
| **C** | **Reducir luz / apoyo intermedio** | L_máx=3,54 m para 8 Hz; un apoyo a centro (L/2) → ~27 Hz | depende de la retícula; cambia el modelo estructural del forjado |
| **D** | **Justificar por respuesta** (EC5 §7.3.3) | con f₁=6,7 Hz (>4,5 Hz) se admite verificar por velocidad de impulso unidad v ≤ b^(f₁·ζ−1) y aceleración a_rms, en lugar del umbral de 8 Hz | no cambia la estructura, pero exige fijar amortiguamiento ζ y parámetros a,b, y aceptar el criterio de confort; más débil para uso de oficinas |

## 3. Recomendación de la IA (a ratificar por JM)

Para un voladizo/forjado ligero de oficina, lo más limpio y defendible es **Opción A (sección mixta
con conexión)** o, si se quiere evitar el diseño de la conexión, **Opción B con IPE 200** (margen a 10 Hz).
La Opción D queda como respaldo si la geometría impide subir rigidez. **Decisión de JM** (DEC-A1).

## 3 bis. DECISIÓN DE JM (2026-06-26): Opción A — sección mixta acero-CLT

> **Elegida la Opción A.** El CLT cuenta como ala colaborante por conexión a rasante con la IPE 160.
> **Objetivo cuantitativo para el build:** EI_efectiva ≥ **1,42 × EI_acero** (≥ 2,59 MN·m²) para f₁ ≥ 8 Hz
> con masa realista ≈450 kg/m. Opciones B/C/D quedan descartadas para este caso (documentadas por trazabilidad).
> Esto cierra la compuerta de decisión de DEC-A1; el dimensionado fino de la conexión mixta pertenece al
> hilo de ingeniería, no al hilo de gobierno.

## 4. Qué hay que hacer en el build tras la decisión

1. **Corregir la flecha** a δ≈9,87 mm (sigue cumpliendo L/300; el número debe ser correcto).
2. **Implementar la opción elegida** y recalcular f₁ con la masa realista (≈450 kg/m), no la optimista.
3. **Re-verificar DEC-A1** contra esta ficha golden con el oráculo PyNite (P3). Solo entonces pasa de NO APTO a APTO.

> Regla: el `esperado` y la tolerancia de `DEC-A1.md` no se tocan para «aprobar»; se corrige el código/diseño
> hasta que el motor reproduzca, para la solución elegida, una f₁ ≥ 8 Hz real (o la justificación de la Op. D).

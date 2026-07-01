# C5 — Puntos abiertos 4–6: implicaciones y opciones para cerrarlos

**Anexo de decisión del contrato C5** · 2026-06-26 · la IA detalla; **decide JM**.

> Los puntos 1–3 quedaron cerrados (schemas, Psets de resultado, alcance lámina). Estos tres no son de
> redacción: cambian **qué calcula y reporta el motor** y **cómo se mide el margen**. Para cada uno: qué
> está en juego, las opciones reales y una recomendación de la IA (a ratificar).

---

## Punto 4 — Formato EC7 (capacidad geotécnica) · afecta a DEC-E2 y a O4

**Qué está en juego.** Hoy el build mezcla formatos: usa **capacidad admisible** (SOCOTEC, con factor de
seguridad global ya aplicado) y la compara con **cargas de servicio** (N_ELU/1,4). Coincide con el oráculo
al 0,04 %, pero no es el formato riguroso de EC7. La elección **no cambia que el pilote cumple con holgura**
(u≈0,41); cambia **el número de margen que se reporta** y la coherencia del contrato.

**Opciones.**

| Op. | Formato | Cómo | Implicación |
|---|---|---|---|
| **4a** | **Admisible (estado actual)** | R_adm SOCOTEC vs cargas de servicio | simple, lo que ya hay; pero mezcla ELU/servicio — débil para auditoría EC7 estricta |
| **4b** | **Parcial EC7, Enfoque DA (recomendado)** | E_d en ELU vs R_d con γ_R parciales; en España suele usarse **DA combinación 2** (γ sobre acciones y resistencias) | riguroso y trazable; obliga a declarar γ_R de punta/fuste y el set de coeficientes; re-expresa O4 |
| **4c** | **Doble reporte** | dar ambos: admisible (continuidad con SOCOTEC) + parcial (rigor EC7) | máxima trazabilidad; más trabajo y dos números que conciliar |

**Implicación en el contrato/golden.** Si se elige 4b/4c hay que: (i) añadir a la entrada los **γ_R** y el
enfoque DA en `verificacion`; (ii) re-expresar el `aprovechamiento` de DEC-E2 con E_d/R_d; (iii) re-ratificar
la tolerancia (±5 % se mantiene). No bloquea N1.1 si se acepta documentar el formato elegido.

**Recomendación IA:** **4b (parcial, DA2 español)** como formato oficial de C5, conservando el dato admisible
SOCOTEC como referencia en la trazabilidad. Es lo defendible ante tercero y fija un único criterio para todo el motor.

---

## Punto 5 — Sismo (modal espectral con torsión) · S-F1, O-4/O-5 · afecta a O3/O4

**Qué está en juego.** Falta el caso sísmico. En Decopak la aceleración es **baja (ac≈0,046 g)** y es
improbable que gobierne, pero "improbable" no es "verificado". Además el depósito añade dos efectos propios:
**empuje hidrodinámico** del agua (Westergaard/Housner) y **térmica**, hoy en gate abierto (O-4/O-5 de DEC-S1).

**Opciones.**

| Op. | Alcance sísmico de C5 v0 | Implicación |
|---|---|---|
| **5a** | **Diferir el sismo fuera de N1.1** (anzuelo): declarar S-F1 como caso no cubierto por v0, justificar cualitativamente que con ac=0,046 g no gobierna | cierra N1.1 antes; honesto si se documenta el límite; el motor no reporta sismo todavía |
| **5b** | **Fuerza lateral equivalente** (método simplificado EC8) | barato; suficiente para estructuras regulares de baja sismicidad; da un O4 sísmico aproximado |
| **5c** | **Modal espectral completo con torsión** (EC8) + hidrodinámico para el depósito | riguroso y general; requiere masa modal, espectro, q de ductilidad, combinación direccional y, en depósitos, masas impulsiva/convectiva |

**Implicación en el contrato/golden.** El **modal ya está en O3** (lo ejercita DEC-A1). Para 5b/5c hay que
añadir: espectro y parámetros EC8 en la entrada, combinación sísmica (ya prevista en el schema) y, para el
depósito, el modelo hidrodinámico. **Habría que sembrar una golden sísmica** (no existe oráculo sísmico hoy →
trabajo nuevo, y PyNite hace modal pero no el espectral completo de serie).

**Recomendación IA:** **5a para N1.1** (diferir el sismo con justificación de baja sismicidad documentada),
y abrir **5c como minor posterior** (C5 v0.x → v0.(x+1)) con su propia golden. Meter el espectral completo en
N1.1 retrasa el piloto del gobierno sin necesidad técnica en este emplazamiento.

---

## Punto 6 — NDP del Anejo Nacional español · afecta a la reproducibilidad de todo el motor

**Qué está en juego.** Cada Eurocódigo tiene **Parámetros de Determinación Nacional** (NDP) que fija el Anejo
Nacional. Si no se fijan explícitamente, dos runs "iguales" pueden diferir y la golden deja de ser un blanco
estable. Hoy las fichas los dan por buenos implícitamente; el schema ya tiene `verificacion.ndp[]` con estado
`confirmado | confirmar_AN`.

**NDP que tocan las 7 golden (lista mínima a confirmar):**

| Norma | NDP relevante | Uso en golden |
|---|---|---|
| EC0 | ψ (simultaneidad), límites de flecha (L/300…) | DEC-A1 (flecha), combinaciones |
| EC1 | categorías de uso, coef. de nieve/viento, **LM1** (α_Q, α_q) | acciones, DEC-S1 (tándem) |
| EC2 | γ_C, γ_S, límite w_k de fisuración, α_cc | DEC-E1, DEC-S1 |
| EC3 | γ_M0, γ_M1 (=1,05 usado) | DEC-B1/B2/B4 |
| EC5 | umbral de vibración f₁≥8 Hz, k_def, ζ | DEC-A1 |
| EC7 | γ_R, enfoque DA (ligado al punto 4) | DEC-E2 |
| EC8 | a_gR por zona, S, q (ligado al punto 5) | (sismo, diferido) |

**Opciones.**

| Op. | Cómo tratar los NDP | Implicación |
|---|---|---|
| **6a** | **Fijar ahora los valores del AN español** en una tabla de C5 (con cita del AN) y marcar `confirmado` | da reproducibilidad inmediata; exige que JM valide cada valor una vez |
| **6b** | **Parametrizar y dejar `confirmar_AN`** caso por caso | flexible (otros AN en el futuro) pero la golden no congela hasta confirmarlos |
| **6c** | **Mixto (recomendado):** fijar como `confirmado` los NDP que ya usan las 7 golden (lista de arriba) y dejar `confirmar_AN` los del sismo (punto 5) y EC7-DA (punto 4) hasta cerrarlos | congela lo que N1.1 necesita sin bloquear; coherente con diferir sismo |

**Implicación en el contrato/golden.** Con 6c, el `verificacion.ndp[]` de cada ficha queda `confirmado`
salvo sismo/EC7-DA. Es el mínimo para que la golden sea un blanco estable y el sello de dos llaves tenga sentido.

**Recomendación IA:** **6c**. Te preparo, si quieres, la **tabla de NDP español confirmados** (valores + cita
del AN) para que la ratifiques de una vez; es el último flanco para que las 7 fichas sean ratificables.

---

## Resumen para decidir

| Punto | Recomendación IA | Bloquea N1.1 si no se cierra |
|---|---|---|
| 4 EC7 | 4b parcial DA2 (+ admisible en traza) | No — basta documentar el formato elegido |
| 5 Sismo | 5a diferir con justificación; 5c en minor posterior | No — si se documenta la baja sismicidad |
| 6 NDP | 6c mixto (confirmar lo de las 7 golden ya) | **Sí en parte** — sin NDP fijados la golden no congela |

> Siguiente paso si validas: cierro el punto 6 con la tabla de NDP español y ajusto DEC-E2 al formato EC7 que elijas.

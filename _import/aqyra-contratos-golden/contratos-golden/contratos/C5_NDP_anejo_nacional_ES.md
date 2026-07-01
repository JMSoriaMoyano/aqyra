# C5 v0 — Tabla de NDP del Anejo Nacional español (para ratificación de JM)

**Anexo del contrato C5** · zona protegida · 2026-06-26 · **la IA propone; SOLO JM ratifica** (vía PR con traza).

> ✅ **RATIFICADO por JM (2026-06-26):** los NDP marcados `confirmado` quedan firmes; **α_cc = 1,0** (EC2) fijado.
> Pendientes de emplazamiento/ejecución los `confirmar_AN` restantes (nieve/viento, ζ y clase de servicio EC5,
> límite de flecha según CTE, y todo EC8 diferido).

> Cierra el punto abierto **6 (opción 6c)**: fija los Parámetros de Determinación Nacional (NDP) que usan
> las 7 fichas golden, para que la golden sea un **blanco estable**. Los del **sismo (EC8) quedan
> `confirmar_AN`** (diferido, decisión 5a). Es el espejo del campo `verificacion.ndp[]` del schema.
>
> **Aviso (gobierno de dos llaves):** estos valores son una **propuesta** de la IA a partir de los Anejos
> Nacionales españoles citados. **No están certificados.** JM debe verificarlos contra el texto oficial
> (BOE / AN UNE-EN) antes de firmar. `estado = confirmado` aquí significa *"propuesto como confirmado,
> pendiente de tu visto"*; `confirmar_AN` significa *"la IA no lo fija; lo decides tú"*.

## 1. EC0 — Bases de cálculo (AN/UNE-EN 1990)

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| γ_G (permanente, desfav. / favor.) | 1,35 / 1,00 | todas las combinaciones ELU | confirmado |
| γ_Q (variable, desfav.) | 1,50 | todas las combinaciones ELU | confirmado |
| ψ₀ / ψ₁ / ψ₂ — uso oficinas (categoría B) | 0,7 / 0,5 / 0,3 | DEC-A1 (cuasiperm.), combinaciones | confirmado |
| Límite de flecha (ELS) | L/300 (total) | DEC-A1 (δ=9,87 ≤ 12,9 mm) | **confirmar_AN** (límite de proyecto; CTE DB-SE puede regir) |

## 2. EC1 — Acciones (AN/UNE-EN 1991 · CTE DB-SE-AE · IAP-11)

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| Sobrecarga de uso por categoría | EN 1991-1-1 AN / CTE DB-SE-AE | acciones | confirmado |
| Nieve / viento | CTE DB-SE-AE (zona, altitud) | acciones | **confirmar_AN** (depende de emplazamiento) |
| **LM1 (tándem 600 kN, huella 3,1×2,3)** | **IAP-11** (2×300 kN/eje + UDL), no EN 1991-2 AN | DEC-S1 (cubierta) | confirmado (origen IAP-11) |

## 3. EC2 — Hormigón (AN/UNE-EN 1992-1-1 · EN 1992-3 depósitos)

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| γ_C (persistente/transitoria) | 1,50 | DEC-E1, DEC-S1 | confirmado |
| γ_S (persistente/transitoria) | 1,15 | DEC-E1, DEC-S1 | confirmado |
| α_cc (resistencia a compresión sostenida) | 1,00 | f_cd de DEC-E1/S1 | **confirmado** (RATIFICADO JM 2026-06-26) |
| w_max — clase exposición normal (XC) | 0,30 mm | (general) | confirmado |
| w_max — estanqueidad depósito (EN 1992-3, clase 1) | 0,20 mm | DEC-S1 (w_k=0,169) | confirmado |

## 4. EC3 — Acero (AN/UNE-EN 1993-1-1)

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| **γ_M0** (resistencia de secciones) | **1,05** | DEC-B1/B2/B4 | confirmado (AN ES; difiere del 1,00 recomendado EN) |
| **γ_M1** (resistencia a inestabilidad/pandeo) | **1,05** | DEC-B1/B2/B4 | confirmado |
| γ_M2 (resistencia a rotura/uniones) | 1,25 | (uniones, futuro) | confirmado |
| Curva de pandeo SHS conformado en frío (S355) | curva b (α=0,34) | DEC-B1/B2/B4 | confirmado |

## 5. EC5 — Madera/CLT (AN/UNE-EN 1995-1-1)

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| Umbral de vibración f₁ | ≥ 8 Hz | DEC-A1 (gobierna el NO APTO) | confirmado |
| Amortiguamiento modal ζ | 0,01 | DEC-A1 (criterio respuesta, Op. D descartada) | **confirmar_AN** |
| k_def / k_mod (clase de servicio) | según clase de servicio | DEC-A1 (sección mixta, Op. A) | **confirmar_AN** (fijar clase de servicio del forjado) |

## 6. EC7 — Geotecnia (AN/UNE-EN 1997-1) · **formato oficial de C5 = parcial DA2 (decisión 4b)**

España adopta el **Enfoque de Proyecto 2 (DA-2)** para todas las actuaciones geotécnicas, salvo
estabilidad global/taludes (**DA-3**). DA-2 = acciones **A1** + resistencias **R2**.

| NDP | Valor propuesto | Usado en | Estado |
|---|---|---|---|
| Enfoque de proyecto | **DA-2** (DA-3 estabilidad global) | DEC-E2 | confirmado |
| γ_b — resistencia por **punta** (pilotes, R2) | **1,35** | DEC-E2 | confirmado |
| γ_s — resistencia por **fuste** (pilotes, R2) | **1,10** | DEC-E2 | confirmado |
| γ_t — resistencia **total/combinada** (R2) | **1,25** | DEC-E2 | confirmado |
| γ_Rd — coeficiente de **modelo** | **1,40** | DEC-E2 | confirmado |
| Acciones (set A1): γ_G / γ_Q | 1,35 / 1,50 | DEC-E2 (E_d en ELU) | confirmado |

> **Conservar trazabilidad:** el dato **admisible SOCOTEC** (R_adm=2.397 kN) se mantiene como referencia en la
> traza de DEC-E2, pero el **veredicto oficial** se expresa en DA-2 (E_d ELU vs R_d con γ_R). Ver `golden/DEC-E2.md`.

## 7. EC8 — Sismo (AN/UNE-EN 1998 · NCSE) — **DIFERIDO (decisión 5a)**

| NDP | Estado |
|---|---|
| a_gR por zona, S, q (ductilidad), combinación sísmica, masas hidrodinámicas (depósito) | **confirmar_AN** — fuera del alcance de C5 v0; se abre en minor posterior (5c) con su propia golden |

---

## 8. Resumen de estado

- **`confirmado` — RATIFICADO JM 2026-06-26:** EC0 γ/ψ, EC1 LM1 (IAP-11), EC2 γ_C/γ_S/w_max/**α_cc=1,0**,
  EC3 γ_M0/γ_M1/γ_M2/curva b, EC5 f₁≥8 Hz, EC7 DA-2 completo.
- **`confirmar_AN` (pendiente de emplazamiento/ejecución):** límite de flecha EC0 (según CTE),
  nieve/viento por emplazamiento (Rubí, Barcelona), ζ y clase de servicio EC5, todo EC8 (sismo, diferido).

> ✅ Con los `confirmado` **ratificados por JM**, las **7 fichas golden quedan ratificadas** y la golden
> puede congelar (último flanco del punto 6). Los `confirmar_AN` no bloquean N1.1 salvo que afecten a una
> ficha concreta; ninguna de las 7 depende hoy de ellos (sismo diferido; nieve/viento ya en las acciones del proyecto).

## Fuentes (Anejos Nacionales citados)

- [AN/UNE-EN 1997-1 (EC7) — MITMA](https://cdn.mitma.gob.es/portal-web-drupal/carreteras/normativa/AN_UNE-EN%201997-1.pdf)
- [AN/UNE-EN 1993-1-1 (EC3) — MITMA](https://cdn.mitma.gob.es/portal-web-drupal/carreteras/normativa/AN_UNE-EN%201993-1-1.pdf)
- [Bases del Anejo Nacional Español del EC-7 — Hormigón y Acero](https://www.elsevier.es/es-revista-hormigon-acero-394-articulo-bases-del-anejo-nacional-espanol-S043956891450006X)
- [Coeficientes parciales EC7 Anejo Nacional España — Sismica Institute](https://sismica-institute.com/coeficientes-parciales-eurocodigo-7-geo5-espana/)

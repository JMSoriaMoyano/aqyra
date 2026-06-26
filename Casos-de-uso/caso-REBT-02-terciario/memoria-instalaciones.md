# Memoria de instalaciones — Caso REBT-02: instalación eléctrica terciaria/industrial

> Predimensionado/asistencia. **Debe ser revisado y firmado por técnico competente
> (Ingeniero de Caminos).** Los valores no determinados (NDP) se marcan `[confirmar AN]`.
> Disciplina `instalaciones`, vertical eléctrico (REBT), PT 4.5 (Ola 4).

## 1. Objeto y alcance

Dimensionado y comprobación de una instalación eléctrica de **local terciario /
industrial** con línea general trifásica a un subcuadro y derivaciones a receptores
(luminarias, toma de uso general y un motor trifásico), de extremo a extremo: IFC MEP
(`ELECTRICAL`) → modelo neutro de red → bases de demanda → solver eléctrico →
verificación → write-back al IFC. Se comprueban **caídas de tensión** e **intensidades
admisibles**.

## 2. Normativa y referencias

- **REBT** (RD 842/2002) y sus ITC.
- **ITC-BT-10** — previsión de cargas.
- **ITC-BT-44** — receptores de alumbrado; **ITC-BT-47** — motores (la línea de un
  motor se dimensiona al 125 % de su intensidad a plena carga) `[confirmar AN]`.
- **ITC-BT-19** — caídas de tensión e intensidades admisibles de los conductores.

Valores por defecto NDP `[confirmar AN]`; el dato del proyecto (IFC) prevalece.

## 3. Descripción de la red

Red **radial (en árbol)**: **cuadro general** (fuente) → **línea general** (LGA) al
**subcuadro** → cuatro derivaciones. Topología leída del IFC por el parser MEP de
`iso19650-openbim`: **6 nodos, 5 tramos, 4 terminales, 1 fuente**. Conductores de
**cobre**, aislamiento **PVC** `[confirmar AN]`, γ = 56 m/Ω·mm² (Cu, 20 °C).

La línea general y la derivación del motor son **trifásicas (400 V)**; las derivaciones
de alumbrado y toma, **monofásicas (230 V)**. La línea general, al alimentar cargas
trifásicas y monofásicas, se resuelve como **trifásica equilibrada** (aproximación de
predimensionado `[confirmar AN]`).

## 4. Bases de demanda (slot C4)

Modo **receptores** (catálogo por tipo). **Potencia prevista total: 11 296 W.**

| Terminal | Tipo | Fases | P (W) | cos φ |
|---|---|---|---|---|
| LUM-1 | luminaria | mono | 58,0 | 0,90 |
| LUM-2 | luminaria | mono | 58,0 | 0,90 |
| TOMA-1 | toma uso general | mono | 3 680,0 | 0,95 |
| MOTOR-1 | motor | tri | 7 500,0 | 0,85 |

## 5. Método de cálculo

- **Intensidad por tramo:** I = P / (U · cos φ) (mono) ; I = P / (√3 · U · cos φ) (tri).
- **Propuesta de sección:** momentos sobre catálogo normalizado, limitada por la
  **intensidad admisible** (ITC-BT-19, Cu, PVC, 2 cond. mono / 3 cond. tri).
- **Caída de tensión (vinculante):** método de las intensidades, ΔU = 2·L·I·cos φ/(γ·S)
  (mono) ; ΔU = √3·L·I·cos φ/(γ·S) (tri), **acumulada** desde el cuadro; redimensionado
  automático si supera el límite (**3 % alumbrado / 5 % fuerza**, ITC-BT-19).
- **Topología radial:** propagación por árbol; sin Hardy-Cross.

## 6. Resultados y comprobaciones

**Veredicto: CUMPLE.** Balance de potencias **0,0000 %**. Caída de tensión máxima
**3,318 %** (terminal gobernante **TOMA-1**), por debajo del límite del 5 % (fuerza).
Intensidades dentro del admisible en todos los tramos.

| Tramo | Tipo | Fases | I (A) | S (mm²) | I adm. (A) | ΔU tramo (%) |
|---|---|---|---|---|---|---|
| T1 — LGA (cuadro→subcuadro) | tri | 18,51 | 4,0 | 24 | 0,630 |
| T2 — LUM-1 | mono | 0,28 | 1,5 | 15 | 0,041 |
| T3 — LUM-2 | mono | 0,28 | 1,5 | 15 | 0,041 |
| T4 — TOMA-1 | mono | 16,84 | 2,5 | 21 | 2,222 |
| T5 — MOTOR-1 | tri | 12,74 | 1,5 | 13 | 1,308 |

| Terminal | Fases | P (W) | ΔU acum. (%) | Límite (%) | Cumple |
|---|---|---|---|---|---|
| LUM-1 | mono | 58,0 | 1,137 | 3 | ✔ |
| LUM-2 | mono | 58,0 | 1,137 | 3 | ✔ |
| TOMA-1 | mono | 3 680,0 | 3,318 | 5 | ✔ |
| MOTOR-1 | tri | 7 500,0 | 1,938 | 5 | ✔ |

**Write-back al IFC:** Psets `Pset_Estructurando_ResultadoRed` — **9 elementos, 51
propiedades**. Validación con `iso19650-openbim:ifc-validate`: **APTO** (continuidad
100 %, 0 incidencias).

## 7. Conclusiones y observaciones

La red cumple las caídas de tensión y las intensidades admisibles con las secciones
propuestas. El gobernante es la toma de uso general (TOMA-1), por ser una carga
monofásica relativamente alta en una derivación larga. La sección del motor (1,5 mm²)
quedaría sujeta a confirmar el criterio del 125 % de ITC-BT-47 y la coordinación con
las protecciones `[confirmar AN]`. **Predimensionado a revisar y firmar por técnico
competente (Ingeniero de Caminos).**

---

*Registro de comprobación — 2026-06-22 · sistema ELECTRICAL (terciario/industrial,
receptores) · solver eléctrico radial (intensidades + momentos) · γ=56, PVC, 230/400 V ·
resultado CUMPLE (balance 0,0 %, ΔU máx 3,318 %) · Psets de resultado al IFC (APTO).*

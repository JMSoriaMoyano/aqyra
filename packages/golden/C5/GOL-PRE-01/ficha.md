# Golden GOL-PRE-01 — presupuesto trazable sobre la medición del Maestro (C5, contract-first)

> El primer caso del contrato **C5** (presupuesto). Hace **PRESUPUESTABLE** el modelo que 3.1 hizo
> abrible y 3.3 hizo juzgable: **medición trazable → precios descompuestos → PEM/PEC firmable**.
> **Modo ANCLADO** (contract-first, D_scope): el presupuesto esperado es el **oráculo** (medición
> manual congelada, verificada ×2); el engine `engines/presupuesto` llega en un hilo posterior y
> **antepondrá** el recompute (parser de Qto + motor) contra este MISMO expected (costura C1/C3/C4).

## La medición NACE de los Qto (no se teclea)

Las fixtures `entrada/ARQ.ifc` y `entrada/EST.ifc` son **copias de los IFC del C4-FED-06 enriquecidas
con `Qto_*`** (md5 propios de C5; los originales anclados del C4/C3/visor quedan **intactos**). Las
cantidades del modelo neutro de medición (`entrada.json`) se **leen de esos `Qto`** — la garantía de
que el modelo los declara es del **QA/IDS de C4** aguas arriba (precondición de conformidad para
medición, D_modelo).

- `entrada/ARQ.ifc` — md5 `0b998513ab079b9ef0870e9a6c04ca84`. 4 Qto sets: 2 muros (`Qto_WallBaseQuantities`),
  1 losa (`Qto_SlabBaseQuantities`), 1 puerta (`Qto_DoorBaseQuantities`).
- `entrada/EST.ifc` — md5 `0d7e7f20fc42aa42214ad58de084322e`. 7 Qto sets: 4 pilares, 2 zapatas
  (`Qto_ColumnBaseQuantities`/`Qto_FootingBaseQuantities`), 1 losa.
- Procedencia de la geometría: derivado del Maestro C4-FED-06 (`dcb1e14460f3556107ce35d6dade16c3`).

## Corte del criterio `AQ/v1` (D2 — lo difícil del criterio)

| objeto (Qto) | clase | partida(s) | unidad | cantidad | regla de medición |
|---|---|---|---|---|---|
| M-Fachada-Sur (con hueco) | IfcWall | FAB010 · REV010 · PIN010 | m² | — | **área neta con descuento de hueco > 1,00 m²** |
| M-Interior-01 (sin hueco) | IfcWall | FAB010 · REV010 · PIN010 | m² | — | área neta (sin descuento) |
| Solado-PB · Forjado-N01 | IfcSlab | EHL010 | m³ | 16,20 | volumen neto |
| P1–P4 | IfcColumn | EHS010 | m³ | 1,92 | volumen neto |
| Z1 · Z2 | IfcFooting | CSZ010 | m³ | 0,128 | volumen neto |
| M-Fachada-Sur_puerta | IfcDoor | PPM010 | ud | 1 | conteo |
| — | (regla, sin geometría) | SYS010 | PA | 1 | **2% del PEM medible** (partida alzada, D5) |

**Un objeto → varias partidas:** cada muro genera fábrica (1 cara) + enfoscado (2 caras) + pintura
(2 caras), sobre el área neta con descuento de huecos. FAB010 = 15,90 + 18,00 = **33,90 m²**;
REV010 = PIN010 = 2 × 33,90 = **67,80 m²**.

## Oráculo (calculado a mano, verificado ×2 con ifcopenshell — 2026-07-03)

Cantidades desde los `Qto` (geometría real: muro 6,0×3,0, hueco 1,0×2,1=2,1 m²>umbral → net 15,9;
losas 36 m² × 0,15 y × 0,30; pilares 0,4×0,4×3,0=0,48 m³; zapatas 0,4³=0,064 m³). Importes = cantidad
× precio del banco `AQ-DEMO/v1` (descompuesto MO/mat/maq/indirectos).

**Resumen:** PEM **7 022,53** → (+13% GG 912,93 +6% BI 421,35) base **8 356,81** → (+21% IVA 1 754,93)
**PEC 10 111,74 EUR**. Aritmética cerrada (Σ capítulos = PEM; importe = cantidad × precio; Σ
descomposición + indirectos = precio del nº1).

## Qué ancla el modo ANCLADO (runner `run_case_c5`, más checks que hoy)

Conformidad de los **2 esquemas** (entrada + salida); **identidad por hash** de las fixtures con Qto;
y **coherencia interna**: importe = cantidad × precio (±0,01); precio_unitario == cuadro nº1; nº1 ==
nº2 (Σ componentes + indirectos); PEM = Σ importes; Σ capítulos = PEM; GG/BI/IVA/base/PEC según
`parametros`; partidas `origen=modelo` ⊆ banco + precio == banco; criterio/banco anclados en
`versions.lock`; `trazabilidad` de cada partida `origen=modelo` ⊆ GUIDs del modelo neutro; `origen`
taxonomía cerrada (modelo/regla/manual); S&S (`origen=regla`) = 2% del PEM medible.

## Regla de oro

Un fallo NO se arregla aflojando esta golden. El presupuesto solo se re-ancla si cambia el DISEÑO
del caso, el criterio o el banco (bump de versión + nuevo hash, decisión explícita con JM). Cuando el
engine de presupuesto exista, **reproducirá este expected** — si discrepa, se investiga el engine
(parser/motor), jamás el oráculo.

# HILO-V3 · D-019 — Contrato C5 (puente al motor): forma de entrada y de salida — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con C.1.a + C.2.a + C.3.a + C.4 sí.** Sección/material resueltos en el lado Aqyra; combinación como mapa `{caso: factor}`; carga por área incluida en C5; servicio de cálculo privado confirmado. Inscrita en `DECISIONES.md` como **D-019**. Este documento se conserva como evidencia. La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Arquitectura / BIM-IFC) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** congela la **forma de datos** del contrato **C5** — qué entra al motor (modelo analítico) y qué vuelve (resultados) — para poder cablear el puente sin que cambie bajo los pies. Es la **espina de V3**.
> **Apoyo ya firmado:** **D-018** (signos/ejes Z-up, ejes por rol), **D-020** (releases de uniones), **D-021** (estado de dato del resultado). D-019 los **ensambla** en un contrato versionado.
> **Fecha:** 2026-06-25.

---

## A. Contexto y qué falta por anclar

El **input ya existe casi entero** en código: `StructuralModel` (`publico/openbim/src/index.ts`) lleva nudos, barras, superficies, núcleos, grupos-núcleo, apoyos, cargas, casos y combinaciones. Faltan **tres piezas** para que el motor pueda resolver:

1. **Propiedades numéricas de sección y material.** Hoy `SectionRef` solo lleva **strings** (`profile`, `material`). El FEM necesita **números**: A, I (fuerte/débil), J, E, G, fy/fck.
2. **Combinaciones estructuradas.** Hoy `Combination.expression` es una **cadena** («1.35·G + 1.50·Q»). El motor no debería parsear texto.
3. **Releases** (D-020) y **carga por área** (D-017·A2, diferida en V2).

El **output es nuevo**: un esquema de resultados que el visor pinta, con su **estado de dato** (D-021).

**Anclaje de estándar (verificado).** El input y el output mapean al **IFC StructuralAnalysisDomain**:
- Cargas: `IfcStructuralLoadGroup` (con `IfcLoadGroupTypeEnum`: grupo/caso/combinación); **`IfcRelAssignsToGroupByFactor`** agrupa casos en combinaciones **con su factor** (un caso puede entrar en varias con distinto factor) → es exactamente «1.35·G + 1.50·Q» en forma estructurada.
- Resultados: `IfcStructuralResultGroup` (agrupa resultados, `ResultGroupFor` → modelo); reacciones = `IfcStructuralReaction`.

---

## B. Contrato propuesto (lo que se firma)

### B.1 · Naturaleza y frontera del puente
- **C5 = el adaptador en `privado/puente-calculo/`** que consume **`motor-fem 0.1.0` anclado** (`versions.lock`); no lo bifurca.
- **Frontera cebo/anzuelo:** son **públicos** los **tipos** del modelo de entrada (ya lo son) y del **esquema de resultados** (lo que el visor consume); es **privado** el **adaptador** (traducción rol→PyNite→EC de D-018, invocación del *solve*, QA) y el **motor**.
- **Consecuencia de arquitectura (a confirmar, §C.4):** el motor es Python/PyNite, no JS de navegador → el post-proceso introduce un **servicio de cálculo** (anzuelo). El **visor (cebo) sigue siendo sin-servidor para ver**; solo el cálculo llama al servicio. Coherente con D-010 (que reservó un backend «si la regeneración lo exige») y con que el motor siempre fue `privado/` anclado.

### B.2 · Forma de ENTRADA (extender `StructuralModel`)
Sobre lo que ya existe, se añade:

| Pieza nueva | Forma | Origen |
|---|---|---|
| `member.releases?` | 6 GdL/extremo i,j (true=liberado), ejes locales por rol | D-020 |
| `member.section` (numérico) | `{ A, I_strong, I_weak, J, Av_strong?, Av_weak? }` (m²/m⁴), ejes por rol (D-018) | §C.1 |
| `material` (numérico) | `{ E, G, density, fy_or_fck }` (kN/m², kN/m³) | §C.1 |
| `combination.terms` | mapa estructurado `{ caseId: factor }` (= `IfcRelAssignsToGroupByFactor`) | §C.2 |
| `surface.areaLoad?` | q (kN/m²) sobre el **área real** + objetivo de reparto | D-017·A2, §C.3 |

El **frame global es Z-up / gravedad −Z** (D-018), implícito en todas las coordenadas. La cadena `expression` se conserva **solo para mostrar**; el motor usa `terms`.

### B.3 · Forma de SALIDA (esquema de resultados, tipos públicos)
- **`ResultGroup`** por combinación (≅ `IfcStructuralResultGroup`), con **`state: DataState`** (D-021) — nace `computed`.
- **`MemberResult`** por barra: `N`, `V_strong`, `V_weak`, `M_strong`, `M_weak`, `T` como **arrays a lo largo de x (i→j)** + **deformada local** (dx,dy,dz) + **aprovechamiento** (ratio) + comprobación gobernante. Signos por D-018; N>0 tracción.
- **`NodeResult`** por nudo: desplazamientos globales (6 GdL) y, en apoyos, **reacciones** (≅ `IfcStructuralReaction`).
- **`SurfaceResult`** por lámina/núcleo: esfuerzos de **membrana** (n_x,n_y,n_xy) y **placa** (m_x,m_y,m_xy) por metro, en el plano local.
- **Envolventes** por conjunto de combinaciones (max/min + **combinación gobernante**) — PyNite lo da nativo por `combo_tags`.
- **«Qué no cumple»:** aprovechamiento > 1 marcado.

### B.4 · Versionado y flujo
- **C5** es el contrato **C5** del rango C1..C8; **SemVer**, **MAJOR = rotura**. Consumo **anclado** (`motor-fem 0.1.0`).
- **Flujo:** visor (`publico/`) construye/edita el modelo `proposal` → lo serializa → **adaptador C5** (`privado/`) → motor resuelve → resultados **`computed`** → QA PyNite **`qa-passed`** (D-023) → firma de JM **`verified-signed`** (D-021) → *write-back* al visor y al IFC (`IfcStructuralResultGroup`). El visor pinta con el estado (D-021); el verde solo lo acuña la firma.

---

## C. Puntos abiertos para JM

**C.1 · Dónde se resuelven las propiedades de sección/material.**
- **C.1.a (recomendada) — en el lado Aqyra:** el modelo analítico (entrada de C5) **ya lleva los números** (resueltos del perfil/material del IFC, de un catálogo o autorados). El motor recibe valores listos y **no necesita el catálogo de Aqyra** → separación limpia, motor reutilizable.
- **C.1.b — en el motor/adaptador:** el motor resuelve los nombres de perfil contra un catálogo. Acopla el motor a una nomenclatura.

**C.2 · Representación de la combinación.**
- **C.2.a (recomendada) — mapa estructurado `{caso: factor}`** (espeja `IfcRelAssignsToGroupByFactor`), conservando la cadena solo para mostrar. El motor no parsea texto.
- **C.2.b — solo la cadena `expression`**, el adaptador la parsea. Frágil.

**C.3 · Carga por área (D-017·A2) en el contrato.**
- **C.3.a (recomendada) — incluir `surface.areaLoad` en el esquema C5 ya**, y que el adaptador la **resuelva** a cargas en vigas de borde/nudos por área tributaria **real** (separando diafragma-rigidez de superficie-de-carga). Cierra la Indicación A del cálculo.
- **C.3.b — diferir:** V3 toma solo cargas explícitas en barra/nudo (el ingeniero las pre-aplica); `areaLoad` entra en una iteración posterior. Más simple ahora, pero arrastra trabajo manual.

**C.4 · Servicio de cálculo (B.1).** Confirmar que introducir un **servicio de cálculo privado** para el post-proceso es coherente con D-002 («web sin servidor»), entendiendo que **D-002 aplica al visor (cebo)**, que **sigue sin-servidor para ver**, y que el motor siempre fue `privado/` anclado. *Recomendación: sí* (es el anzuelo, no el cebo).

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

### D-019 · Contrato C5 — forma de entrada y de salida (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** congelar el contrato **C5** (puente al `motor-fem 0.1.0` anclado, adaptador en `privado/`). **Entrada** = `StructuralModel` (D-018 Z-up) extendido con `member.releases` (D-020), **propiedades numéricas de sección/material** (A, I_strong, I_weak, J, E, G, fy/fck), **combinaciones estructuradas** `{caso: factor}` (≅ `IfcRelAssignsToGroupByFactor`) y `surface.areaLoad` (≅ Indicación A). **Salida** = esquema de resultados con **`state: DataState`** (D-021, nace `computed`): `MemberResult` (N/V/M/T por x, deformada, aprovechamiento, signos D-018), `NodeResult` (desplazamientos + reacciones ≅ `IfcStructuralReaction`), `SurfaceResult` (membrana/placa), **envolventes** con combinación gobernante; mapeo a `IfcStructuralResultGroup`. **Frontera:** tipos públicos (entrada + resultados); adaptador y motor privados. **SemVer**, MAJOR = rotura.
- **Bifurcaciones firmadas por JM:** [C.1 props sección/material: a lado-Aqyra / b motor] · [C.2 combinación: a mapa / b cadena] · [C.3 carga por área: a incluir / b diferir] · [C.4 servicio de cálculo: sí / revisar].
- **Evidencia:** IFC StructuralAnalysisDomain — `IfcStructuralLoadGroup`/`IfcLoadGroupTypeEnum`, `IfcRelAssignsToGroupByFactor` (casos→combinación con factor), `IfcStructuralResultGroup`/`IfcStructuralReaction` (verificado 2026-06-25); PyNite — esfuerzos por dirección, envolventes por `combo_tags` (verificado 2026-06-25); D-018/D-020/D-021; código V2 — `StructuralModel`, `SectionRef` solo strings, `Combination.expression` string. Detalle en `HILO-V3_para-firma_D-019-contrato-C5.md`.
- **Acciones que dispara:** (1) extender los tipos públicos de entrada (sección/material numéricos, `releases`, `terms`, `areaLoad`) y definir los tipos públicos de **resultado** + bump SemVer del contrato; (2) implementar el **adaptador C5** en `privado/puente-calculo/` (serialización modelo→motor, traducción de ejes/signos/releases de D-018/D-020, *solve*, mapeo de resultados con estado); (3) levantar el **servicio de cálculo** privado (C.4); (4) `write-back` de resultados al IFC como `IfcStructuralResultGroup`; (5) caso patrón end-to-end (Decopak HQ: una combinación ELU → deformada + aprovechamientos `computed`) como prueba del contrato.

---

## Fuentes

- **IFC — agrupación de cargas:** `IfcStructuralLoadGroup` con `IfcLoadGroupTypeEnum` (LOAD_GROUP/LOAD_CASE/LOAD_COMBINATION); `IfcRelAssignsToGroupByFactor` agrupa casos en combinaciones con `Factor` (un caso en varias combinaciones con distinto factor); desde IFC4 se recomienda casos + grupos + `IfcRelAssignsToGroupByFactor` (consultado 2026-06-25): [IfcStructuralLoadGroup (IFC4.2)](https://standards.buildingsmart.org/IFC/DEV/IFC4_2/FINAL/HTML/schema/ifcstructuralanalysisdomain/lexical/ifcstructuralloadgroup.htm) · [IfcLoadGroupTypeEnum (IFC4.3)](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcLoadGroupTypeEnum.htm)
- **IFC — resultados:** `IfcStructuralResultGroup` (`ResultGroupFor` → modelo), `IfcStructuralReaction` (IFC4.3, consultado 2026-06-25): [IfcStructuralReaction](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcStructuralReaction.htm)
- **PyNite — resultados/envolventes:** esfuerzos por dirección local, `combo_tags` para envolventes con combinación gobernante (consultado 2026-06-25): [Members — Pynite](https://pynite.readthedocs.io/en/latest/member.html)
- **Estado interno:** `publico/openbim/src/index.ts` (`StructuralModel`, `SectionRef` solo strings, `Combination.expression` string), `DECISIONES.md` D-002/D-010/D-018/D-020/D-021, `integracion/versions.lock` (`motor-fem 0.1.0`), `privado/README.md` (`puente-calculo/`) — repo Aqyra, 2026-06-25.

---

*Para-firma de D-019 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md` y arrancar el cableado del adaptador C5. La IA opera; JM firma.*

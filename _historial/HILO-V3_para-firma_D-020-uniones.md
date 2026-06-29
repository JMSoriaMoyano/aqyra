# HILO-V3 · D-020 — Tipificación de uniones (rígido/articulado / *releases*) — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con la opción C.b** (las aspas/`brace` nacen articuladas). Inscrita en `DECISIONES.md` como **D-020**. Este documento se conserva como evidencia (modelo de datos, tablas y fuentes). La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Ing. estructural / BIM-IFC) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** define cómo se tipifican las uniones del modelo analítico (nudos rígidos por defecto, extremos liberables a articulado) y cómo se representan los *releases* en el dato — el segundo input que el motor (C5) necesita y que V2 dejó aplazado (la 2.ª mitad de la «terna»). **Prerequisito de C5** (D-019), junto con D-018.
> **Apoyo ya firmado:** **D-018** fijó la mecánica de *releases* (6 GdL/extremo `{ux,uy,uz,rx,ry,rz}×{i,j}`, **true = liberado**, polaridad invertida frente a `Restraints`, mapeo a `def_releases` de PyNite y a ejes locales por rol). D-020 define el **modelo de datos, los defaults, la codificación, la UI y el alcance**.
> **Fecha:** 2026-06-25.

---

## A. Por qué hace falta D-020

El modelo analítico de V2 (`StructuralMember`) **no lleva información de unión**: id, tipo, nudos, sección, trazabilidad — y nada sobre si los extremos transmiten momento. Sin esto, el motor tiene que **asumir** un comportamiento (todo rígido o todo articulado), y cualquiera de las dos hipótesis falsea casos reales:

- una **viga-pilar de pórtico** necesita **nudo rígido** (transmite momento; si se articula, el pórtico no tiene estabilidad lateral por flexión);
- un **tirante / aspa de arriostramiento** es **biarticulado** (solo axil; si se empotra, aparecen flectores espurios y el dimensionado sale mal);
- una **vigueta apoyada** suele ir **articulada** en sus extremos.

Es exactamente el tipo de decisión de idealización que el gobierno marca como fuente de error (D-008): debe ser **explícita, revisable y editable**, nunca una hipótesis silenciosa del solver.

**Anclaje de estándar (verificado).** En IFC StructuralAnalysisDomain la unión se expresa con `IfcRelConnectsStructuralMember`, cuyo **`AppliedCondition`** fija la condición por GdL (rigидez/liberación) en un **`ConditionCoordinateSystem` alineado por defecto con los ejes locales de la barra**; `AdditionalConditions` cubre deslizamiento/fallo. Articulado = libre giro; rígido/momento = restringe el giro y transmite flector. El Pset diff-able de Aqyra (D-011/D-013) **espeja** este concepto para que la futura emisión nativa `IfcRelConnectsStructuralMember` (≈V3+) sea limpia.

---

## B. Convenio propuesto (lo que se firma)

### B.1 · Default: nudo RÍGIDO (continuo)
Por defecto **ningún extremo lleva *release*** → nudo **rígido/continuo** (transmite N, V, M, T). El ingeniero **relaja a articulado** donde corresponda. *Motivo:* es el comportamiento neutro y conservador para hormigón monolítico y acero soldado; relajar es una acción consciente y trazable.

> **Frontera cebo/anzuelo:** proponer **automáticamente** qué unión es articulada por **tipología o norma** (p. ej. «las aspas son biarticuladas», clasificación de nudos EC3 por rigidez) es **criterio = anzuelo → V4**. En V2/V3 la **mecánica** es: default rígido + *release* autorado. El default no incorpora criterio; solo abre el grado de libertad.

### B.2 · *Release* de extremo (modelo de datos)
Cada barra puede llevar *releases* en sus extremos **i** (nudo inicial) y **j** (nudo final), expresados en **ejes locales por rol** (D-018), 6 GdL, **true = liberado**:

| GdL local | Libera | Pin estándar |
|---|---|---|
| `axial` (ux) | esfuerzo axil N | — |
| `vStrong` (cortante en plano fuerte) | cortante V eje fuerte | — |
| `vWeak` (cortante en plano débil) | cortante V eje débil | — |
| `torsion` (rx) | momento torsor T | — |
| `mStrong` (giro que libera el flector de eje **fuerte**) | M de eje fuerte | **✓** |
| `mWeak` (giro que libera el flector de eje **débil**) | M de eje débil | **✓** |

- **Rótula (articulación) estándar** = liberar **`mStrong` + `mWeak`** en el extremo (los dos flectores), manteniendo axil, cortantes y torsión.
- **Barra biarticulada (tirante/aspa, comportamiento de celosía)** = rótula en **ambos** extremos.
- **Regla de estabilidad (de PyNite, a respetar en la UI):** no liberar simultáneamente **axil** (`axial`) ni **torsión** (`torsion`) en los **dos** extremos de la misma barra → mecanismo inestable; la UI lo impide o avisa.

### B.3 · Extensión del contrato (`publico/`, SemVer MINOR)
- **`StructuralMember`** gana un campo opcional `releases?: { i?: MemberEndRelease; j?: MemberEndRelease }` (ausente = rígido). `MemberEndRelease` = los 6 booleanos de B.2, todos `proposal`.
- **`PreApi`** gana `listReleases()` y `setRelease(memberId, end, release)` (espeja `setSupport`). Bump `@aqyra/embed` (MINOR).
- **Campo reservado, no usado en V3:** `stiffness?` por GdL (resorte rotacional) para **semirrígido** — el `AppliedCondition` de IFC lo admite; aquí se deja el hueco pero **V3 solo implementa el booleano** (ver B.5).

### B.4 · Codificación (Pset diff-able) y UI
- **Persistencia:** línea `release:{memberId}` en el anejo `Pset_AqyraStructural` (mismo mecanismo *append* de D-013), con los flags de i/j; idempotente y reversible. Espeja `IfcRelConnectsStructuralMember.AppliedCondition` para la futura emisión nativa.
- **UI / NL (skin Calculista):** comandos «articula este extremo» / «rótula aquí» / «pon este tirante biarticulado»; **glifo** en el extremo (circulito = rótula) sobre el wireframe idealizado; editable, `state="proposal"`. El cartel de aviso de modelado se retira cuando las uniones quedan resueltas/confirmadas.

### B.5 · Alcance de V3 (y lo que queda fuera)
- **Dentro:** uniones **rígidas** (default) y **articuladas** (release booleano de flectores), por extremo, editables. Mapeo directo a `def_releases` de PyNite (D-018).
- **Fuera (diferido):** **semirrígido** (rigidez rotacional parcial / resortes de nudo) y la **clasificación de nudos EC3** (rígido/semirrígido/articulado por rigidez y resistencia) → necesita criterio (anzuelo, V4) y capacidad del motor; el campo `stiffness?` queda reservado para no romper el contrato cuando llegue.

---

## C. Punto abierto para JM

**Default de las barras tipo `brace` (aspas/arriostramientos).** Dos opciones:
- **C.a (recomendada) — default RÍGIDO para todas, incluidas las `brace`.** Coherente con B.1 (mecánica sin criterio); el ingeniero articula las aspas explícitamente. La sugerencia automática «las aspas son biarticuladas» se enciende con el copiloto en **V4** (criterio). *Recomendada por disciplina cebo/anzuelo: ningún criterio en `publico/`.*
- **C.b — default ARTICULADO solo para `brace`.** Más cómodo (las aspas casi siempre son biarticuladas), pero **mete una regla de criterio en la mecánica** del cebo. Si se elige, dejar constancia de que es una excepción pragmática, no la puerta a más auto-criterio.

El resto del convenio (B.2–B.5) no tiene alternativa razonable.

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

> Copiar a `DECISIONES.md` como **D-020**, poner fecha + `Firmante: JM` + `FIRMA: ✅`, y registrar la opción elegida en C.

### D-020 · Tipificación de uniones (rígido/articulado / *releases*) (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** uniones **rígidas por defecto** (sin *release* = transmite N/V/M/T); extremos **liberables a articulado** por el ingeniero. *Release* por extremo i/j en **ejes locales por rol** (D-018), 6 GdL, **true = liberado**; **rótula = liberar `mStrong`+`mWeak`**, **biarticulada = rótula en ambos extremos**. Se prohíbe liberar axil o torsión en los dos extremos a la vez (inestabilidad, PyNite). Modelo de datos: `StructuralMember.releases?` + `PreApi.setRelease/listReleases` (contrato **MINOR**); persistencia como línea `release:{id}` en `Pset_AqyraStructural` (*append* D-013), espejando `IfcRelConnectsStructuralMember.AppliedCondition`. UI/NL en la skin Calculista con glifo de rótula, todo `proposal`. **Semirrígido y clasificación de nudos EC3 → diferidos** (campo `stiffness?` reservado; criterio = anzuelo, V4).
- **Default de `brace`:** [registrar opción C.a rígido / C.b articulado firmada por JM].
- **Evidencia:** IFC StructuralAnalysisDomain — `IfcRelConnectsStructuralMember.AppliedCondition` en `ConditionCoordinateSystem` de ejes locales; articulado=libre giro, rígido=transmite momento (IFC4/4.3, verificado 2026-06-25); PyNite `def_releases` 6 GdL/extremo true=liberado, advertencia de inestabilidad por liberar axil/torsión en ambos extremos (verificado 2026-06-25); D-018 (mecánica de *releases* y ejes por rol); código V2 (`StructuralMember` sin releases hoy). Detalle en `HILO-V3_para-firma_D-020-uniones.md`.
- **Acciones que dispara:** (1) extender `StructuralMember`/`PreApi` (`publico/openbim`) con `releases`/`setRelease`/`listReleases` + bump MINOR de `@aqyra/embed`; (2) codificar `release:{id}` en el anejo y su round-trip; (3) UI/NL de rótula en la skin Calculista (glifo + comandos), con la regla de estabilidad; (4) el adaptador C5 (`privado/`) traduce los *releases* a `def_releases` de PyNite (polaridad ya invertida, D-018); (5) test: barra biarticulada → solo axil (M nulo en extremos) en el caso patrón.

---

## Fuentes

- **IFC StructuralAnalysisDomain — uniones/condiciones de extremo:** `IfcRelConnectsStructuralMember` (`AppliedCondition` por GdL en `ConditionCoordinateSystem` de ejes locales; `AdditionalConditions` = deslizamiento/fallo); articulado = libre giro, rígido = transmite momento. buildingSMART (consultado 2026-06-25): [IfcRelConnectsStructuralMember (IFC4)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD1/HTML/schema/ifcstructuralanalysisdomain/lexical/ifcrelconnectsstructuralmember.htm) · [IfcRelConnectsStructuralMember (IFC4.3 dev)](https://github.com/buildingSMART/IFC4.3.x-development/blob/master/docs/schemas/domain/IfcStructuralAnalysisDomain/Entities/IfcRelConnectsStructuralMember.md) · [IfcStructuralConnection](https://standards.buildingsmart.org/IFC/DEV/IFC4_2/FINAL/HTML/schema/ifcstructuralanalysisdomain/lexical/ifcstructuralconnection.htm)
- **PyNite — *releases*:** `def_releases(Dxi..Rzj)` 6 GdL/extremo, true=liberado; rótula = liberar `Ry`/`Rz`; advertencia: no liberar axil ni torsión en ambos extremos (consultado 2026-06-25): [Members — Pynite](https://pynite.readthedocs.io/en/latest/member.html)
- **Estado interno:** `DECISIONES.md` D-018 (mecánica de *releases*, ejes por rol), D-011/D-013 (Pset diff-able); `publico/openbim/src/index.ts` (`StructuralMember` sin releases) — repo Aqyra, 2026-06-25.

---

*Para-firma de D-020 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md`. La IA opera; JM firma.*

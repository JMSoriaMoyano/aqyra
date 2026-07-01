# HILO-V3 · D-018 — Convenio definitivo de ejes y signos — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con la opción +Z.** Inscrita en `DECISIONES.md` como **D-018**; **D-015** marcada superada. Este documento se conserva como evidencia (tablas de mapeo y fuentes). La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Ing. estructural / BIM-IFC) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** fija, sin ambigüedad, el sistema global, los ejes locales de barra y los signos de esfuerzos, deformada, reacciones y *releases* del modelo analítico que viaja por el **contrato C5** al motor y a la QA (PyNite). **Sustituye a D-015** (provisional). Es **prerequisito de C5** (D-019): sin esto, deformada y esfuerzos pueden salir «del revés» y la verificación puede cruzar eje fuerte/débil.
> **Fecha:** 2026-06-25.
> **Evidencia:** búsqueda de estándares (ver §Fuentes) + código real de V2 (`publico/visor/src/idealize.ts`, `publico/openbim/src/index.ts`).

---

## A. Por qué hace falta D-018 (dos ambigüedades reales detectadas)

**A.1 · Mezcla Z-up / Y-up entre la geometría y la carga.** La idealización de V2 deriva la geometría en **Z-up de IFC**: la verticalización de muros comprueba la componente **Z** de la normal (`idealize.ts:491`, `Math.abs(normal[2]) < 0.7`). Pero D-015 (provisional) puso la gravedad por defecto en `direction="y"` hacia **−Y** — el frame del visor (Three.js, Y-up). Geometría en Z-up y carga en Y-down en el mismo modelo es una incoherencia que hay que cerrar antes de tocar el motor.

**A.2 · Choque de nomenclatura PyNite ↔ Eurocódigo (eje fuerte/débil).** Verificado:
- **PyNite** (motor + oráculo QA): eje local **x** = barra (i→j); **z = eje fuerte** (en su ejemplo `Iz=204 in⁴` *strong*, `Iy=17,3 in⁴` *weak*); el momento de eje fuerte es **`Mz`**, el de eje débil **`My`**.
- **Eurocódigo EN 1993-1-1**: **y-y = eje fuerte (mayor)**, z-z = eje débil; el momento de eje fuerte es **`My,Ed`**.

→ «Mz» de PyNite (fuerte) ≡ «My,Ed» del Eurocódigo (fuerte): **mismas letras, ejes intercambiados**. Si el contrato identifica los ejes por **letra** y no por **rol**, la verificación EC (armado) cruza fuerte↔débil y da resultados plausibles pero falsos. Es el patrón de error que el gobierno de dos llaves debe atrapar (D-008).

**A.3 · Polaridad opuesta de coacciones vs *releases*.** El contrato actual usa `Restraints { ux..rz }` con **true = restringido** (apoyo). PyNite `def_releases(Dxi..Rzj)` usa **true = liberado**. El adaptador C5 debe invertir; hay que dejarlo escrito para que no se cuele un empotramiento donde iba una rótula.

---

## B. Convenio propuesto (lo que se firma)

### B.1 · Sistema global
**Global Z-up, dextrógiro, unidades SI del proyecto (m, kN).** La **gravedad actúa según −Z global**. El modelo analítico y el contrato C5 **hablan Z-up**; la representación del visor en Three.js (Y-up) es un **detalle de presentación** (transformada interna), nunca parte del contrato.

| | Aqyra (contrato C5) | IFC4/4.3 | PyNite | Visor (Three.js) |
|---|---|---|---|---|
| Vertical (+) | **+Z** | +Z (nativo) | +Z (definido por Aqyra) | +Y *(solo pantalla)* |
| Gravedad | **−Z** | −Z | `FZ` negativa | *(−Y en pantalla)* |

*Motivo:* alinea el modelo analítico con la geometría IFC de la que se deriva (elimina A.1), con el IFC StructuralAnalysisDomain y con un PyNite que es agnóstico al frame (su ejemplo de ménsula ya usa `FZ -5`). Es además **menos trabajo**: la geometría ya está en Z-up; solo se corrige el *default* de carga de D-015.

### B.2 · Ejes locales de barra
- **x_local** = del nudo inicial (i) al final (j). Define el sentido de recorrido del diagrama.
- **Los otros dos ejes se nombran por ROL, no por letra**, y el contrato lleva el mapeo explícito a cada consumidor:

| Rol en el contrato C5 | Geometría | PyNite | Eurocódigo |
|---|---|---|---|
| `axis` (longitudinal) | i→j | x (Fx, dx) | x |
| `strong` (eje fuerte, mayor I) | el de mayor inercia | **z** (Iz, Mz, Fy, dy) | **y-y** (My,Ed) |
| `weak` (eje débil, menor I) | el de menor inercia | **y** (Iy, My, Fz, dz) | **z-z** (Mz,Ed) |

→ El contrato C5 **expone `strong`/`weak` por rol**; el adaptador (privado/) traduce a las letras de PyNite y la memoria de armado a las del Eurocódigo. **Nunca se pasa una letra cruda entre capas.** La orientación de la sección (qué eje es el fuerte) se ancla con el ángulo de rotación de PyNite (`add_member(rotation=…)`).

### B.3 · Signos de esfuerzos
- **N (axil): N > 0 = TRACCIÓN**, N < 0 = compresión. (Coincide con EC.)
- **V (cortante), M (flector), T (torsor):** se adopta como **canónica la convención positiva de PyNite** (productor + segunda llave), documentada en su diagrama `sign_convention.png`. El adaptador C5 **alinea el signo de salida de PyNite a esta convención** y la memoria de armado interpreta a ejes EC vía la tabla B.2.
- *A confirmar en implementación (distinguido de lo verificado):* el signo exacto de las flechas de V/M/T se fija contra `sign_convention.png` de PyNite al cablear el adaptador; aquí se fija la **regla** (PyNite canónico + N>0 tracción), no se reproduce el diagrama.

### B.4 · Deformada y reacciones
- **Deformada:** desplazamientos en componentes **globales** (dX, dY, dZ) y giros (rX, rY, rZ); positivo = según el eje global positivo. Para diagramas por barra, componentes **locales** (dx, dy, dz) según B.2.
- **Reacciones:** en los apoyos, componentes **globales**; signo = **fuerza que el apoyo ejerce sobre la estructura**. Mapean a `IfcStructuralReaction` del IFC StructuralAnalysisDomain (write-back y trazabilidad).

### B.5 · Coacciones y *releases* (enlaza con D-020)
- **Apoyos** (`Restraints`): **true = GdL restringido** (convenio actual del contrato; se mantiene).
- ***Releases* de extremo de barra:** 6 GdL por extremo `{ux,uy,uz,rx,ry,rz}` × {i,j}, **true = GdL LIBERADO**. Rótula = liberar `rz`+`ry` (giros de flexión) en el extremo. **El adaptador C5 invierte la polaridad** al traducir coacción↔*release* y al llamar a `def_releases` de PyNite. *(Evita liberar simultáneamente axil o torsión en ambos extremos: inestabilidad — advertencia de PyNite.)*

---

## C. Punto abierto para JM (la única bifurcación real)

**Sistema global vertical: `+Z` (recomendado) vs `+Y`.**
- **Recomendación de la IA: +Z (B.1).** Coherente con la geometría IFC ya derivada, con el dominio estructural IFC y con PyNite; corrige la incoherencia A.1 con el mínimo cambio (solo el *default* de carga de D-015).
- *Alternativa +Y:* solo tendría sentido si se quisiera que el contrato hablara el frame del visor; obligaría a transformar toda la geometría derivada y a convivir con el frame IFC en cada *write-back*. No se recomienda.

El resto del convenio (B.2–B.5) no tiene alternativa razonable: el mapeo por rol y la inversión de polaridad son correcciones de errores, no preferencias.

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

> Copiar a `DECISIONES.md` como **D-018**, poner fecha + `Firmante: JM` + `FIRMA: ✅`, y marcar D-015 como **superada por D-018**.

### D-018 · Convenio definitivo de ejes y signos (sustituye D-015) (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** **Global Z-up dextrógiro**, gravedad −Z; el modelo analítico y el contrato C5 hablan Z-up (el Y-up del visor es presentación). **Ejes locales de barra por ROL** (`axis`/`strong`/`weak`), con mapeo explícito a PyNite (x/z/y) y a Eurocódigo (x/y-y/z-z) — nunca se pasa la letra cruda entre capas. **N>0 = tracción**; V/M/T en la **convención positiva canónica de PyNite**, alineada por el adaptador C5. **Deformada/reacciones** en componentes globales (reacciones → `IfcStructuralReaction`). ***Releases*** 6 GdL/extremo con **true = liberado** (el adaptador invierte la polaridad frente a `Restraints`, true = restringido).
- **Evidencia:** PyNite docs (ejes locales x/z-strong/y-weak; `def_releases`; loads global mayúscula / local minúscula) — verificado 2026-06-25; EN 1993-1-1 (y-y mayor / z-z menor) — verificado 2026-06-25; IFC StructuralAnalysisDomain (`IfcStructuralReaction`/`IfcStructuralResultGroup`) — verificado 2026-06-25; código V2 (`idealize.ts` deriva en Z-up; `openbim` `Restraints` true=restringido).
- **Sustituye:** **D-015** (convenio provisional kN/−Y) → marcar D-015 «superada por D-018».
- **Acciones que dispara:** (1) corregir el *default* de carga gravitatoria de `direction="y"`/−Y a **−Z global**; (2) el contrato C5 (D-019) expone ejes por rol + esquema de resultados con su signo; (3) el adaptador C5 (privado/) implementa la traducción de letras y la inversión de polaridad de *releases* y la alineación de signo de PyNite; (4) un **test de signos** (caso patrón: ménsula con carga −Z → tracción arriba, flecha −Z, reacción +Z y M de empotramiento de signo conocido) como red de seguridad de la segunda llave.

---

## Fuentes

- **PyNite (motor/QA) — ejes locales y signos:** x = i→j; z local horizontal a la derecha; y = z×x; en el ejemplo `Iz` *strong* / `Iy` *weak*; `Mz` momento de eje fuerte, `My` de eje débil; cargas globales en MAYÚSCULA (`FX/FY/FZ`) y locales en minúscula (`Fx/Fy/Fz`); `def_releases(Dxi..Rzj)` true=liberado. Pynite docs (consultado 2026-06-25): [Members — Pynite](https://pynite.readthedocs.io/en/latest/member.html) · diagrama [sign_convention.png](https://pynite.readthedocs.io/en/latest/_images/sign_convention.png)
- **Eurocódigo EN 1993-1-1 — ejes principales:** y-y = eje mayor (fuerte), z-z = eje menor (débil); `My,Ed` momento de eje fuerte, `Mz,Ed` de eje débil (consultado 2026-06-25): [Guide to Eurocode 3 — SkyCiv](https://skyciv.com/docs/tech-notes/other/guide-to-eurocode-3-steel-design/) · [JRC Eurocodes Steel — Design of Members](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/05_Eurocodes_Steel_Workshop_SIMOES.pdf)
- **IFC StructuralAnalysisDomain — resultados/reacciones:** `IfcStructuralReaction`, `IfcStructuralResultGroup` (IFC4.3, buildingSMART, consultado 2026-06-25): [IfcStructuralReaction](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcStructuralReaction.htm) · [IfcStructuralAnalysisDomain](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/ifcstructuralanalysisdomain/content.html)
- **Estado interno:** `publico/visor/src/idealize.ts` (verticalización por `normal[2]`, Z-up), `publico/openbim/src/index.ts` (`Restraints`, `Load.direction`), `DECISIONES.md` D-015 (repo Aqyra, 2026-06-25).

---

*Para-firma de D-018 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md` y marcar D-015 superada. La IA opera; JM firma.*

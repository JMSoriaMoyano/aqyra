# HILO-V3 · D-023 — Carril de QA con PyNite (la segunda llave) — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con C.1 sí + C.2 propuesta + C.3 sí + C.4.a.** Independencia PyNite≠motor-fem exigida; tolerancias propuestas aceptadas; equilibrio como gate previo; ante `qa-fail`, bloqueo con anulación documentada. Inscrita en `DECISIONES.md` como **D-023**. Este documento se conserva como evidencia. La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Gobierno QA / BIM-IFC) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** cómo se produce el estado **`qa-passed`** que D-021 dejó dibujado — la **verificación independiente** que es la primera de las dos llaves antes de tu firma. Define el productor≠QA, qué se reconcilia, con qué tolerancia y qué pasa si no cuadra.
> **Apoyo ya firmado:** **D-021** (estados `computed`→`qa-passed`→`verified-signed`), **D-019** (contrato C5, esquema de resultados), **D-018** (signos para comparar manzanas con manzanas).
> **Fecha:** 2026-06-25.

---

## A. Contexto y anclaje

D-021 fijó que un resultado nace `computed` (motor, 0 llaves) y solo llega a `verified-signed` tras **QA independiente + firma**. D-023 define esa **QA independiente** — la 1.ª llave.

**Roles (confirmados en el repo):**
- **Productor (llave 0):** `motor-fem` resuelve el FEM → `computed`.
- **QA / oráculo (llave 1):** **PyNite**, motor **independiente**, re-ejecuta y reconcilia → `qa-passed` (carril *Estructurando 2.0*; D-009 ya registró que la verificación está «pendiente del oráculo PyNite»).
- **Firma (llave 2):** **JM** → `verified-signed`.

**Anclaje en práctica reconocida (verificado).** El **chequeo de Categoría 3** (BS 5975) es el patrón de verificación independiente del sector: lo hace un revisor **organizativamente independiente** del proyectista, que **desarrolla sus propios cálculos** — explícitamente **no** una revisión de cortesía ni un *peer review* de las mismas cuentas. Las dos llaves de Aqyra son la versión disciplinada de eso:
- la **QA automática** (PyNite, motor distinto + equilibrio) cubre la parte mecánica de la independencia;
- la **firma de JM** aporta el juicio humano de Cat 3 (¿son correctas las hipótesis y la idealización?), que la automatización no puede certificar.

---

## B. Propuesta (lo que se firma)

### B.1 · Independencia productor ≠ QA (el núcleo)
La QA **solo es evidencia si es independiente**: PyNite debe ser un **código distinto** del solver de `motor-fem`. Si `motor-fem` compartiera su núcleo de resolución con PyNite, que «coincidan» no probaría nada (sería el mismo motor dos veces). → **Requisito + verificación:** confirmar que `motor-fem` y PyNite no comparten núcleo; si lo compartieran, la QA usa otro motor o método.

### B.2 · Qué reconcilia la QA (sobre el mismo modelo analítico y combinación)
1. **Equilibrio global** (gate barato, siempre activo, **pura estática, sin FEM**): Σreacciones = Σacciones aplicadas, por eje y momentos. Atrapa al instante errores gruesos (signos, cargas perdidas, unidades).
2. **Reacciones** en apoyos.
3. **Desplazamientos** clave (flecha máxima por barra / nudo).
4. **Esfuerzos** de extremo y envolventes N/V/M en secciones críticas.
5. **Aprovechamientos** (el «qué no cumple»).

Dentro de tolerancia → `qa-passed`. Fuera → **`qa-fail`**.

### B.3 · Tolerancias (propuesta, §C.2)
- **Equilibrio:** ~0,1 % (debe cuadrar casi exacto; si no, hay un error, no una tolerancia).
- **Reacciones y desplazamientos:** ±2–5 %.
- **Esfuerzos y aprovechamientos:** ±5 %.

Una diferencia mayor casi siempre delata una **idealización distinta** entre los dos modelos (la fuente de error de D-008), no «ruido numérico»; por eso se investiga, no se promedia.

### B.4 · Qué pasa si NO cuadra (`qa-fail`)
`qa-fail` **no degrada en silencio**: **bloquea** el camino a `verified-signed` y **expone la discrepancia** (qué magnitud, dónde, cuánto) para que el ingeniero la resuelva — normalmente una revisión de idealización (D-008). El visor mantiene el resultado como `computed` con marca de **QA fallida**; nunca lo pinta `qa-passed`.

### B.5 · Entorno y trazabilidad
La QA corre en el **entorno certificado** (`privado/`, carril *Estructurando 2.0*), por una **vía de código distinta** de la del productor. La auditoría registra **ambas ejecuciones** (motor-fem y PyNite) + la **reconciliación** como evidencia que acompaña a la firma.

### B.6 · Qué significa cada llave (gobierno)
`qa-passed` es **necesario pero no suficiente**: es «dos motores independientes coinciden y la estática cuadra». La **2.ª llave es tu firma**, que añade el juicio humano sobre hipótesis e idealización. Solo entonces `verified-signed`. **La IA prepara la evidencia (las dos ejecuciones + la reconciliación); JM firma.**

### B.7 · Alcance de D-023 (y lo que queda fuera)
- **Dentro:** el carril de QA, la independencia productor≠QA, qué se reconcilia y con qué tolerancia, el gate `qa-passed`/`qa-fail`.
- **Fuera:** el **alcance del armado** que se verifica (D-022); la **mecánica de firma** (flujo de `privado/`, parte de C5/D-019); los **internos de `motor-fem`** (anclado, no se reescribe).

---

## C. Puntos abiertos para JM

**C.1 · Independencia del motor de QA.** ¿Exigir que **PyNite ≠ núcleo de `motor-fem`** (recomendado), con una verificación de que no comparten solver? *Recomendado sí: es lo que hace que la QA sea evidencia y no eco.*

**C.2 · Magnitudes y tolerancias (B.2/B.3).** ¿Aceptar el conjunto propuesto (equilibrio casi-exacto; reacciones/desplazamientos ±2–5 %; esfuerzos/aprovechamientos ±5 %) o ajustar bandas? *Recomendado: aceptar como punto de partida y afinar contra Decopak HQ.*

**C.3 · Equilibrio como gate barato siempre activo (B.2.1).** ¿Correr el chequeo de equilibrio (pura estática) **antes** del re-cálculo completo de PyNite, como primera red instantánea? *Recomendado sí: cuesta nada y caza los errores gruesos al momento.*

**C.4 · Qué puede hacer la firma ante un `qa-fail`.**
- **C.4.a (recomendada) — bloqueo con anulación documentada:** `qa-fail` bloquea la firma por defecto; JM **puede** anular, pero **solo con justificación escrita** que queda en la auditoría (p. ej. «la discrepancia es un artefacto de tolerancia conocido»). Mantiene tu autoridad última **y** la trazabilidad.
- **C.4.b — bloqueo duro:** `qa-fail` impide firmar sin excepción; hay que resolver la discrepancia antes. Más estricto, menos flexible.

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

### D-023 · Carril de QA con PyNite (segunda llave) (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** la 1.ª llave (`qa-passed`) la produce una **QA independiente** del productor: `motor-fem` (productor, → `computed`) y **PyNite** (oráculo QA, **código independiente**, → `qa-passed`); la 2.ª llave es la **firma de JM** (→ `verified-signed`). La QA reconcilia sobre el mismo modelo: **equilibrio global** (gate de pura estática), reacciones, desplazamientos clave, esfuerzos/envolventes y aprovechamientos. **`qa-fail` bloquea** la firma y **expone** la discrepancia (no degrada en silencio); el visor mantiene el resultado `computed` con marca de QA fallida. Corre en **entorno certificado** (`privado/`), por vía de código distinta del productor; la auditoría guarda **ambas ejecuciones + la reconciliación** como evidencia. `qa-passed` es necesario, no suficiente: solo la firma sella `verified-signed`. Anclado en el patrón de **chequeo independiente Cat 3** (BS 5975).
- **Bifurcaciones firmadas por JM:** [C.1 independencia PyNite≠motor-fem: sí / revisar] · [C.2 tolerancias: aceptar propuesta / ajustar] · [C.3 equilibrio como gate previo: sí / no] · [C.4 ante qa-fail: a) bloqueo con anulación documentada / b) bloqueo duro].
- **Evidencia:** chequeo independiente Cat 3 (BS 5975): revisor organizativamente independiente, cálculos propios, no peer review (verificado 2026-06-25); PyNite — re-cálculo independiente, envolventes por `combo_tags` (verificado 2026-06-25); repo — `motor-fem` productor vs PyNite oráculo QA (`HILO-V2_cierre-y-arranque-V3.md` §3, `DECISIONES.md` D-009 salvedad, `privado/README.md` dos llaves); D-018/D-019/D-021. Detalle en `HILO-V3_para-firma_D-023-qa-pynite.md`.
- **Acciones que dispara:** (1) verificar que `motor-fem` y PyNite no comparten núcleo de solver (C.1); (2) implementar la QA en `privado/` (re-cálculo PyNite + chequeo de equilibrio + reconciliación con tolerancias C.2/C.3); (3) gate `qa-passed`/`qa-fail` cableado al estado de dato (D-021) y a la guarda de firma; (4) registro de auditoría (ambas ejecuciones + reconciliación); (5) caso patrón: Decopak HQ, una combinación ELU → motor-fem `computed` → PyNite reconcilia → `qa-passed`, y un caso forzado de discrepancia → `qa-fail` que bloquea.

---

## Fuentes

- **Chequeo independiente Categoría 3 (BS 5975):** verificación por revisor **organizativamente independiente** del proyectista, que desarrolla **load cases, cálculos y análisis propios**; explícitamente **no** una revisión de cortesía ni *peer review* de las mismas cuentas; el disparador es el **riesgo** (consultado 2026-06-25): [Category 3 Checking and Independent Verification — Eadon Consulting](https://eadonconsulting.co.uk/engineering-services/category-3-checking-independent-verification/) · [The role of independent design checking in major projects — IABSE](http://thost-iabse-elearning.org/l12/data/downloads/reference.pdf) · [Concern that structural design may not have been checked — CROSS](https://www.cross-safety.org/us/safety-information/cross-safety-report/concern-structural-design-some-recent-1120)
- **PyNite — re-cálculo y envolventes:** análisis independiente; `combo_tags` para envolventes con combinación gobernante (consultado 2026-06-25): [Members — Pynite](https://pynite.readthedocs.io/en/latest/member.html)
- **Estado interno:** `HILO-V2_cierre-y-arranque-V3.md` §3 (re-ejecución de la QA con PyNite, carril *Estructurando 2.0*), `DECISIONES.md` D-009 (salvedad «sin el oráculo PyNite»), D-021 (estados), `privado/README.md` (dos llaves) — repo Aqyra, 2026-06-25.

---

*Para-firma de D-023 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md`. La IA opera; JM firma.*

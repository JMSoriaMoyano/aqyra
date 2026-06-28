# RFC C1 — evolución completa para las tres familias de P1 (sin más parches)

> **Para JM** · hilo de coordinación (Aqyra-Raiz) · 2026-06-28 · **propuesta; la adopción y la firma son de JM (PR a la zona protegida).**
> **Objetivo:** que las tres familias del Visor/Editor (P1·A edificación, P1·B trazado, P1·C normativa) se desarrollen **sin tope de contrato**, mediante **una sola evolución de C1 diseñada y completa** — **no** una sucesión de parches. Sustituye/absorbe la antigua RFC «IfcAlignment» y el parche puntual `losas[].huecos`.

---

## 1. Principio de diseño (dos patas)

1. **`alto.json` forward-open.** El esquema del cebo declara `additionalProperties` permitido: el cebo **emite por delante** de lo que el compilador autora; lo que C1 aún no entiende, lo ignora, nunca rompe. **El contrato nunca bloquea el preview.**
2. **Capacidad-completa, no parches.** Cuando una capacidad entra en C1, entra **entera y genérica** (no la rebanada mínima): huecos en cualquier anfitrión, **cualquier** `ifcClass` del catálogo, alineación con planta+alzado+sección+peralte. Así **C1 no se vuelve a tocar** por cada variante futura. El cebo sigue construyendo por **slices** (preview), pero contra un contrato ya completo.

> Esto es lo que pide «no más parches»: el coste de cada familia nueva o cada variante deja de ser un cambio de contrato; pasa a ser trabajo de cebo contra una superficie estable.

---

## 2. Las tres familias contra C1

| Familia | Qué necesita de C1 | Estado real |
|---|---|---|
| **P1·A edificación** | Huecos en cualquier elemento · envolvente poligonal · catálogo abierto de clases | El compilador ya autora **perfiles poligonales** (`IfcArbitraryClosedProfileDef`), muros por segmento y un **handler genérico `elementos[]` por `ifcClass`** (catálogo bsDD). Lo que falta para cerrarla **entera**: **huecos generalizados** (hoy solo en muros) y declarar el catálogo de clases **abierto** (el ascensor `IfcTransportElement` y cualquier clase futura entran sin re-bump). |
| **P1·B trazado** | Autorar **`IfcAlignment` completo** | C1 **ya parsea** `IfcAlignment` (Ola 5, `iso19650-openbim` v0.5.0) y **ya lo genera** (`scripts/lineal/generate_test_ifc_lineal.py`: planta recta/clotoide/curva + alzado + peralte + georref). Falta **una sola vez**: el handler `alineaciones[]` en el compilador del cebo (`spec_to_ifc.py`) que reutilice esa maquinaria, definido **completo** (planta+alzado+sección+peralte), no por trozos. |
| **P1·C normativa/auditoría** | Nada | **Frontera-cero:** es lectura (audita/asiste); no añade primitivos al `alto.json`. |

---

## 3. La evolución de C1 (UNA versión nueva, completa)

Una versión de C1 (bump deliberado, retrocompatible) que cierra las capacidades **enteras**, de una vez:

1. **Huecos generalizados** como primitiva de autoría: `IfcOpeningElement`/`IfcRelVoidsElement` aplicable a **cualquier elemento anfitrión** que los admita (losas, cubiertas, muros —ya—), no un caso suelto.
2. **Catálogo de clases abierto:** el handler genérico `elementos[].ifcClass` autora **cualquier** `IfcClass` del catálogo bsDD (ascensor `IfcTransportElement` incluido) **sin tocar el contrato** en el futuro.
3. **Alineaciones completas:** `alineaciones[]` → `IfcAlignment` con planta (recta+arco+**clotoide**), alzado (rasantes+acuerdos) y sección barrida + peralte, reutilizando la maquinaria de Ola 5.
4. **Esquema `alto.json` forward-open** declarado (additive, `additionalProperties` permitido) — la garantía formal de «sin más parches».

**Golden única de C1 (Llave 1)** que prueba la versión entera: un `alto.json` con (a) huecos en **losa y muro**, (b) un elemento `IfcTransportElement`, (c) una alineación con **clotoide + acuerdo vertical** → compila un IFC válido, con la losa **vaciada**, el ascensor presente y un `IfcAlignment` **legible por el parser lineal existente**.

---

## 4. Adopción (regla de dos llaves) y reparto

`bump (versión nueva de C1, no parche) → golden → adoptar si verde → anclar → firma`:

- **Lado cebo (P1 / repo `Entorno`):** que `c1-bridge.ts` **emita** `losas/…[].huecos`, `elementos[].ifcClass` y `alineaciones[]` en el `alto.json`. Preview vivo, **sin export firmable**. Puede ir **ya**, contra el contrato completo.
- **Lado contrato/compilador (motor / `narracion-ifc` + `iso19650-openbim`, zona protegida):** implementar §3.1–§3.4 en `spec_to_ifc.py`, **bump** de `iso19650-openbim`, sembrar la **golden** de §3.
- **Anclaje:** subir la versión en `Entorno/integracion/versions.lock` **solo si la golden está verde**.
- **Llave 2:** **firma de JM**.

---

## 5. Reservado a JM

- Adoptar esta evolución de C1 y **cuándo** se hace el bump.
- La **firma** (Llave 2) cuando la golden esté verde.
- Si esta RFC pasa al `ROADMAP_cebo-anzuelo.md` como línea (hilo de estrategia).

*Procedencia: Aqyra-Raiz · hilo de coordinación · RFC de evolución completa de C1 para las familias de P1 · 2026-06-28.*

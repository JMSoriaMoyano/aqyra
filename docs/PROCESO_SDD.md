# Proceso SDD — obligatorio para toda funcionalidad de Aqyra

> Fuente única del **cómo se desarrolla** en Aqyra. Gobernado por `Aqyra-Raiz`. Cualquier agente
> (IA o humano) que vaya a tocar el código LEE esto antes de escribir una línea. Los principios
> viven en `docs/base-standards.md` (`AGENTS.md`); esto es el **procedimiento operativo**.

## Regla de oro

**Ningún código de funcionalidad entra sin pasar por el flujo SDD.** El código implementa la
especificación; nunca al revés. La documentación (contrato + esquema + golden) es la fuente de
verdad. Un PR que toca `engines/`, `services/`, `apps/`, `packages/core|packs/`, `documentos/` o
`packages/contracts/` **debe traer** su cambio en `openspec/changes/<change-id>/`. El CI lo
comprueba (`tools/check_sdd_conformance.py`); CODEOWNERS exige tu revisión en la frontera; el
merge es tu firma (Llave 2).

## El flujo, paso a paso

1. **`enrich-us <ticket|texto>`** — refina la historia (lee Jira si le das un ID; proyectos
   `AQYRAALL` / `BCFMAN` / `INDUS` / `INFRA`). Planificación con **Opus high reasoning**.
2. **`opsx:propose <change-id>`** — crea `openspec/changes/<change-id>/` con `proposal.md`
   (qué/por qué), `design.md` (cómo) y `tasks.md` (pasos, Step 0 = rama). Aquí se listan las
   **decisiones a ratificar**.
3. **Ratificar decisiones con JM** — OK explícito ANTES del código (patrón C3 D1–D10 / C5
   D11–D15). Se anclan en `packages/contracts/Cn-*/DECISIONES.md` (y `apps/visor/DECISIONES.md`
   si aplica).
4. **`opsx:apply <change-id>`** — implementa las tasks de una en una (baby steps, solo lo
   afectado). Contract-first para capacidad nueva: contrato + esquema + pack + **golden ANCLADA**
   antes que el engine. Test-first.
5. **`adversarial-review <change-id>`** — verificación mecánica (tests/lint/typecheck/build/tasks)
   + pase adversarial.
6. **`opsx:archive <change-id>` → `commit`** — archiva y abre el **PR**. CODEOWNERS revisa la
   frontera; el gate (Llave 1) debe estar verde; el **merge/firma es de JM** (Llave 2).

## Tipos de capacidad (cómo encuadrar una petición)

- **Extender una capacidad viva** (p. ej. más presupuesto sobre C5): change nuevo, decisiones,
  engine/golden, PR. No se crea contrato nuevo si el existente basta (forward-open).
- **Capacidad nueva** (p. ej. huella de carbono): **contract-first** — primero el contrato `Cn`
  (`contrato.md` + `*.schema.json` + pack + `GOL-*` ANCLADA), decisiones ratificadas, DESPUÉS el
  engine, DESPUÉS el visor si procede.
- **Documento / operador** (p. ej. pliego de condiciones): capa `documentos/` orquestada por el
  operador **C7**, que COMPONE salidas autoritativas de otras capacidades (C3 cumplimiento, C5
  presupuesto…) en un `.docx` firmable — no recalcula (patrón `documento-presupuesto`).

## Reglas duras (no negociables)

- **Git solo por `.bat` en el host** (nunca `git` desde el sandbox). Verdad del árbol por lectura
  con ruta explícita del host.
- **Dos llaves**: gate verde en CI (Llave 1) + firma GPG / merge de JM (Llave 2). La IA propone;
  **no certifica**.
- **Un fallo se corrige en el código, NUNCA aflojando la golden.** Esquemas **forward-open** (solo
  añadir claves, no cambiar semántica).
- **No tocar la zona firmada** (golden/tags GPG existentes) ni `sdd-aqyra` desde el producto.
- **Reservado a JM**: alcance, qué entra en cada change, y las firmas.

## Excepción (hotfix legítimo sin spec)

Rarísima. Si un arreglo urgente no admite spec previa, el PR se etiqueta **`sin-spec`** y JM lo
aprueba a conciencia (revisión humana explícita). No es la vía normal: es la excepción auditable.

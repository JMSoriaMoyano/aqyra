# Diagnóstico typecheck — bloquea la firma del cebo (para el hilo P1/visor)

> **De:** hilo de coordinación (Aqyra-Raiz) · **Para:** hilo P1/visor · **2026-06-28**
> El VERIFICAR fresco (28/06 15:45) dejó la **golden VERDE** (parking 7/7, columns 35/35, suite 144/144) pero el **typecheck en ROJO** (3 errores en `Entorno/publico/demo/src`). El gate de Llave 1 del visor es el VERIFICAR completo (typecheck **y** tests), así que la firma está bloqueada hasta dejarlo limpio. Abajo, los 3 con su parche exacto.

> *Nota de método:* la vista de la shell sobre `Entorno` estaba **desfasada** (mostraba copias antiguas de los `.ts`); este diagnóstico está hecho sobre el disco real (file-tools del host), líneas confirmadas.

---

## 1. ⚠️ `diseno.ts:940` — TS2367 (NO es ruido: rama muerta = bug funcional)

```ts
// línea 850 — el tipo de a.target NO incluye "openings":
target?: "cores" | "corridor" | "rooms" | "grid" | "partitions" | "program"; // type=clear
...
// línea 940 — por eso esta rama es INALCANZABLE:
else if (a.target === "openings") bInput.openings = undefined;
```

**Consecuencia real:** la carpintería (`openings`, que SÍ se **añade** con `type:"carpentry"`, líneas 927–932) **no se puede BORRAR** con la acción `clear`. Todas las demás categorías (cores, corridor, rooms, grid, partitions, program) sí se limpian; openings queda como excepción silenciosa.

**Fix recomendado (corrige el bug, no lo tapa): añadir `"openings"` al union.**

```ts
target?: "cores" | "corridor" | "rooms" | "grid" | "partitions" | "program" | "openings"; // type=clear
```

Con eso la rama 940 pasa a ser alcanzable, desaparece el TS2367 y se restaura la simetría añadir/borrar de la carpintería.

---

## 2. `model.ts:138` — TS6133 `DEFAULT_RISER` declarado y nunca usado

```ts
const DEFAULT_RISER = 0.18; // contrahuella (m), DB-SUA
```

El demo solo **coloca** la escalera (IfcStair, líneas 464–475) y **delega a C1** la geometría real (peldaños/contrahuella) — la constante quedó huérfana.

**Dos salidas, decide el hilo:**
- **(a) Borrarla** — minimiza riesgo; el dato de contrahuella ya es responsabilidad de C1.
- **(b) Cablearla** al payload de la escalera (líneas 467–475) si se quiere **emitir** la contrahuella a C1 como dato de entrada. Es una decisión de diseño del puente, no de la firma.

---

## 3. `diseno.ts:793` — TS6133 `starterChips()` función sin uso

```ts
function starterChips(items: string[]): void { ... }
```

Función no referenciada (probable resto de los "chips" de arranque del chat).

**Fix:** borrarla, o cablearla a la UI si se pretendía mostrar. Lo más limpio para desbloquear: borrarla.

---

## 4. Cierre

Aplicados los 3 (el #1 es el importante), **re-correr `VERIFICAR_V3.bat`**; con typecheck **y** tests en verde, la Llave 1 queda limpia y firmamos los dos tags (`cebo-elementos`, `cebo-parking`) en una sola pasada. El paquete de firma sigue preparado en `PAQUETE-FIRMA_cebo-elementos-parking.md`.

*Procedencia: Aqyra-Raiz · hilo de coordinación · diagnóstico para el hilo P1/visor · 2026-06-28.*

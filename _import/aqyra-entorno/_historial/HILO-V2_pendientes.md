# Aqyra · V2 (pre-proceso) — Temas PENDIENTES

> **Qué es:** lista de lo que queda abierto del hilo de desarrollo de V2 (pre-proceso estructural visual). Solo pendientes de V2; **no incluye alcance de V3**. La IA propone; **JM decide y firma**. Todo lo de V2 vive en `publico/` y es `proposal` revisable.
> **Fecha:** 2026-06-25.

---

## 1. Tipificación de uniones (rígido / articulado) — NO implementado
La 2.ª mitad de la "terna" (superficies ya hecho; uniones aplazado y nunca implementado).
- Nudos **rígidos por defecto**; comando para **liberar** un extremo/nudo a **articulado** (releases).
- Visualizar el tipo de unión (p. ej. articulado con marcador distinto) y persistirlo en `Pset_AqyraStructural` (release por extremo de barra).
- El **criterio** de qué unión es rígida/articulada por norma es anzuelo (V4); aquí, mecánica editable como `proposal`.

## 2. Derivación robusta de cajones de hormigón — resuelve los desajustes del depósito (REIMPLEMENTADO por PLANO MEDIO/OBB · `proposal`, pendiente re-sellado en Windows)

> **Estado (2026-06-25, 2.ª iteración):** la 1.ª versión (descomposición por **triángulos**) se afinó sobre cajas sintéticas perfectas y **fallaba con el IFC real** del depósito (`DepositoDecopakEnterrado.ifc`, IFC2X3). Diagnóstico sobre el modelo real: los muros "50 cm" de Revit salen como **`IfcFacetedBrep`** y extrusiones **`IfcBooleanClippingResult`**, y las losas como **CSG**; la teselación cruda se fragmenta (un muro → **39 parches**), el filtro retenía **2 láminas por muro** y el relleno rectangular **sobresalía**. Render resultante: muros ladeados, láminas duplicadas/desfasadas y planos sobredimensionados.
>
> **Reescrito** a **plano medio por caja orientada (OBB)** en `publico/visor/src/idealize.ts` (`surfaceFromBox`): de los 3 ejes principales de la nube, el de **menor extensión = espesor**; su **plano medio = la lámina**, con **espesor y orientación reales**, sesgo por tipo (muro→vertical, losa→horizontal). Sin clustering frágil; solo usa la nube de vértices (se revirtió la plomería de `tris`). Activado por `surfaceMode:"obb"` desde `deriveStructural`; el modo `"plane"` heredado se conserva para los tests sintéticos. **Validado sobre la geometría REAL del depósito** (reconstruí la teselación de extrusiones+breps en Python): los **7 muros** salen como láminas verticales con espesor real (0,50/0,52/0,63/0,50/0,54/0,20/0,20) y la losa horizontal 0,60. **Pendiente:** el **cierre automático de la caja** aún no engancha en el depósito real (7 segmentos a >0,7 m → grados [1,1,1,0,0,1,0]); cada lámina renderiza bien, pero falta afinar la tolerancia de cosido / extender aristas. **El contorno poligonal exacto desde `IfcExtrudedAreaSolid`** (para muros en L/recortados) queda como capa siguiente: exige leer el perfil vía web-ifc y **no se ha podido verificar en sandbox**. **JM re-sella en Windows** (`cd publico; npm run typecheck; npm test`) — ver §5. Test: `publico/visor/test/idealize-faces.test.ts` (7 tests OBB).

Este es el punto que **corrige los desajustes** observados en el depósito enterrado (y el caso EST-02): muros **torcidos**, láminas que **no casan** en las aristas, y caras marcadas **no-plano (rojo)** que deberían ser muros limpios.

**Causa raíz.** Hoy idealizo cada elemento reduciéndolo a **UN plano PCA por elemento**. Para muros/cajones **facetados, gruesos o huecos** (los `IfcWall` del depósito no traen perfil extruido limpio) eso falla en tres frentes a la vez:
1. la orientación del plano sale **ladeada** (de ahí el muro torcido) — la verticalización lo mitiga pero no lo cura;
2. el **contorno** (hull de toda la nube) sale sucio → las láminas **no casan** en las esquinas;
3. el **espesor aparente** (extensión perpendicular del conjunto) dispara el flag **no-plano** → muros limpios salen en rojo.

**Solución vigente: plano medio por OBB (una lámina por elemento).** *(✔ = hecho; ⏳ = pendiente)*
1. ✔ **Plano medio por OBB** (`surfaceFromBox`): 3 ejes principales de la nube → eje de menor extensión = **espesor**; plano medio perpendicular = **lámina**, con espesor y orientación reales. Sesgo por tipo (muro→lámina vertical, losa→horizontal). Determinista (PCA por iteración de potencia).
2. ✔ **Robusto frente a geometría real** (brep/recorte/CSG): no clusteriza triángulos, así que no se fragmenta. Validado sobre el depósito real (7 muros + losa).
3. ✔ **Sin artefactos:** `planar=true` siempre (sin falso no-plano), `skewed=false` (la normal es el eje de espesor, sin tilt), contorno = rectángulo del OBB en el plano medio (no sobresale en muros rectangulares).
4. ✔ **Espesor:** `thick` si t/luz > 0,1 (placa gruesa/sólido), reutilizando el flag.
4b. ✔ **Filtro de elementos degenerados** (`minSurfaceSpan`, 1,0 m): un elemento cuya dimensión menor en el plano es diminuta (los "muros de 20 cm" del depósito salen de 22 m × 0,1–0,7 m: canto/bordillo/upstand, no muro) **no se idealiza como lámina**. Esto eliminó las **tiras magenta diagonales** que cruzaban el render (eran esos slivers pintados grueso/rosa). Quedan 5 muros de 50 cm + losas.
5. ⏳ **Cosido en caja cerrada:** `groupCores`/`buildCoreShell` siguen activos, pero en el depósito real los 7 segmentos no comparten esquinas dentro de 0,7 m → la caja **no se reconoce cerrada** todavía. Afinar tolerancia de cosido o extender aristas de las láminas hasta los encuentros.
6. ⏳ **Contorno poligonal exacto** desde `IfcExtrudedAreaSolid` (perfil + eje·profundidad) para muros en L/recortados: capa siguiente; requiere leer el perfil vía web-ifc (no verificable en sandbox).

**Resultado esperado:** el depósito sale como una **caja de muros planos rectos, cerrada**, sin torcidos ni falsos no-planos; idéntico tratamiento sirve para el núcleo EST-02 (hoy cubierto solo con la **columna-cajón equivalente**, que se mantiene como alternativa).

**Gobierno:** es **mecánica** (cebo), `proposal` revisable (preview/diff); nunca malla cerrada dada por buena. *(La resolución FE del cajón cosido queda fuera de V2.)*

**Verificación:** test con un **cajón sintético facetado** → N caras planas limpias y cosidas, **sin** `skewed` ni falsos no-planos, caja cerrada.

## 3. Carga por área (Indicación A2)
- Aplicar la presión q (kN/m²) sobre el **área REAL** (ya calculada) → repercutir como **cargas lineales en vigas de borde**.
- Separar formalmente en el modelo de datos el **diafragma-rigidez** (vínculo, no aporta peso) de la **superficie-de-carga** (área tributaria).
- Mostrar la **carga total resultante (kN)** para validación.

## 4. Afinado de umbrales (a la vista de los modelos reales)
- **Tolerancia de coincidencia de nudos** (D-014, 150 mm): valor por defecto y/o derivarlo de las unidades del modelo.
- Umbrales de **planar / grueso / torcido**.
- Posible **sobre-marcado de "no-plano"** tras verticalizar muros (al forzar la normal horizontal, una cara irregular puede dar espesor aparente mayor) — revisar si conviene relajar el umbral de planaridad.

## 5. Verificación y convenios
- **Re-sellado VERDE en Windows (2026-06-25 21:46):** `typecheck` OK (exit 0) + **`vitest run` 62/62 tests en 11 ficheros** (exit 0), incluido el plano medio por OBB del §2 (`idealize-faces.test.ts`, 8 tests, con el filtro de elementos degenerados) y `idealize.test.ts` (17). Se corrigió de paso un `noUnusedLocals` latente (`postState` muerto en `demo/src/calculista.ts`). Lanzado con `RESELLAR.bat` → vuelca a `resellado_resultado.txt`. *(El sandbox de la IA no puede sellar: enlaces pnpm a rutas Windows + mount cacheado que trunca los fuentes; por eso se ejecuta en la máquina real.)*
- **Convenio de unidades/signos de carga** (D-015): hoy provisional (kN, gravedad −Y); **confirmarlo** antes de conectar al cálculo.
- Aplicar/confirmar el **bump SemVer** de `@aqyra/embed` (ahora 0.4.0) al cerrar el corte.

## 6. Cierre de producto
- Consolidar **DoD y demo** del pre-proceso sobre Decopak HQ (y validar el depósito).
- **Gate legal** antes de publicar `publico/` (D-003): validación jurídica + escaneo del árbol real de dependencias (bloquea si aparece GPL/AGPL).
- **Sello del release N1.1** del núcleo (suite golden verde + tag GPG firmado por JM) — residual de `DECISIONES.md` D-005.
- Verificación autoritativa de **marca/dominio** Aqyra y relación con Aqyra-CDE (residual D-004).

## 7. Operativa (no bloquea, pero conviene)
- Lanzador del visor: usar `INICIAR_VISOR_npm.bat` (un clic, npm); no dejar caer el servidor de Vite mientras se usa el visor.
- Recordatorio externo: re-ejecutar la QA del cálculo con **PyNite** en entorno certificado (carril *Estructurando 2.0*) — no bloquea V2.

---

*Pendientes de V2 · proyecto Aqyra · IA (PM / Ing. BIM-IFC) · 2026-06-25. La IA opera; JM firma.*

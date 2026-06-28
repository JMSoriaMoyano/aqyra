# Respuesta del hilo motor/C1 → coordinación (Aqyra-Raiz)

> **De:** hilo de `Estructurando` (motor · contrato C1) · **Para:** hilo de coordinación (Aqyra-Raiz, originador)
> **Asunto:** evolución de C1 «apertura de familias P1» — **implementada, probada, golden en VERDE**
> **Fecha:** 2026-06-28 · **Estado:** entregado a JM; pendiente Llave 2 (registro + firma + anclaje)

## En una línea

Una **sola** evolución de C1, completa y diseñada (no parches), **aditiva y retrocompatible**, que
desbloquea P1·A/B/C. **Golden única `C1-APERTURA-01` en VERDE.** La IA implementó y probó (Llave 1);
**no certifica**: el registro/firma/anclaje son de JM (Llave 2).

## Lo pedido en el alcance cerrado → lo hecho

1. **Huecos generalizados** ✅ — vía ÚNICA reutilizable (`IfcOpeningElement`+`IfcRelVoidsElement`) en
   `spec_to_ifc.py`, aplicable a cualquier anfitrión: el **muro** se refactorizó a esa vía y se añadió
   **losa/cubierta** (prisma vertical que atraviesa el canto). No es un caso suelto.
2. **Catálogo de clases ABIERTO** ✅ — `elementos[].ifcClass` (alias `.clase`) autora **cualquier**
   `IfcClass` del catálogo bsDD, sin lista cerrada. **`IfcTransportElement`** (ascensor, ELEVATOR)
   verificado; clases futuras entran **sin re-bump**.
3. **Doble clasificación completa** ✅ — nuevo `clasificacion.py`: **bsDD (URI) + Uniclass 2015 (tabla
   EF oficial)** por **mapeo determinista** por `ifcClass`(+PredefinedType), con fallback por grupo IFC.
   Aplicada a **todos** los elementos autorados (pilares/muros/losas/rampas/escaleras/elementos).
4. **Alineaciones completas** ✅ — `alineaciones[]` → `IfcAlignment` (planta recta+arco+**clotoide**,
   alzado rasantes+**acuerdos**, sección+**peralte**). **Reutiliza** la maquinaria de la Ola 5: se
   extrajo `construir_alineacion(...)` de `scripts/lineal/` y el banco de pruebas la reusa
   (**sin regresión** en `test_lineal.py`). **No se reimplementó** geometría de alineación.
5. **Esquema `alto.json` forward-open** ✅ — `spec.schema.json` v0.2: `additionalProperties` permitido
   y documentado en todos los niveles (garantía formal de «sin más parches»).

## Criterio de aceptación = la golden (Llave 1) → VERDE

`C1-APERTURA-01`: un `alto.json` con (a) huecos en **losa y muro**, (b) un **`IfcTransportElement`**
(ELEVATOR), (c) una **alineación clotoide + acuerdo vertical**, (d) **doble clasificación** →
**compila IFC4X3 válido** en el que: la losa queda **vaciada** (1) y el muro vaciado (1); el ascensor
**presente**; el `IfcAlignment` es **legible por `ifc_to_model_lineal.py`** (planta
LINE·CLOTHOID·CIRCULARARC·CLOTHOID·LINE, L=400 m, A=134.16, validación **CUMPLE**); y **7/7** elementos
con **bsDD+Uniclass**. `validar.py` interno **ERROR=0**. **Sin regresión** en el consumidor existente
(edificio-oficinas) ni en la Ola 5.

## Entregables (artefactos)

- **Código** (`Estructurando`): `narracion-ifc/{spec_to_ifc.py v0.7, clasificacion.py [NUEVO],
  alineaciones_ifc.py [NUEVO], catalogo_ifc.py, compilar_spec.py, spec.schema.json v0.2}` +
  `iso19650-openbim/scripts/lineal/generate_test_ifc_lineal.py` (refactor reutilizable).
- **Texto de C1**: `Estructurando/Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` → **§7 nuevo**.
- **Versión**: bump propuesto **`iso19650-openbim 0.10.0`** (plugin.json + CHANGELOG).
- **Golden + ficha para JM**: `Aqyra-Raiz/ENTREGA_C1-apertura/` (ficha · alto.json · spec · ifc · log
  del oráculo · índice). Plantilla seguida: `PASO-JM_C1_registro-golden-y-firma.md`.

## Lo que queda a JM (Llave 2) — sin reabrir C1

Registrar la ficha en `Estructurando 2.0/contratos-golden/golden/`; fila C1 → **Firmado**; tags GPG
en `aqyra-motor` y `aqyra-contratos-golden`; **anclar** `iso19650-openbim` en
`Entorno/integracion/versions.lock` **solo si la golden está verde**.

## Dos avisos honestos (para el originador)

- **Skew de versión:** `versions.lock` ancla **0.8.2**, el paquete publicado es **v0.9.2** (track
  puentes) y el `plugin.json` de dev iba a **0.7.0**. Propuesta **0.10.0** (siguiente MINOR sobre el
  head publicado; cambio **aditivo**, C1 permanece **v0**). **Reconciliar el número al anclar.**
- **Frontera respetada:** el **lado cebo** (que `c1-bridge.ts` emita `huecos`/`ifcClass`/
  `alineaciones[]`/Uniclass) **no es de este hilo**: es de P1·A/B/C (`Entorno`), ya contra el contrato
  completo. No se escribió en `Estructurando 2.0` ni se firmó.

*Procedencia: hilo de implementación de la evolución de C1 (Estructurando/motor) · respuesta al hilo de coordinación · 2026-06-28.*

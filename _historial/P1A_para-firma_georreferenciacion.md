# P1·A — Para firma de JM: georreferenciación del emplazamiento + Norte real/soleamiento

> ✅ **FIRMADO (dos llaves) — 2026-06-28.** Llave 1: golden VERDE en Windows (`VERIFICAR_V3`: typecheck sin errores; **17 ficheros / 119 tests**, incl. `author.test.ts` 15 y `solar.test.ts` 9). Llave 2: **firma de JM**. **Adoptado:** `@aqyra/visor 0.3.0` anclado en `Entorno/integracion/versions.lock` (entrada `visor-ifc`). C1 sin cambios.

**Fecha:** 2026-06-27 · **Procedencia:** sub-dirección de P1 (Visor/Editor IFC) · Aqyra · IA prepara y propone; **JM firma**.
**Regla aplicada:** cambio en la frontera de C1 ⇒ **bump → golden → adoptar si verde**; anclar en `versions.lock`.

---

## 1. Qué se ha preparado

El activo deja de "flotar en el origen (0,0,0)": el autor de IFC puede ahora **situar y orientar** el modelo en el mundo real, como **entidad IFC real** (no ayuda visual), y se añade la primera herramienta de ayuda al diseño sobre el emplazamiento (Norte real + soleamiento).

- **`author.ts`** — `createSpatial` admite un bloque **`georef`** opcional y emite `IfcProjectedCRS` (CRS proyectado: EPSG, datum, proyección, huso) + `IfcMapConversion` (origen Eastings/Northings/cota, **rotación a Norte real**, escala) sobre el contexto geométrico. **Opt-in**: sin `georef` la salida es **byte-idéntica** al incremento previo (golden anterior intacto).
- **`solar.ts`** (módulo nuevo, puro) — Norte real (`trueNorthInProject`, de la rotación de `IfcMapConversion` a los ejes de la maqueta), posición del Sol (`sunPosition`, altitud/azimut) y sombra (`shadow`). Listo para cablear a la maqueta del skin Diseño. *Aún no toca la UI viva de `diseno.ts`* (se cablea tras tu visto bueno).

## 2. Decisiones tuyas aplicadas (2026-06-27)

| Decisión | Cierre |
|---|---|
| CRS/EPSG por defecto | **Configurable por proyecto** — `epsg` es obligatorio en la semilla; no se cablea default de despacho. |
| Fuente del emplazamiento | **Catastro INSPIRE** — de la ref. catastral salen eastings/northings. |
| Alcance v0 herramientas | **Georref + Norte real + soleamiento**. |
| IfcFacility primero | **Edificación** (Site/Building). Obra lineal (IfcAlignment/Road, IFC4.3) → incremento posterior. |

## 3. Dato real de anclaje (Can Cabassa)

Parcela **0419901DF2901H** · *CM Can Cabassa 32, Sant Cugat del Vallès (Barcelona)*.
Centroide vía Catastro **OVC `Consulta_CPMRC`** (formato abierto, diff-able):

- **ETRS89 / UTM 31N (EPSG:25831):** E = **420286.12**, N = **4591705.32**
- **ETRS89 geográficas (EPSG:4326):** lat = **41.4730°N**, lon = **2.0453°E** (latitud usada en el soleamiento)

## 4. Frontera y bump propuesto

La extensión es **aditiva y opt-in** sobre la salida del autor IFC: el parser/loader (C1) sigue reabriendo el modelo sin cambios. No es ruptura de contrato.

- **Contrato C1:** se mantiene en **v0** (sin breaking change del parser).
- **Bump del paquete `@aqyra/visor`:** **0.2.0 → 0.3.0** (MINOR, funcionalidad aditiva).
- **Anclar** en `Entorno/integracion/versions.lock` (`visor-ifc`) **solo si la golden queda verde**.

## 5. Las dos llaves

- **Llave 1 — golden (la corres tú en Windows; la IA NO certifica).**
  La suite del visor incluye ahora:
  - `test/author.test.ts` → georref: emite `IfcProjectedCRS`/`IfcMapConversion`, valores reales de Catastro, rotación `rotationDeg=0 ⇒ XAxisAbscissa=1/XAxisOrdinate=0`, round-trip del loader, y **guarda opt-in** (sin `georef` no aparece ninguna entidad de georref).
  - `test/solar.test.ts` → Norte real + altitud solar (solsticios/equinoccio) en la latitud de Can Cabassa + sombra.
  Ejecutar con la herramienta de test del visor (p. ej. `VERIFICAR_V3.bat` / `npm test` del paquete).
  *Nota: el soleamiento ya se verificó de forma independiente (verano 71.96° vs teórico 71.97°, invierno 25.09°, equinoccio 48.48°). El golden de georref requiere el wasm de web-ifc y se corre en tu máquina.*
- **Llave 2 — tu firma** sobre el release una vez la golden esté verde.

## 6. Ficheros tocados

- `publico/visor/src/author.ts` — interfaz `GeoRef` + emisión de georref (opt-in).
- `publico/visor/src/solar.ts` — **nuevo**: Norte real + soleamiento.
- `publico/visor/src/index.ts` — exporta `GeoRef`, `sunPosition`, `trueNorthInProject`, `shadow`, `SunPosition`.
- `publico/visor/test/author.test.ts` — golden de georref.
- `publico/visor/test/solar.test.ts` — **nuevo**: golden de soleamiento/Norte.

## 7. Nota operativa (no bloqueante): desfase de sync Windows↔Linux

El sandbox Linux y el árbol Windows mostraban **versiones distintas del mismo fichero** (p. ej. `index.ts`/`author.ts` en generaciones de sync diferentes) y el sandbox solo tiene **shims de herramientas de Windows** (`vitest.CMD`), sin espacio en disco. Por eso **la golden la corres tú**. Toda la edición se hizo sobre el árbol canónico (Windows). Conviene dejar asentar el sync antes de tu `npm test`.

## 8. Siguiente incremento (tras tu firma)

1. Cablear `solar.ts` a la maqueta de `diseno.ts` (alinear cardinales N-S-E-O al Norte real; sombra por fecha/hora).
2. Integración viva con **Catastro INSPIRE WFS** (parcela GML completa, no solo centroide) para límites/retranqueos.
3. **IfcFacility / IfcAlignment** (IFC4.3) para obra lineal — `IfcMapConversion` con `ScaleY/ScaleZ` del 4.3.

*La IA prepara y propone; la adopción y la firma son de JM.*

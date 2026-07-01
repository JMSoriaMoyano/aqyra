# P1·A — Para firma de JM: primer corte de reconstrucción del entorno

> ✅ **FIRMADO (dos llaves) — 2026-06-28.** Llave 1: golden VERDE en Windows (mismo run `VERIFICAR_V3` 28/06: `environment.test.ts` 10 + `terrain.test.ts` 6, dentro de 17 ficheros/119 tests). Llave 2: **firma de JM**. **Adoptado:** `@aqyra/visor 0.4.0` (entorno «planta del entorno» + terreno/topografía) anclado en `Entorno/integracion/versions.lock`. Frontera nueva (no C1). **Abierto NO bloqueante (heredado de §"Cabos a confirmar"):** confirmar en vivo el GML de **Catastro BU** (edificios) y el endpoint **CartoCiudad viales**; degradan con elegancia si difieren (ajuste menor de parser).

**Fecha:** 2026-06-27 · **Procedencia:** sub-dirección P1 · Aqyra · IA prepara y propone; **JM firma** (dos llaves). Frontera **nueva** (no C1).

## Qué se ha implementado (según tus 6 decisiones + 4 confirmaciones)

La "planta del entorno" como **contexto visual** alrededor del activo georreferenciado: parcela propia + vecinas y huellas de edificios (Catastro), viales (CartoCiudad), normalizado a **GeoJSON abierto (EPSG:25831)** y **congelable como snapshot**. **No toca el IFC del activo.**

- **`visor/src/environment.ts`** (núcleo PURO): tipos + parser GML→GeoJSON sin dependencias (`parseParcels`, `parseBuildings`, `parseRoads`), altura de vecinos = nº plantas × **altura tipo 3,0 m configurable**, `toCollection`/`toSnapshot`, y `StateEnvProvider` (URLs del proxy).
- **`visor/test/environment.test.ts`** + **`test/fixtures/catastro_parcels_cancabassa.xml`**: golden con **fixture REAL** capturado (3 parcelas: 11.884 / 770 / 759 m²), más edificios/viales sintéticos.
- **`demo/vite.config.ts`**: proxy **`/__aqyra/geo`** (resuelve CORS y el GML que el navegador no surfacea) → Catastro CP (`GetNeighbourParcel`), BU (`GetAllConstructionByParcel`), CartoCiudad viales.
- **`demo/entorno.html`**: página de contexto servible — carga el entorno por ref. catastral, dibuja la planta (parcela del activo resaltada, vecinas, edificios con etiqueta `nº plantas · altura`, viales) y descarga el **snapshot**.
- **`visor/src/index.ts`**: exporta el módulo.

## Verificación independiente hecha por la IA (no es la golden)

El parser es JS puro: lo corrí en sandbox contra el fixture real → **3 parcelas con refcat y área correctos, anillos cerrados, coords E-N**; altura 4 plantas → 12 m; vial 3 puntos. El golden oficial lo corres tú.

## Las dos llaves

- **Llave 1 — golden (la corres tú en Windows):** `npm test` / `VERIFICAR_V3.bat` en `publico`. Incluye `environment.test.ts` (entorno) además de `author.test.ts` (georref) y `solar.test.ts` (soleamiento).
- **Llave 2 — tu firma** cuando esté verde.

## Cómo probarlo en el visor

1. `INICIAR_VISOR_npm.bat` (o `npm run dev` en `publico/demo`).
2. Navega a **`http://localhost:5173/entorno.html`** → se carga Can Cabassa; cambia la ref. catastral o la altura/planta y pulsa "Cargar"; "Congelar snapshot" descarga el GeoJSON.

## Cabos a confirmar (honestidad)

- **Edificios (Catastro BU):** el parser sigue el esquema INSPIRE-BU 3.0; **no pude capturar el GML real de BU** este turno (atasco de caché del navegador). Se confirma en tu primera carga en vivo; si el prefijo/atributo difiere, es ajuste menor del regex.
- **Viales (CartoCiudad):** endpoint/typename `wfs-vial` **a confirmar en vivo**; si falla, la página degrada con elegancia (0 viales) sin romper parcelas/edificios.
- **Sync:** edición sobre el árbol Windows (canónico); el sandbox no corre la golden (shims Windows). 

## Bump propuesto

`@aqyra/visor` 0.3.0 → **0.4.0** (aditivo). Anclar en `versions.lock` solo si la golden queda verde. C1 sin cambios.

## Siguiente (tras tu firma)

Confirmar BU/viales en vivo; afinar parser (huecos/curvas); cablear el contexto a la maqueta 3D del visor junto al activo y al soleamiento; y, más adelante, el plugin ICGC (alta resolución) y la topografía.

*La IA prepara y propone; adopción y firma de JM.*

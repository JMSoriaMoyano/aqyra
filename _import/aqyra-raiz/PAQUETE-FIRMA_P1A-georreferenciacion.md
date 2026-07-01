# Paquete de firma (2ª llave) — P1·A Georreferenciación + Norte real / soleamiento

**Preparado por:** hilo de coordinación (Aqyra-Raiz) · 2026-06-28 · **Fuente:** `Entorno/P1A_para-firma_georreferenciacion.md`.
**Para:** JM. La IA prepara y propone; **correr la golden y firmar son tuyos.**

> Objetivo de este paquete: que puedas **despachar la firma en una sentada** — qué correr, qué tiene que salir verde, qué firmar y qué anclar. Es el primero de la cola; desbloquea el resto de P1.

---

## 1. Qué firmas (en una línea)

Que el autor de IFC puede **situar y orientar el modelo en el mundo real** como entidad IFC real (`IfcProjectedCRS` + `IfcMapConversion`, **opt-in**), más la primera ayuda de diseño sobre el emplazamiento (**Norte real + soleamiento**). Es **aditivo**: sin bloque `georef` la salida es **byte-idéntica** a la anterior. **No toca el contrato C1.** Sigue siendo **cebo** (sin export firmable).

Ficheros del incremento: `publico/visor/src/author.ts`, `src/solar.ts` (nuevo), `src/index.ts`, `test/author.test.ts`, `test/solar.test.ts`.

## 2. Antes de empezar (no bloqueante, pero evita un falso rojo)

- Deja **asentar el sync Windows↔Linux** antes de lanzar los tests (hubo desfase entre el árbol Windows canónico y el sandbox). Trabaja sobre el **árbol Windows**.

## 3. Llave 1 — correr la golden (en tu Windows)

1. En `Entorno/publico`: ejecuta **`VERIFICAR_V3.bat`** (o `npm test` del paquete del visor).
2. La suite incluye ahora `author.test.ts` (georref), `solar.test.ts` (soleamiento) y `environment.test.ts` (entorno).

**Verde = se cumple TODO esto** (criterios de aceptación):

- [ ] `IfcProjectedCRS` + `IfcMapConversion` **se emiten** con el bloque `georef`.
- [ ] Valores reales de Catastro para Can Cabassa: **E = 420286.12 · N = 4591705.32** (EPSG:25831).
- [ ] Rotación a Norte: `rotationDeg = 0 ⇒ XAxisAbscissa = 1 / XAxisOrdinate = 0`.
- [ ] **Round-trip del loader** (el visor reabre el modelo sin pérdida).
- [ ] **Guarda opt-in**: sin bloque `georef`, **no aparece ninguna entidad de georref** (salida byte-idéntica).
- [ ] Soleamiento en latitud de Can Cabassa (41,473°N): **verano ≈ 71,96° · equinoccio ≈ 48,48° · invierno ≈ 25,09°**.
- [ ] La suite termina sin fallos (exit 0).

> Si algo sale **rojo**: se arregla **en el código**, nunca aflojando el test (regla sagrada). En ese caso, me avisas y lo devuelvo al hilo P1.

## 4. Decisión previa que solo cierras tú (política de versión)

Hay un **desajuste de numeración** que conviene resolver antes de anclar:

- El paquete del repo se llama **`@aqyra/visor`** y el incremento propone **0.2.0 → 0.3.0** (MINOR, aditivo).
- El `Entorno/integracion/versions.lock` ancla hoy **`visor-ifc: "0.1.0"`**.

→ Decide si **`@aqyra/visor` y `visor-ifc` son la misma línea** (entonces el lock salta directo a **0.3.0**) o si hay que reconciliar nombre/numeración primero. Sin esto cerrado, el anclaje queda ambiguo.

## 5. Llave 2 — tu firma y anclaje (solo si la golden está verde)

1. **Firma**: registra tu visto bueno en `Entorno/P1A_para-firma_georreferenciacion.md` (deja fecha; es el cierre de la 2ª llave para este incremento del visor — el visor no usa manifiesto GPG como C5, basta tu firma registrada).
2. **Ancla** en `Entorno/integracion/versions.lock`, línea de `visor-ifc`, según la decisión del §4:

   ```
   # antes
   visor-ifc:            "0.1.0"   # base del visor (V1) · N0 artesanal, primer tag de producto (N1.1)
   # después (georref adoptada, golden verde + firma JM)
   visor-ifc:            "0.3.0"   # + georref opt-in (IfcProjectedCRS/IfcMapConversion) + Norte real/soleamiento · C1 sin cambios
   ```

   *(si decides reconciliar el nombre a `@aqyra/visor`, dímelo y ajusto la entrada).*
3. Avísame y **actualizo el panel y el roadmap** reflejando el anclaje.

## 6. Qué NO entra en este paquete (límites)

- **No** incluye el **Entorno/terreno** (planta Catastro/CartoCiudad + topografía): va en el **siguiente paquete (→0.4.0)**, que se firma después de éste.
- **No** toca **C1** (parser/loader sin cambios).
- **No** abre export firmable: el visor sigue siendo cebo.
- El cableado de `solar.ts` a la maqueta del skin Diseño es **incremento posterior** (tras tu visto bueno).

---

## Sello de dos llaves — P1·A Georreferenciación (visor 0.3.0) — ✅ CERRADO

- **Llave 1 (golden verde):** `VERIFICAR_V3` en Windows — typecheck OK · **17 ficheros / 119 tests** (author 15, solar 9)  ·  fecha: **2026-06-28**
- **Llave 2 (firma de JM):** **FIRMADO**  ·  fecha: **2026-06-28**
- **Adoptado:** `@aqyra/visor 0.3.0` (entrada `visor-ifc` en `Entorno/integracion/versions.lock`); `package.json` sellado a 0.3.0; C1 sin cambios.

> *Procedencia: hilo de coordinación · Aqyra-Raiz · paquete preparado para la firma de JM · 2026-06-28.*

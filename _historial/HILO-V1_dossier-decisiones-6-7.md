# Dossier de decisiones — V1 (§6 decisiones abiertas + §7 frontera)

> **Qué es:** evidencia para cerrar las cuatro decisiones abiertas del brief de V1 (`HILO-V1_brief_visor_industrializado.md` §6) y resolver la frontera de qué viaja con el Entorno (§7). **La IA propone; JM decide y firma.** Nada aquí es una decisión de negocio cerrada.
> **Método:** search-first; cada afirmación lleva fuente y fecha; se distingue **[VERIFICADO]** (leído en fuente primaria/oficial) de **[INFERIDO]** (deducción de la IA, sujeta a revisión).
> **Estado:** preparado por la IA (PM) · 2026-06-24 · pendiente de firma de JM.

---

## Resumen para la firma (una línea por decisión)

| # | Decisión | Recomendación de la IA (a confirmar por JM) |
|---|---|---|
| §6.1 | ¿BCF e IDS completos en V1, o IDS a V2? | **BCF completo (ver+crear) en V1**; **IDS: lectura + validación básica en V1**, autoría/edición de IDS a V2. El tooling web nativo existe para ambos. |
| §6.2 | web-ifc puro vs Speckle | **web-ifc + Fragments puro en V1.** Speckle no encaja con "web sin instalación" (exige servidor). Reevaluar Speckle solo si V5/SaaS pide capa de datos servidor. |
| §6.3 | Licencia OSS del cebo | El stack base es publicable: **web-ifc = MPL-2.0** (copyleft por fichero, no contagia), **components/fragments/ui = MIT**. Recomendación de licencia del repo `publico/`: **MIT o Apache-2.0**, respetando MPL-2.0 de web-ifc como dependencia. |
| §6.4 | Marca | Decisión de negocio de JM. La IA aporta criterios y una lista de candidatas; **no concluye**. |
| §7 | Qué viaja / qué se ancla | **Viajan:** benchmark + instantánea del gobierno + baseline narración→IFC. **Se quedan y se consumen anclados:** contrato C8 (CDE), corpus golden, motores de cálculo. |

---

## §6.1 — ¿BCF e IDS completos en V1, o IDS se difiere a V2?

### Evidencia

**Estándares (fuente primaria buildingSMART):**
- **IDS 1.0 es estándar oficial desde junio de 2024.** buildingSMART International anunció el 4 de junio de 2024 (Londres) que la versión 1.0 del *Information Delivery Specification* alcanzó el estatus de estándar definitivo; ya se recoge feedback para IDS 1.1 y 2.0. **[VERIFICADO]** (buildingSMART / BibLus, consultado 2026-06-24).
- **BCF 3.0 es la versión vigente**, con dos modos: fichero (`.bcfzip`, *roundtrippable*) y **API REST** (`/bcf/3.0/...`). **[VERIFICADO]** (buildingSMART Technical / BCF-API, consultado 2026-06-24).

**Tooling web en el stack elegido (That Open):**
- **BCF:** existe el componente **`BCFTopics`** en `@thatopen/components` — importa, exporta a `.bcfzip` y manipula incidencias BCF **en el navegador**. **[VERIFICADO]** (docs.thatopen.com, consultado 2026-06-24).
- **IDS:** existe el componente **`IDSSpecifications`** en That Open Engine — crea especificaciones a partir de los *facets* del esquema IDS (entity, attribute, property, material, classification, partOf) y verifica requisitos sobre el modelo (p. ej. `IfcDoor` → `FireRating`). **[VERIFICADO]** (docs.thatopen.com, consultado 2026-06-24).
- Como red de seguridad fuera de navegador, **IfcOpenShell** (ya en el baseline, 0.8.x) incluye soporte IDS (`ifctester`) y BCF. **[INFERIDO]** del baseline + docs IfcOpenShell 0.8.5.

### Lectura

El argumento del brief para diferir IDS ("acotar el alcance del primer entregable") era razonable **antes** de confirmar que hay componente web nativo. Confirmado `IDSSpecifications`, el coste de meter una validación IDS de lectura en V1 baja mucho: no hay que construir un motor de validación desde cero. El riesgo real no está en *validar*, sino en *autorear/editar* IDS (UI de creación de requisitos), que sí es trabajo de producto considerable y encaja mejor en V2 junto al pre-proceso (donde el usuario ya define requisitos sobre el modelo).

### Recomendación (a firmar por JM)

- **BCF — completo en V1:** ver y **crear** incidencias (alcance del DoD), exportando `.bcfzip`. El modo API REST se deja como gancho para V5/SaaS.
- **IDS — partido:** en V1, **cargar un IDS existente y ejecutar la validación** sobre el modelo (cumple el DoD "validar un requisito con IDS"). **Diferir a V2** la autoría/edición de IDS en la UI.
- Esto mantiene el DoD de V1 íntegro sin inflar el alcance de UI.

---

## §6.2 — Stack de datos: web-ifc puro vs Speckle

### Evidencia

- **web-ifc + Fragments** es 100% cliente: lee/escribe IFC en el navegador (WASM) y Fragments es el formato de teselado de That Open para rendimiento en modelos grandes. Sin servidor obligatorio. **[VERIFICADO]** (ThatOpen/engine_web-ifc; docs.thatopen.com/fragments, consultado 2026-06-24).
- **Speckle** es una plataforma servidor: "Speckle Server es el backend que da soporte a toda la funcionalidad"; el visor 3D vive en `speckle-server`; el self-host es vía Docker. Licencia **Apache-2.0**, **salvo** el módulo `packages/server/modules/gatekeeper/`, bajo *Speckle Enterprise Edition (EE) license*. **[VERIFICADO]** (github.com/specklesystems/speckle-server LICENSE, consultado 2026-06-24).

### Lectura

El principio no negociable nº2 de V1 es **"web sin instalación + tablet desde el día uno"**. Speckle, por diseño, requiere un servidor (alojar datos, versionado, federación servidor). Eso es exactamente la fricción que el brief llama "el enemigo" (la curva de entrada). Speckle es una capa de datos potente (versionado, colaboración, federación robusta) que tiene sentido **si y cuando** el Entorno necesite backend (V5/SaaS), pero introducirlo en V1 contradice el principio fundacional y añade un componente con un módulo EE no abierto que rozaría el límite cebo/anzuelo. Además, la decisión está marcada como heredada del benchmark (`HILO-1_benchmark_entorno.md`), que debe consultarse para no contradecir conclusiones ya tomadas allí.

### Recomendación (a firmar por JM)

- **V1: web-ifc + Fragments puro, sin servidor.** Es lo coherente con "web sin instalación + tablet" y con el cebo OSS.
- **Reevaluar Speckle en V5** (despliegue SaaS), si entonces se necesita capa de datos servidor (versionado/federación gestionada). Hasta entonces, no.
- **Pendiente:** cotejar esta recomendación con la conclusión del benchmark (`HILO-1`) antes de cerrar; el brief la declara "decisión heredada".

---

## §6.3 — Licencia OSS del cebo (verificación paquete a paquete)

### Evidencia (licencias del ecosistema That Open, consultado 2026-06-24)

| Paquete | Licencia | Estado |
|---|---|---|
| `web-ifc` (engine_web-ifc) | **MPL-2.0** | **[VERIFICADO]** — LICENSE.md y package.json del repo ThatOpen/engine_web-ifc |
| `@thatopen/components` | **MIT** (v3.3.x) | **[VERIFICADO]** — npm |
| `@thatopen/fragments` | **MIT** (v3.4.x) | **[VERIFICADO]** — npm |
| `@thatopen/ui` | **MIT** | **[VERIFICADO]** — npm |
| `three.js` | **MIT** | **[INFERIDO]** — licencia histórica de three.js (confirmar en `package.json` al fijar versión) |

### Lectura (qué significa la mezcla MPL-2.0 + MIT)

- **MPL-2.0 es copyleft "por fichero" (weak copyleft).** Obliga a publicar las modificaciones **de los ficheros MPL**, pero permite combinarlos en una obra mayor con otra licencia. Como el Entorno **consume web-ifc como dependencia** (WASM/paquete) y **no modifica sus ficheros**, MPL-2.0 **no contagia** el resto del visor. Si en algún momento se *parchea* web-ifc, ese parche debe permanecer MPL-2.0 y publicarse. **[INFERIDO]** de los términos MPL-2.0; conviene validación legal antes de publicar.
- MIT (components/fragments/ui/three) no impone obligaciones más allá de conservar el aviso de copyright.

### Recomendación (a firmar por JM)

- **Licenciar `publico/` bajo MIT o Apache-2.0** (Apache-2.0 añade cláusula de patentes, suele preferirse para producto con vocación comercial/spin-off). Ambas conviven sin problema con dependencias MPL-2.0 y MIT.
- **Regla operativa:** no modificar ficheros de web-ifc dentro del repo; consumirlo como dependencia anclada. Si hubiera que parchearlo, hacerlo en un fork MPL-2.0 separado y publicarlo.
- **Antes de la primera publicación:** revisión legal del *NOTICE*/atribuciones y un `LICENSES.md` que liste paquete→licencia (este cuadro es el punto de partida). **No publicar `publico/` hasta ese check.**

---

## §6.4 — Marca del producto (placeholder "Entorno")

**Esto es una decisión de negocio: la firma JM. La IA no concluye.** Aporto solo criterios y materia prima:

- **Criterios sugeridos:** (a) dominio `.com`/`.io` y npm scope libres; (b) sin colisión con marcas BIM existentes (That Open, Speckle, Solibri, Catenda, BIMcollab, usBIM); (c) pronunciable en ES y EN (vocación spin-off/externa); (d) no describe de más (deja sitio a pre/post/copiloto, no solo "visor").
- **Observación:** "Entorno" como nombre común español es difícil de proteger como marca y de posicionar en buscadores. Es buen *placeholder*, dudoso como marca final.
- **Siguiente paso si JM quiere:** la IA puede generar una lista de candidatas + comprobación de dominios/npm/EUIPO, como tarea aparte. No lo hago aquí para no concluir negocio.

---

## §7 — Frontera: qué viaja con el Entorno y qué se ancla

Resuelvo el "primer paso del hilo" del brief. Base: README del repo, `INSTRUCCIONES_PROYECTO.md`, `integracion/versions.lock`, `estado-inicial_narracion-IFC.md`.

### Viaja **con** el Entorno (vive en este repo)

- **El benchmark** (`HILO-1_benchmark_entorno.md`) — sustenta §6.2; debe acompañar al producto. *(Nota: el fichero se referencia en los README pero no está aún en el árbol; conviene traer la copia.)* **[INFERIDO]**
- **Una instantánea/copia del gobierno** (reglas de dos llaves, SemVer, frontera cebo/anzuelo) — el Entorno necesita el gobierno a mano sin depender de la rama viva de 2.0. **[VERIFICADO]** contra README ("una copia/instantánea del gobierno viaja").
- **El baseline narración→IFC** (`estado-inicial_narracion-IFC.md` + skill `iso19650-openbim v0.8.2`) — punto de partida real de V0/V1. **[VERIFICADO]**.
- Todo lo de `publico/` (visor, adaptadores OpenBIM, superficie NL) y la cáscara de `privado/`.

### Se **queda** en la zona protegida de 2.0 y solo se **consume anclado**

- **Contrato C8 (CDE):** no viaja; el Entorno lo referencia. *(Matiz a confirmar: en `versions.lock` los contratos listados llegan hasta C7; **C8 no aparece todavía** en el lock. Hay que reconciliar la numeración: o C8 existe en 2.0 y falta anclarlo, o el brief usa "C8" de forma prospectiva.)* **[INFERIDO — requiere confirmación de JM]**.
- **Corpus golden** y su recuperación por OIR (capa 7) — propiedad de QA/JM; en `privado/` solo vive el **puente** de lectura, anclado. **[VERIFICADO]** contra `privado/README.md`.
- **Motores de cálculo** (motor-fem, motor-calculo) — se consumen anclados vía `integracion/versions.lock`, no se publican. **[VERIFICADO]**.

### Acción previa a escribir código (cierre de §7)

1. **Traer la copia del benchmark** `HILO-1` al repo (hoy solo está referenciado).
2. **Reconciliar la numeración de contratos** C7↔C8 entre el brief y `versions.lock` (decisión de JM).
3. **Rellenar `versions.lock`** con los tags reales que publique el productor (hoy todo `0.0.0`, plantilla).

---

## Decisiones que requieren firma de JM

1. **§6.1** — ¿Acepta BCF completo + IDS (validación-lectura) en V1, autoría IDS a V2?
2. **§6.2** — ¿Acepta web-ifc puro en V1 y reevaluar Speckle en V5? *(antes, cotejar con `HILO-1`)*
3. **§6.3** — ¿Licencia de `publico/`: MIT o Apache-2.0? ¿Autoriza el check legal de atribuciones antes de publicar?
4. **§6.4** — Marca: ¿encarga a la IA una lista de candidatas + verificación de dominios/marcas, o lo lleva JM?
5. **§7** — ¿Confirma la frontera y la reconciliación C7/C8? ¿Autoriza traer el benchmark y rellenar `versions.lock`?

---

## Fuentes

- [engine_web-ifc — package.json (license: MPL-2.0)](https://github.com/ThatOpen/engine_web-ifc/blob/main/package.json) · consultado 2026-06-24
- [@thatopen/components — npm (MIT)](https://www.npmjs.com/package/@thatopen/components) · consultado 2026-06-24
- [@thatopen/fragments — npm (MIT)](https://www.npmjs.com/package/@thatopen/fragments) · consultado 2026-06-24
- [@thatopen/ui — npm (MIT)](https://www.npmjs.com/package/@thatopen/ui) · consultado 2026-06-24
- [That Open docs — BCFTopics](https://docs.thatopen.com/api/@thatopen/components/classes/BCFTopics) · consultado 2026-06-24
- [That Open docs — IDSSpecifications](https://docs.thatopen.com/Tutorials/Components/Core/IDSSpecifications) · consultado 2026-06-24
- [buildingSMART — Information Delivery Specification (IDS)](https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/) · consultado 2026-06-24
- [BibLus — IDS 1.0 como estándar definitivo (jun 2024)](https://biblus.accasoftware.com/en/what-is-ids-information-delivery-specification-and-what-is-it-used-for/) · consultado 2026-06-24
- [buildingSMART — BIM Collaboration Format (BCF) 3.0](https://www.buildingsmart.org/bim-collaboration-format-bcf-3-0/) · consultado 2026-06-24
- [buildingSMART/BCF-API (REST 3.0)](https://github.com/buildingSMART/BCF-API) · consultado 2026-06-24
- [specklesystems/speckle-server — LICENSE (Apache-2.0 + EE gatekeeper)](https://github.com/specklesystems/speckle-server/blob/main/LICENSE) · consultado 2026-06-24
- [Speckle Docs — Hosting Your Own Speckle Server](https://docs.speckle.systems/developers/server/introduction) · consultado 2026-06-24

---

*Procedencia: dossier de decisiones §6+§7 · proyecto Entorno · IA (PM) · 2026-06-24 · evidencia para decisión y firma de JM. La IA opera; JM firma.*

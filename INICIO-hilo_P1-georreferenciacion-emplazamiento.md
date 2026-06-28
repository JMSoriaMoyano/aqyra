# INICIO de hilo — P1·A: Georreferenciación, emplazamiento real e IfcFacility

> Pega este texto al abrir el hilo. Es autocontenido. Trabaja sobre `Documents\Claude\Projects` (ecosistema Aqyra). Sub-dirección del proyecto P1 (Visor/Editor IFC); gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md`.

## Texto de arranque (copiar al abrir el hilo)

> "Actúa como ingeniero de software del **Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo supervisión de JM. Esta línea de trabajo aborda la **ubicación del activo en un emplazamiento real**: georreferenciar el `IfcSite`/`IfcBuilding` y, para infraestructura, el `IfcFacility` (puente, carretera…), y crear **herramientas que ayuden a diseñar ese activo sobre su emplazamiento real**. Parte de lo ya construido en el skin Diseño (copiloto conversacional que crea la estructura espacial). La IA prepara y propone; **JM firma** (dos llaves: golden verde + firma)."

## De dónde partimos (ya hecho en P1)

- **Skin Diseño conversacional** en `Entorno/publico/demo/diseno.html` + `src/diseno.ts`: el copiloto guía la creación del edificio desde cero (emplazamiento → volumetría → plantas → habitaciones → ejes) y rellena el resumen de estructura espacial + una maqueta volumétrica (SVG isométrico con girar/trasladar/zoom, ejes X/Y/Z y cardinales N-S-E-O).
- **Operador IA real** (Claude API) en `Entorno/publico/demo/vite.config.ts` (endpoint `/__aqyra/llm`, tool-calling → `{reply, actions}`, clave en `.env` server-side). Doc: `Entorno/publico/demo/LLM.md`.
- **Autoría IFC base**: `Entorno/publico/visor/src/author.ts` (`IfcAuthor`: crea Project/Site/Building/Storey + IfcSpace con web-ifc) + golden `test/author.test.ts`.
- **Decisiones de JM:** al IFC solo va el edificio (estructura espacial + IfcGrid + IfcElements); la caja de volumen es ayuda visual. Esquema IFC4 / IFC4.3.

## Objetivo de ESTE hilo

Llevar el activo del "flota en el origen (0,0,0)" a estar **situado y orientado en el mundo real**, y dar herramientas de diseño que lo aprovechen:

1. **Georreferenciar el emplazamiento.** `IfcSite` con `IfcProjectedCRS` (EPSG del sistema, p. ej. ETRS89 / UTM 31N para Sant Cugat) + `IfcMapConversion` (Eastings/Northings/OrthogonalHeight, rotación a Norte real, escala). Norte de proyecto vs norte geográfico.
2. **Partir de un dato real.** A partir de la **referencia catastral** (0419901DF2901H0001WW) y/o coordenadas: obtener parcela, posición y orientación. Definir de dónde se toma (catastro, mapa base, topografía) y cómo entra (formato abierto).
3. **IfcFacility para infraestructura (IFC4.3).** Cuando el activo no es un edificio: `IfcAlignment` (eje), `IfcRoad`, `IfcBridge`, `IfcRailway`… georreferenciados. El copiloto debe distinguir "edificio" de "obra lineal" y enrutar.
4. **Herramientas de ayuda al diseño sobre el emplazamiento.** Catálogo a cerrar con JM: situar/ver en mapa, **norte real y soleamiento** (orientación de fachadas, sombras), **rasante/topografía** y cota, límites de parcela y retranqueos, contexto (edificios vecinos del conjunto Can Cabassa).

## Decisiones que solo cierra JM

- Sistema de coordenadas de referencia (CRS/EPSG) por defecto del despacho.
- Fuente del emplazamiento real (catastro INSPIRE/WFS, mapa base, topografía aportada) y su frontera de datos (abierta, diff-able).
- Alcance v0 de las herramientas (¿empezamos por georreferenciar + norte/soleamiento, o por el mapa de parcela?).
- Qué `IfcFacility` entran primero (edificación vs obra lineal).

## Reglas (no romper)

- Formato abierto en toda frontera; el resultado va al IFC (georreferencia = entidad IFC real, no ayuda visual).
- El visor es cebo: sin medidor visible, sin export firmable. La IA propone; JM firma.
- Cambio en la frontera de C1 = bump → golden → adoptar si verde; anclar en `versions.lock`.

## Primer paso propuesto

1. Georreferenciar el `IfcSite` de Can Cabassa (CRS + MapConversion) a partir de la ref. catastral/coordenadas, y orientar el **Norte real** en la maqueta (alinear los cardinales N-S-E-O ya dibujados con la orientación de la parcela).
2. Prototipar **una** herramienta de ayuda (propuesta: orientación/soleamiento básico) sobre el modelo situado.
3. Cerrar con JM el CRS por defecto, la fuente de emplazamiento y el alcance v0.

*Procedencia: sub-dirección de P1 (Visor/Editor IFC) · Aqyra · IA · para revisión y firma de JM.*

# INICIO de hilo — P1·B: Procesado de la instrucción por el LLM (gráfico + esquema IFC)

> Pega este texto al abrir el hilo. Es autocontenido. Trabaja sobre `Documents\Claude\Projects` (ecosistema Aqyra). Sub-dirección del proyecto P1 (Visor/Editor IFC); gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md`.

## Texto de arranque (copiar al abrir el hilo)

> "Actúa como ingeniero de software del **Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo supervisión de JM. Esta línea trabaja **cómo el operador IA (LLM) procesa una indicación rica del usuario**, traduciéndola a la vez en (a) **representación gráfica** en la maqueta y (b) **estructuración del esquema IFC** (espacios, núcleos, relaciones), y preparando el salto a la **autoría IFC real**. Parte del skin Diseño + operador IA ya construidos. La IA propone; **JM firma**."

## El caso que dispara este hilo

El copiloto ya entiende y resume bien una instrucción compleja. Ejemplo real (captura de JM):

> "Residencia de estudiantes; en cada planta hay 20 habitaciones repartidas a lado y lado, separadas por un pasillo central de 1,5 m. También existe un núcleo de comunicaciones con dos ascensores y escaleras al S-E, y otro de escaleras al N-O."

El LLM lo llevó al resumen como: *20 habitaciones (10 a cada lado del pasillo 1,50 m) + núcleo SE (2 ascensores + escalera) + núcleo NO (escalera) = 23 espacios/planta · 115 totales*. **Buen parseo de texto**, pero falta:

1. **Representación gráfica** de esa distribución en la maqueta: las habitaciones a ambos lados, el pasillo central, y los **núcleos en su orientación** (SE / NO — ahora que ya hay cardinales N-S-E-O).
2. **Estructuración del esquema IFC**: distinguir tipos de espacio (habitación / pasillo / núcleo), su posición y conteo, y dejarlo listo para autoría real (IfcSpace, y a futuro IfcZone para "habitaciones" vs "comunes", núcleos como espacios de circulación).

## De dónde partimos (ya hecho en P1)

- **Skin Diseño** `Entorno/publico/demo/diseno.html` + `src/diseno.ts`: maqueta SVG isométrica (volumen, plantas, ejes de replanteo etiquetados, ejes X/Y/Z, cardinales N-S-E-O; girar/trasladar/zoom). Acciones que ejecuta el visor: `summary` (resumen) y `view` (volume|levels|grid|reset).
- **Operador IA real** (Claude API) en `Entorno/publico/demo/vite.config.ts` (endpoint `/__aqyra/llm`, tool-calling con la herramienta `responder` → `{reply, actions}`; system prompt del copiloto). Doc: `Entorno/publico/demo/LLM.md`.
- **Decisiones de JM:** diálogo con LLM real; al IFC solo el edificio (estructura espacial + IfcGrid + IfcElements), la caja de volumen es ayuda visual.

## Objetivo de ESTE hilo

Que una indicación del usuario se traduzca, de forma fiable, en **gráfico + esquema IFC** coherentes:

1. **Ampliar el vocabulario de acciones** del LLM más allá de `summary`/`view`: nuevas acciones gráficas de planta tipo (dibujar habitaciones a ambos lados, pasillo central, núcleos por orientación), y de esquema (declarar tipos/cuentas de IfcSpace).
2. **Mejorar el system prompt** para que el LLM ubique elementos por orientación (usar SE/NO contra los cardinales) y mantenga la coherencia de cuentas (20/planta, núcleos, totales).
3. **Render de planta tipo** en la maqueta (vista en planta o sobre el volumen) que refleje la distribución descrita.
4. **Mapeo a IFC** y puente a autoría real: cómo esos espacios se convierten en `IfcSpace` (+ futura `IfcZone` habitaciones/comunes) con `IfcAuthor` (`Entorno/publico/visor/src/author.ts`).

## Decisiones que solo cierra JM

- Hasta dónde llega la representación gráfica v0 (esquema en planta vs volumetría con subdivisiones).
- Tipología de espacios y su clasificación (habitación / pasillo / núcleo; IfcZone habitaciones vs comunes).
- Cuándo se pasa de "acciones visuales" a **escribir IFC real** desde el diálogo.

## Reglas (no romper)

- Una acción por dato; el LLM no inventa lo no dicho, pregunta. Determinismo verificable donde se pueda (golden del parseo → acciones).
- Formato abierto; al IFC solo el edificio. La IA propone; JM firma.

## Primer paso propuesto

1. Definir las **nuevas acciones** (gráficas + de esquema) y extender `runAction` en `diseno.ts` y la herramienta `responder` en `vite.config.ts`.
2. Ajustar el **system prompt** para situar núcleos por orientación y conservar cuentas.
3. Dibujar la **planta tipo** (habitaciones a ambos lados + pasillo + núcleos SE/NO) en la maqueta a partir de la instrucción del ejemplo.
4. Esbozar el **mapeo a IfcSpace** para el salto posterior a autoría real.

*Procedencia: sub-dirección de P1 (Visor/Editor IFC) · Aqyra · IA · para revisión y firma de JM.*

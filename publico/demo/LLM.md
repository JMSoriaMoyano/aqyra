# Operador IA del skin Diseño — motor LLM

El cuadro de diálogo del skin Diseño (`/diseno.html`) usa un **LLM real** como cerebro
del copiloto. Conversación en lenguaje libre, instantánea, que devuelve **respuesta +
acciones** que actualizan el visor.

## Montaje actual (elegido)

- **Motor:** Claude API (Anthropic), Messages API con **tool-calling** (herramienta
  `responder` → `{ reply, actions }`). Modelo por defecto `claude-sonnet-4-6`.
- **Dónde corre:** endpoint `POST /__aqyra/llm` en el **servidor de desarrollo**
  (plugin `aqyra-plugin` en `vite.config.ts`). La clave vive **server-side**.
- **Clave:** crea `publico/demo/.env` (gitignored) con:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  # opcional: ANTHROPIC_MODEL=claude-sonnet-4-6
  ```
  Reinicia el servidor tras crearlo (Vite lee `.env` al arrancar).
- **Flujo:** el visor manda el historial `messages` → el endpoint llama a Claude con
  el system prompt del copiloto + la herramienta → devuelve `{ reply, actions }` →
  el visor pinta la respuesta y ejecuta las acciones (resumen + maqueta).

Protocolo `{ reply, actions }` (mismo que el puente A):
- `summary` con `key` ∈ project|site|building|volume|storeys|spaces|grid + `value`
  (project/site/building alimentan el árbol; el resto es texto/ayuda visual).
- `storeys` (P1·B·2): `count` = nº de plantas, `height` = altura piso a piso (m). El visor
  genera una **IfcBuildingStorey por planta** en el árbol de instancias.
- `view` con `show` ∈ volume|levels|grid|**plan**|reset (maqueta visual; aún no IFC real).
- `space` (P1·B): declara UN grupo de espacios de la planta tipo RESIDENCIAL. El visor
  lo acumula y dibuja la **planta 2D** (esquema cenital, N arriba). Una acción por dato.
  - `kind` ∈ room|corridor|core.
  - `count` (nº por planta; room: total de habitaciones), `width` (m; pasillo),
    `layout` ∈ both-sides|single-side (room), `orientation` ∈ N|S|E|O|NE|NO|SE|SO (core),
    `detail` (texto libre, p. ej. "2 ascensores + escalera"), `zone` ∈ privado|comunes.
- `program` (Inc 2): planta tipo NO residencial vía un **generador de distribución**.
  - `generator` ∈ residence-corridor | parking-comb (registro en `demo/src/generators.ts`).
  - parking-comb: `bays` (plazas/planta), `aisle` (ancho de vial m), `orientation` (rampa).
  - El núcleo (modelo/render/árbol) es agnóstico: coloca footprints genéricos por
    objectType y agrupa en IfcZone por uso. Tipología nueva = generador nuevo, sin
    tocar el núcleo. bsDD se resuelve por clase a demanda (cualquier IfcXxx 4.3).

## Árbol de instancias IFC (P1·B·2)

Con `storeys` + las `space` de la planta tipo, el visor materializa el **árbol real**
(`demo/src/model.ts`): N IfcBuildingStorey, y por planta una IfcSpace por habitación
(`AQ-ESP-HAB-Pnn-{IZQ|DER}-mm`), pasillo (`AQ-ESP-PAS-Pnn`) y núcleo
(`AQ-ESP-NUC-Pnn-{SE|NO}`), agrupadas en IfcZone `AQ-ZON-PRI`/`AQ-ZON-COM`. Cada nodo
enlaza su clase **bsDD en vivo** (`demo/src/bsdd.ts`, IFC 4.3, por clase y cacheado) con
URI + Psets por defecto al desplegar. El mismo modelo alimenta la autoría IFC real
(`visor/src/author.ts`, `createBuildingModel`).

Ejemplo (residencia de estudiantes, 20 hab/planta a lado y lado):
```
space kind=room  count=20 layout=both-sides
space kind=corridor width=1.5
space kind=core  orientation=SE detail="2 ascensores + escalera"
space kind=core  orientation=NO detail="escalera"
view  show=plan
summary key=spaces value="20 hab (10+10) · pasillo 1,5 m · núcleo SE · núcleo NO = 23/planta"
```

**Orientación:** cardinales fijos del visor +Y=N / −Y=S / +X=E / −X=O. El núcleo "al S-E"
va con `orientation=SE` (esquina inferior-derecha en planta). No reinterpretar.

**Mapeo a IFC (esbozo, no conectado):** cada `space` → `IfcSpace` con `ObjectType`
(Habitacion/Pasillo/Nucleo); `zone` → `IfcZone` privado/comunes (`IfcRelAssignsToGroup`).
Vive en `visor/src/author.ts` (`SpaceSeed.kind`, `ZoneSeed`). El salto a escribir IFC
real desde el diálogo lo firma JM en un incremento posterior.

## Posibilidades anotadas para el futuro

1. **Multi-proveedor con selector.** Abstraer el endpoint para elegir modelo desde un
   desplegable (Claude / OpenAI / Gemini) y comparar experiencias. El protocolo
   `{ reply, actions }` no cambia → el visor no se toca.
2. **Modelo LOCAL (Ollama).** Llama 3 / Mistral / Qwen en la máquina: sin clave ni
   coste, privado y offline. Cambia solo la llamada dentro del endpoint (a
   `http://localhost:11434`). Tool-calling más flojo en modelos pequeños.
3. **Backend aparte (Node/Python).** Para producción, mover el endpoint a un servicio
   propio (el operador IA, capa 6 / C7), con el **criterio/moat en `privado/`**. El
   endpoint del dev server gradúa a ese backend sin tocar el visor.

## Coste y seguridad

- Pago por uso de la API; el diseño conversacional consume poco. Fija un **límite de
  gasto** en la Console de Anthropic.
- La clave NUNCA va al navegador ni al repo (vive en `.env`, server-side).

# publico/ — el CEBO (publicable OSS)

Todo lo que vive aquí **puede publicarse abierto** sin erosionar el foso. Es el visor commodity + estándares; el diferencial (curva cero por NL, entorno propio) no depende de ocultar este código.

## Qué va aquí

- **`visor/`** — el visor web: web-ifc/That Open + Three.js, navegación 3D, selección, Psets, árbol espacial, color por clase. Industrialización de la skill `visor-ifc` (V1 de la hoja de ruta).
- **`openbim/`** — adaptadores de estándar abierto: IFC (4/4.3), **BCF** (incidencias), **IDS** (validación), **bsDD**.
- **`ui-nl/`** — la **superficie** del copiloto en lenguaje natural: parsear la intención del usuario y traducirla a acciones del visor. *La superficie es pública; el criterio que recupera del corpus, no — eso vive en `../privado/`.*

## Qué NO va aquí

- El corpus golden ni su recuperación por OIR.
- Los motores de cálculo (se consumen anclados, no se publican).
- El criterio de ingeniero que el copiloto recupera (el moat).

## Licencia

Pendiente de decisión de JM (open-core / freemium / OSS total). **Antes de publicar:** verificar la licencia **paquete a paquete** del ecosistema That Open (web-ifc es MPL-2.0; conviven posibles MIT) — pendiente del `../../HILO-1_benchmark_entorno.md`.

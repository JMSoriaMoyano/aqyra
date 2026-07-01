# Desarrollo — `publico/` (Aqyra, cebo)

Monorepo **pnpm** (D-006). Node ≥ 22.

## Comandos

```bash
pnpm install            # instala el workspace (visor, openbim, embed, ui-nl, demo)
pnpm typecheck          # tsc sobre las fuentes (tsconfig.check.json)
pnpm build              # compila @aqyra/visor, @aqyra/openbim, @aqyra/embed
pnpm test               # vitest (jsdom)
pnpm licenses           # gate de licencias: solo permisivas + MPL-2.0; bloquea GPL/AGPL
pnpm --filter @aqyra/demo dev   # arranca la demo (Vite) y embebe <aqyra-viewer>
```

## Estructura (F0)

| Paquete | Rol | Estado F0 |
|---|---|---|
| `@aqyra/visor` | escena 3D (three.js) + carga IFC (web-ifc) | **F1:** `IfcLoader` (IFC4/4.3, federación, Psets) + render + cámara ✅ · **F2:** selección, color/visibilidad por clase, árbol espacial, aislado por elemento ✅ |
| `@aqyra/openbim` | adaptadores BCF/IDS/bsDD | superficie + stubs (BCF→F3, IDS→F4) |
| `@aqyra/embed` | Web Component `<aqyra-viewer>` + **contrato** `AqyraViewer` | **F1+F2:** `load`/`getProperties`/`select`/`on`/`setVisibility-ColorByClass` cableados ✅ + helpers `classes`/`spatialTree`/`isolateByExpressIds` |
| `@aqyra/ui-nl` | superficie NL (pública) | placeholder; se enciende en V4 |
| `@aqyra/demo` | demostración del DoD | embebe el componente |

### Avance

- **F0** ✅ andamiaje (monorepo, contrato, CI, web component embebido).
- **F1** ✅ casi completa:
  - **Datos:** carga **IFC4 / IFC4.3** vía web-ifc, **federación ≥2 modelos** (registro + índice por GlobalId), **Psets**.
  - **Geometría/render:** `getMeshes` (web-ifc `StreamAllMeshes` → arrays) + `Viewer.addIfcModel` (`BufferGeometry` + material + matriz + encuadre). El **grafo de escena three.js** se verifica headless; la **rasterización GPU** se verifica en navegador real con el harness `e2e/` (`pnpm e2e:build && pnpm e2e:test`), que corre en CI.
  - **Pendiente de F1:** **presupuesto de FPS** sobre modelo grande (Decopak HQ) y controles de órbita (táctil) → con F5/tablet.
- **F1+ (navegación):** controles de cámara (OrbitControls) — **izquierdo = girar, rueda = zoom al cursor, rueda pulsada/derecho = pan (mano)**, plano *near* ajustado para no recortar al acercar. Verificado en navegador real con los IFC de **Decopak HQ** (carga, federación de 3 modelos y render).
- **F2** ✅ **completa:** **selección por clic** con resaltado (raycasting), **Psets** del elemento, **visibilidad/color por clase IFC**, y **árbol de estructura espacial** (Proyecto › Sitio › Edificio › Planta › elementos) con **aislado por elemento** (`isolateByExpressIds`).
- **Skin Calculista** (`demo/calculista.html`): lienzo limpio sin paneles permanentes; **barra de comandos NL** (stub de reglas → contrato), **menús contextuales** al clic, **historial/deshacer**, listado **"clases"** interactivo (color/visibilidad/aislar), árbol sumonable. Dirección de producto firmada en **D-007**.
- Tests: **12/12 verdes** (`vitest`: carga, esquema, federación, Psets, teselado, grafo three.js, control por clase, árbol espacial), `tsc` typecheck OK, build de paquetes OK.
- Verificación de navegador (`e2e/`): no ejecutable en el sandbox de la IA (CDN de Chromium de Playwright fuera de su lista de red); corre en CI/local. La interacción (clic, órbita, paneles, comandos) se valida en la demo (`pnpm --filter @aqyra/demo dev`).

## Contrato

La API pública de `@aqyra/embed` (`AqyraViewer` en `embed/src/contract.ts`) es el **contrato versionado SemVer**: romperla = MAJOR. Reserva ya el estado de dato `proposal` / `verified-signed` para las **dos llaves** del gobierno (el visor nunca pinta como verificado lo no firmado).

## Notas de entorno

- Publicación en **registro privado hasta V5** (D-006). No publicar `publico/` hasta cerrar el gate legal (D-003) y la marca (D-004).
- `node_modules` no debe vivir en el montaje compartido si está lleno; instalar en disco con espacio.

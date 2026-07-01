# Cómo probar Aqyra (V1 · F0+F1)

Todo se ejecuta dentro de la carpeta `publico/`. En tu equipo:
`C:\Users\jmsor\Documents\Claude\Projects\Entorno\publico`

## 0) Requisitos (una sola vez)

- **Node 22+** — https://nodejs.org
- **pnpm** — en una terminal (PowerShell):
  ```powershell
  corepack enable
  ```
  (si no funciona: `npm install -g pnpm`)

## 1) Instalar

```powershell
cd C:\Users\jmsor\Documents\Claude\Projects\Entorno\publico
pnpm install
```

## 2) VER UN IFC (lo más visual) ✅

```powershell
pnpm --filter @aqyra/demo dev
```

Abre en el navegador la dirección que muestra (normalmente **http://localhost:5173**) y **arrastra y suelta un archivo `.ifc`** (IFC4 o IFC4.3) sobre la ventana. Verás el modelo renderizado. Suelta **dos o más** a la vez para **federarlos**.

> El WASM de web-ifc se copia solo al arrancar (`predev`). Si tienes el IFC de Decopak HQ, es el modelo ideal para probar.

## 3) Tests automáticos (sin navegador)

```powershell
pnpm typecheck     # comprobación de tipos
pnpm test          # 10 tests: carga IFC4/4.3, federación, Psets, teselado, grafo 3D
```

## 4) Verificar el render en un navegador real (opcional, e2e)

```powershell
pnpm e2e:build
pnpm exec playwright install chromium
pnpm e2e:test
```

Monta el visor, carga un IFC con geometría y comprueba que three.js dibuja sobre WebGL real. (Para verlo con ventana: añade `--headed` al final.)

## 5) Gate de licencias (cebo OSS)

```powershell
pnpm licenses      # falla si aparece GPL/AGPL en publico/
```

---

### Qué esperar en esta versión

- **F0+F1**: abre y **renderiza** IFC4/IFC4.3, federa varios modelos, lee Psets.
- Cámara con **encuadre automático**; los **controles de órbita táctiles** y el **panel de Psets/árbol** llegan en F2/F5.
- Si algo falla, copia el mensaje de la terminal o de la consola del navegador (F12) y lo revisamos.

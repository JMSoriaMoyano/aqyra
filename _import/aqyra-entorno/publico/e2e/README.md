# `e2e/` — verificación en navegador real (F1 render)

Comprueba que el render WebGL de F1 funciona de verdad en un navegador (lo que los tests headless no pueden: la rasterización GPU).

```bash
pnpm --filter @aqyra/demo exec true   # asegúrate del workspace instalado
pnpm e2e:build                        # vite build del bundle e2e
cp ../node_modules/web-ifc/web-ifc*.wasm dist/   # WASM servido en '/'
pnpm exec playwright install chromium # descarga Chromium (red del CI)
pnpm e2e:test                         # Playwright: monta el visor, carga IFC, asserta malla en WebGL
```

> **Nota:** no se ejecuta en el sandbox de desarrollo de la IA porque el CDN de navegadores de Playwright no está en su lista de red permitida; corre en CI o en local. La **extracción de geometría** (web-ifc) y la **construcción del grafo three.js** sí están verificadas headless (`visor/test/*`).

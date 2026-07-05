# Plan · Cambio de convenio del visor a Z-up (para hilo dedicado)

> Handoff desde el hilo de mockup/slice-1 · 2026-07-04 · para JM
> **Objetivo:** que el visor use **Z vertical** (convenio del ecosistema), no Y-up.
> **Estado:** PLANIFICADO — no implementado. Requiere hilo propio + re-firma de golden.

---

## 1. Por qué

El ecosistema de cálculo y el propio IFC son **Z-up**:

- `motor-fem` lo declara literal (`scripts/elementos/barra.py`, `scripts/fem1.py`, `scripts/mallador.py`):
  «Convención de ejes GLOBALES del ecosistema: **X,Y horizontales, Z vertical, gravedad −Z**».
- El IFC de decopak-hq: el eje del World Coordinate System es `IFCDIRECTION((0.,0.,1.))` → **Z arriba**.

Hoy el visor pinta **Y-up** porque web-ifc convierte la geometría IFC (Z-up) a Y-up para three.js.
Consecuencia: el visor no habla el mismo idioma de ejes que los motores.

## 2. Suposiciones Y-up en el visor (qué hay que tocar)

Todas en `apps/visor/src/`:

- **`bcf.ts` — el punto crítico.** `bcfCameraToViewer` mapea la cámara BCF (IFC Z-up) al marco Y-up
  con `m = (v) => [v[0], v[2], -v[1]]` (comentarios líneas 9, 28, 133). Si el visor pasa a Z-up
  (= IFC nativo), este mapeo se vuelve **identidad**. **PERO** el golden **C4-FED-06 (cámara D29)**
  está baselineado con el mapeo Y-up actual → cambiarlo **rompe el golden** → hay que
  **re-baselinar y re-firmar (Llave 2, GPG de JM)**. Este es el riesgo gobernado principal.
- **`viewer.ts` · `elementElevations` (≈521–534):** usa `box.min.y/max.y` como «cota IFC». Pasa a `.z`.
  (Comentario «eje Y = cota IFC».) En Z-up esto es MÁS natural: `.z` es la cota real.
- **`viewer.ts` · constructor:** `camera.up` por defecto es Y. Poner `camera.up = (0,0,1)` y ajustar
  OrbitControls para Z-up.
- **`viewer.ts` · `fitToModels` / `frameElement`:** el vector de offset de cámara y el «arriba».
- **`viewer.ts` ≈632:** comentario «MARCO DEL VISOR (Y-up)» — actualizar.
- **`spatial-metric.ts` ≈26–34:** `elevationMetric` («posición = cota (Y)») → cota = `.z`.
- **`idealize.ts`:** trabaja en coordenadas de la geometría (`[n.x,n.y,n.z]`); si se rota la
  geometría a Z-up en la ingesta, queda consistente (verificar glifos/idealizado).
- **Gizmo de ejes** (añadido en slice-1): hoy muestra Y vertical; con Z-up mostrará Z vertical solo.

## 3. Enfoque técnico recomendado

**Deshacer el swap de web-ifc en la ingesta:** rotar las mallas +90° sobre X al cargarlas
(`ifc-loader`/`addIfcModel`), de modo que la geometría quede en **Z-up nativo del IFC**. A partir
de ahí: `camera.up = Z`, cota = `.z`, y el mapeo BCF se simplifica a identidad. Ventaja: el visor,
el IFC y los motores comparten un único sistema de coordenadas.

Alternativa descartada: mantener geometría Y-up y solo re-etiquetar (incoherente).

## 4. Tests y golden afectados (a actualizar en el hilo con entorno de test)

- Golden **C4-FED-06 (D29)** → re-baseline + **firma GPG de JM** (Llave 2). *Bloqueante gobernado.*
- `test/bcf.test.ts`, `test/federado-e2e.test.ts`, `test/coste-5d-e2e.test.ts` (cámara BCF).
- `test/ux-behavior.test.ts` (cámara), `test/spatial-tree.test.ts`, `test/saneamiento.test.ts`
  (métrica de cota).
- No se pudo correr vitest en el hilo de origen (disco del sandbox lleno) → ejecutar en un entorno con test.

## 5. Secuencia sugerida para el hilo nuevo

1. Rotar geometría a Z-up en la ingesta + `camera.up=Z` + OrbitControls; ver un IFC y confirmar Z vertical.
2. Migrar cota a `.z` (`elementElevations`, `spatial-metric`) y verificar árbol/saneamiento.
3. Simplificar `bcfCameraToViewer` a identidad; **re-baselinar el golden D29** y pedir la firma de JM.
4. Pasar toda la batería de tests del visor (vitest) en verde.
5. Actualizar comentarios de convenio y el gizmo (Z vertical).

## 6. Lo ya hecho en el hilo de origen (no rehacer)

Sobre `apps/visor/src/viewer.ts` y `apps/aqyra-shell/`:
- Encuadre iso en `fitToModels`, iluminación con profundidad, aristas por malla, gizmo de ejes XYZ.
- Fix de la distorsión al desplegar el árbol (era layout CSS del shell: `.main`/`.viewer` sin acotar
  altura; resuelto con `min-height:0` + `overflow:hidden` + `grid-template-rows: minmax(0,1fr)`).
- Shell slice-1 (`apps/aqyra-shell`) que abre un IFC suelto; árbol con tipos IFC coloreados.

*Procedencia: handoff del hilo mockup/slice-1 · 2026-07-04.*

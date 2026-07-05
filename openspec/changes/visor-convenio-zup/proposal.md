# Cambio · Convenio de ejes del visor a Z-up

> Change-id: `visor-convenio-zup` · Capacidad: `visor` (`apps/visor`, `@aqyra/visor`)
> Procedencia: ADR-018-DRAFT (Aqyra-Raiz) · impacto en `apps/visor/PLAN_convenio-Zup.md`
> Estado: spec redactada (SSD) · la capa OpenSpec ya está en `main` (PR #33) · pendiente de
> ratificar Q-Zup-1 (D29) y Q-Zup-2 (slice-1) antes del código.

## Por qué

El ecosistema de cálculo y el propio IFC son **Z-up**: `motor-fem` lo declara literal
(«X,Y horizontales, Z vertical, gravedad −Z») y el World Coordinate System del IFC es
`IFCDIRECTION((0.,0.,1.))`. Hoy el visor pinta **Y-up** porque web-ifc convierte la geometría
IFC a Y-up para three.js. Consecuencia: el visor **no habla el mismo idioma de ejes** que los
motores ni que el propio modelo que carga. Alinear el visor con el Z-up nativo del IFC unifica
un único sistema de coordenadas entre modelo, motores y visor, y simplifica el mapeo de la
cámara BCF a la identidad.

## Qué cambia (superficies de `apps/visor/src/`)

- **Ingesta de geometría** (`ifc-loader`/`viewer.addIfcModel`): deshacer el swap Y-up de web-ifc
  rotando las mallas +90° sobre X al construir la escena, dejando la geometría en **Z-up nativo**.
- **Cámara** (`viewer.ts` constructor y framing): `camera.up = (0,0,1)`, OrbitControls a Z-up;
  revisar los vectores de offset de `fitToModels` y `frameElement`.
- **Cota de elemento** (`viewer.elementElevations` ≈521–534; `spatial-metric.elevationMetric`):
  la cota pasa de `box.min.y/max.y` a `box.min.z/max.z` (en Z-up, `.z` **es** la cota real).
- **Mapeo de cámara BCF** (`bcf.ts` · `bcfCameraToViewer`): la permutación `(x,y,z)→(x,z,−y)`
  se convierte en **identidad** (el visor y el BCF comparten ya el marco IFC Z-up).
- **Gizmo de ejes** y comentario «MARCO DEL VISOR (Y-up)» (`viewer.ts` ≈652): Z vertical.
- **Idealización** (`idealize.ts`): trabaja en coordenadas de la geometría; queda consistente si
  la rotación se aplica en la ingesta (verificar glifos/idealizado).

## Impacto en gobierno — HALLAZGO que corrige el brief

El ADR/PLAN señalan el re-baseline del golden **C4-FED-06 (cámara D29)** como el corazón del
hilo y un **bloqueante gobernado (Llave 2, re-firma GPG)**. La inspección del código muestra que
**ese riesgo no se materializa**:

- El golden firmado `C4-FED-06` ancla la cámara del viewpoint en **marco IFC (Z-up)**
  (`pos = pb_EST + (1,−1,1)·d`, `up = (−1,1,2)/√6`). Es el marco al que precisamente migramos.
- `test/federado-e2e.test.ts` (líneas 95–104) comprueba la cámara **tal como sale de
  `parseViewpoint`** (IFC Z-up), **sin** aplicar `bcfCameraToViewer`. No cambia.
- `test/coste-5d-e2e.test.ts` no comprueba cámara.
- El **único** consumidor de `bcfCameraToViewer` en tests es el unitario `test/bcf.test.ts`
  (líneas 78–84), interno del visor.

Por tanto, el cambio de convenio hace `bcfCameraToViewer` = identidad, pero **no toca ningún
artefacto firmado**: el golden D29 permanece byte a byte y las fixtures IFC (md5) no se editan
(la rotación es de render, no reescribe ficheros). **El cambio queda íntegramente dentro de la
Llave 1** (PR con typecheck+build+tests verdes). **No requiere Llave 2.**

> Este hallazgo reclasifica el riesgo del hilo y debe ser **ratificado por JM** (dueño del
> producto) antes de darlo por firme, por contradecir el encuadre del ADR-018-DRAFT.

## Fuera de alcance

- No se reescriben las fixtures IFC ni el golden C4-FED-06 (permanecen anclados por md5).
- No se aterriza aquí el trabajo de **slice-1** sin commitear (shell `apps/aqyra-shell`, gizmo,
  fix de layout): va en su propia PR, dependencia de este cambio (ver `tasks.md`, paso 0-bis).
- No se cambia el contrato C4 ni el service `federacion` (la cámara BCF ya es Z-up en origen).

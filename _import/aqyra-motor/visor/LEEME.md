# Visor IFC v1.0 — edición de datos e ingesta por arrastre

Visor BIM transversal (estructuras / instalaciones MEP / obras lineales) sobre el motor
**ThatOpen (fragments)**. Desde la v1.0 es una herramienta **de despacho**: abre cualquier
`.ifc` arrastrándolo, **edita sus datos** (atributos, Property Sets) y **exporta el IFC
modificado**. Frontera firme: el visor **lee, anota y edita DATOS; nunca modela geometría**.

## Abrir el visor (forma fácil — recomendada)

**La primera vez (solo una):** doble clic en **`Crear acceso directo (escritorio).bat`**.
Crea un icono **«Visor IFC»** en el Escritorio.

**A partir de ahí, el día a día:** doble clic en el icono **«Visor IFC»** del Escritorio.
Eso arranca el servidor **oculto** (sin consola) y abre el visor en una **ventana tipo app**
(sin pestañas ni barra de direcciones), todo en un clic. Sin pensar en puertos ni en `file://`.

Por debajo, el icono ejecuta `Abrir Visor IFC.vbs` → `Abrir Visor IFC.bat`, que: comprueba si
el servidor del puerto 8007 ya está activo (lo reutiliza si sí), si no lo levanta con `pythonw`
(sin ventana), y abre Chrome en modo aplicación (`--app`) apuntando a `visor-ifc-v1.0.html`.

> **Nunca abras el `.html` con doble clic (`file://`)** ni uses puertos antiguos (p. ej. 8000):
> el visor v1.0 vive en **`http://localhost:8007/visor-ifc-v1.0.html`** y el worker/PWA solo
> funcionan sobre `http`/`localhost`. El lanzador se encarga de todo esto.

**Alternativa manual:** doble clic en `servir_visor.bat` (sirve por http 8007 y abre el visor en
una pestaña normal del navegador). Útil si no usas Chrome.

La cabecera indica la versión (**`build b5`** o superior). La 1ª vez necesita internet (descarga
three / fragments / web-ifc / worker desde CDN); después, instalada como PWA, funciona offline.

## Instalar como app (offline) — PWA

Desde build b5 el visor es una **PWA**: se instala como aplicación con icono propio,
ventana sin pestañas ni barra, y **funciona sin conexión** tras la primera carga.

- **En el escritorio (Chrome/Edge):** con el visor abierto, pulsa **«⤓ Instalar app»** en la
  cabecera, o el icono de instalar (⊕) de la barra de direcciones. Queda como app con icono.
- **Offline:** un *service worker* (`sw.js`) cachea el visor, las librerías (three / fragments /
  web-ifc + WASM + worker) y los modelos en la primera carga **con internet**; después abre y
  navega sin red. Al publicar una versión nueva se sube el número de caché (`build bN`) y el SW
  la sustituye.
- **En tablet (iPad / Android) para obra:** sirve la carpeta `visor/` en la red local **por
  HTTPS** (las PWA y el worker exigen `https://` o `localhost`) y, desde el navegador de la
  tablet, «Añadir a pantalla de inicio» / «Instalar». Lleva los modelos ya convertidos
  (`.frag`+`.props.json`) para que vaya ligero; con el service worker, una vez cargado funciona
  offline en el tajo. Útil para **medición** táctil y consulta del modelo; el **replanteo** por
  coordenadas (leer la coordenada real de un punto) es la siguiente función orientada a obra.

> Nota: servir por HTTPS en red local (para tablet) requiere un certificado; en el equipo de
> despacho basta `localhost` (el `.bat`). El empaquetado offline pleno embebido queda para v1.0.x.

## Novedades de la v1.0

### Abrir un IFC por arrastre (sin conversión externa)
- **Arrastra un `.ifc`** a cualquier parte de la ventana, o pulsa **«Abrir IFC…»**.
- El visor lo convierte **en el navegador** (web-ifc WASM) a geometría ligera + índice de
  datos (atributos, Psets, cantidades `Qto_*`, clasificación Uniclass/GuBIMClass, cotas de
  planta) y lo añade a la federación viva, con toda la navegación operativa.
- Botón **«⬇ caché»** en la tarjeta del modelo: guarda `modelo.frag` + `modelo.props.json`
  (en una carpeta que elijas, si el navegador soporta *File System Access*, o por descarga)
  para reaperturas instantáneas sin reconvertir.

### Editar datos y exportar el IFC
1. Selecciona un elemento (clic en 3D, en el **Árbol** o en **Buscar**).
2. En el panel derecho pulsa **«✎ Editar datos»** (aparece solo en modelos abiertos por
   arrastre, que conservan su IFC fuente).
3. Edita el **Name** y los **valores de los Property Sets**; **«＋ propiedad»** añade una
   propiedad nueva a un Pset.
4. **«Validar (QA)»** ejecuta comprobaciones ligeras (Psets de proyecto, Name, clasificación,
   valores vacíos).
5. **«Aplicar cambios»** los escribe en el modelo; **«Exportar IFC…»** descarga
   `modelo-editado.ifc`, reabrible en otra herramienta (BIMvision / Revit / usBIM) o
   arrastrándolo de vuelta al propio visor.

> **QA completa:** las comprobaciones del visor son una puerta de aviso, no sustituyen la
> validación normativa. Para el control completo, pasa la skill **`ifc-validate`**
> (IfcOpenShell) sobre el IFC exportado.

## Capacidades heredadas (v0.5–v0.9.1)

- **Federación** multi-disciplina: varios modelos a la vez; panel de **Modelos** con
  visibilidad, aislar y color por modelo / disciplina / clasificación.
- **Navegación y filtrado**: buscar/filtrar por texto, clase, atributo o `Pset ▸ Propiedad`;
  aislar/ocultar por elemento, nodo o clase; **vista por plantas** (por cota o por planta).
- **Medición y secciones**: corte X/Y/Z sobre toda la federación; medir **distancia** y
  **área**; lectura de cantidades `Qto_*`.
- **Clasificación y BCF**: color/leyenda por Uniclass/GuBIMClass; incidencias **BCF 2.1**
  (crear con punto de vista, comentar, exportar/importar `.bcfzip`).

## Convertir IFC desde Node (opcional)

La ingesta por arrastre ya no necesita conversión externa. Si aun así quieres pre-generar
los `.frag`/`.props.json` (p. ej. para el `manifest.json` inicial):

1. Node.js instalado → una vez: **`instalar_dependencias.bat`**.
2. Por cada IFC: **`convertir_ifc.bat  C:\ruta\modelo.ifc`** → crea `models\modelo.frag` y
   `models\modelo.props.json`; añade su línea al `models\manifest.json`.

## Estructura de la carpeta

```
visor/
  visor-ifc-v1.0.html      Visor actual (de despacho · PWA)
  visor-ifc-v0.9.html … v0.5   versiones previas conservadas
  Crear acceso directo (escritorio).bat   Crea el icono «Visor IFC» en el Escritorio (una vez)
  Abrir Visor IFC.bat      Lanzador de un clic: server oculto + ventana app (Chrome --app)
  Abrir Visor IFC.vbs      Ejecuta el lanzador sin ventana de consola
  servir_visor.bat         Lanzador http (8007) clásico → abre v1.0 en pestaña normal
  visor.webmanifest        Manifiesto PWA (nombre, iconos, ventana standalone)
  sw.js                    Service worker (caché offline; subir CACHE al cambiar de build)
  icons/                   Iconos de la app (192/512/maskable/apple-touch)
  pipeline.mjs             Conversor IFC -> fragments + índice (Node; misma lógica portada al navegador)
  models/                  Modelos del manifest + demos (qto-demo, clasif-demo)
```

## Versiones fijadas (compatibles — no cambiar de forma aislada)

`@thatopen/fragments@3.4.5` · `web-ifc@0.0.77` · `three@0.184.0`.

- Worker de fragments: `cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.5/dist/Worker/worker.mjs`.
- **web-ifc** (ingesta + edición): glue de navegador `cdn.jsdelivr.net/npm/web-ifc@0.0.77/web-ifc-api.js`,
  externalizado del bundle de fragments en el importmap (clave para que el `IfcImporter`
  funcione en navegador).
```

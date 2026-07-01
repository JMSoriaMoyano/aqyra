# Visor IFC — App de escritorio (Electron)

App de escritorio **sin servidor externo**: un único ejecutable que lleva el visor dentro y
levanta su mini-servidor **dentro del propio proceso** de la app. No hay un Python ni un proceso
aparte que un antivirus pueda cerrar — si la app está abierta, su servidor está dentro de ella.
Esto resuelve de raíz las caídas del servidor local.

## Uso en ESTE equipo (sin construir nada) — recomendado

Como Electron ya se instala con `npm install`, no necesitas generar ningún `.exe`:

1. Doble clic en **`Probar sin construir.bat`** (instala Electron si falta y abre la app).
2. Para el día a día: doble clic en **`Crear icono escritorio (app).bat`** una vez → te deja el
   icono **«Visor IFC»** en el Escritorio. A partir de ahí, doble clic en ese icono abre la app
   directamente (sin consola, sin servidor, sin puertos).

> El icono lanza `Abrir Visor IFC (app).vbs`, que ejecuta el Electron ya instalado
> (`node_modules\electron\dist\electron.exe`) cargando `main.js`. Nada que un antivirus mate.

## Crear el INSTALADOR para ti y tus compañeros (Setup.exe)

Requisitos: **Node.js** instalado. Internet para la 1ª compilación. Permisos de administrador
(el `.bat` los pide solo con un UAC).

1. Doble clic en **`Construir instalador (1 vez).bat`** y acepta el aviso de administrador (UAC).
   - Copia el visor a `app\`, instala dependencias y construye con `electron-builder`.
   - (El UAC hace falta porque electron-builder crea enlaces simbólicos al preparar sus
     herramientas, y Windows lo exige. Alternativa sin admin: activar **Modo de desarrollador**
     en Configuración → Privacidad y seguridad → Para programadores, y volver a ejecutar.)
2. Al terminar, en `dist\` tienes:
   - **`Visor IFC Setup 1.0.0.exe`** → el **instalador**. Tú y tus compañeros lo ejecutáis, elige
     carpeta, y crea el acceso directo «Visor IFC» en el Escritorio y el menú Inicio.
   - **`Visor IFC portable.exe`** → versión que se ejecuta sin instalar (un solo archivo).
3. Reparte el `Setup.exe` (o el portable) a tus compañeros por carpeta compartida, USB o email.

> **Aviso de SmartScreen la 1ª vez:** al no estar firmado con un certificado de empresa, Windows
> puede mostrar «Windows protegió tu PC». Pulsa **«Más información» → «Ejecutar de todos modos»**.
> Para quitar ese aviso del todo hace falta un **certificado de firma de código** (de pago); es
> un paso aparte que puedo dejar preparado cuando lo tengáis.

## Probar sin construir (modo desarrollo)

Doble clic en **`Probar sin construir.bat`**: instala Electron (si falta) y abre la app cargando
el visor de la carpeta `..\` directamente (sin generar el `.exe`). Útil para iterar rápido.

## Qué incluye / qué no

- **Incluye** (offline): el visor, los modelos de `models\`, iconos. El mini-servidor interno los
  sirve por `http://127.0.0.1` (contexto seguro; el worker de fragments y web-ifc funcionan).
- **Aún por CDN la 1ª vez** (necesita internet): las librerías `three` / `@thatopen/fragments` /
  `web-ifc` (+ WASM y worker) se descargan de jsDelivr/esm.sh. Para **offline pleno en obra** hay
  que empaquetarlas dentro de la app (paso v1.0.x): descargarlas a `app\vendor\` y reescribir el
  importmap a rutas locales. Cuando quieras, lo preparo.

## Estructura

```
desktop/
  main.js                     Proceso principal: servidor http interno + ventana
  package.json                Config de Electron + electron-builder (target portable)
  assets/icon.ico             Icono de la app
  Construir app (1 vez).bat   Copia assets + npm install + npm run dist  -> dist\Visor IFC.exe
  Probar sin construir.bat    npm start (Electron en modo desarrollo)
  app/                        (se genera al construir) copia de los archivos web del visor
  dist/                       (se genera al construir) el ejecutable Visor IFC.exe
```

## Versiones

`electron ^31` · `electron-builder ^24`. El visor interno sigue fijado a
`@thatopen/fragments@3.4.5` · `web-ifc@0.0.77` · `three@0.184.0`.

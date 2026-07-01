# THIRD-PARTY-NOTICES — plantilla

> Fichero de atribuciones que **se distribuye con `publico/`**. Esta es la **plantilla**: rellenar las versiones, los titulares de copyright y enlazar el texto de licencia de cada paquete cuando V1 fije su árbol de dependencias. Generar la lista definitiva con `license-checker` (npm) sobre el árbol real y revisar transitivas. Renombrar a `THIRD-PARTY-NOTICES.md` (o `.txt`) al publicar.

Este producto incluye software de terceros bajo las licencias que se indican. Se conservan sus avisos de copyright y licencia.

---

## web-ifc — MPL-2.0

- **Proyecto:** That Open Engine · web-ifc
- **Versión:** `<rellenar>`
- **Copyright:** © That Open Company y colaboradores
- **Licencia:** Mozilla Public License 2.0 — https://www.mozilla.org/MPL/2.0/
- **Fuente:** https://github.com/ThatOpen/engine_web-ifc
- **Nota MPL:** los ficheros cubiertos por MPL conservan su licencia; si se han modificado, su fuente modificada está disponible en `<enlace al fork/fuente>`.

## @thatopen/components — MIT

- **Proyecto:** That Open Engine · components
- **Versión:** `<rellenar>`
- **Copyright:** © That Open Company y colaboradores
- **Licencia:** MIT — https://github.com/ThatOpen/engine_components/blob/main/LICENSE.md
- **Fuente:** https://github.com/ThatOpen/engine_components

## three.js — MIT

- **Proyecto:** three.js
- **Versión:** `<rellenar>`
- **Copyright:** © 2010–present three.js authors
- **Licencia:** MIT — https://github.com/mrdoob/three.js/blob/dev/LICENSE
- **Fuente:** https://github.com/mrdoob/three.js

<!-- Añadir aquí el resto de dependencias DIRECTAS y TRANSITIVAS que el escáner detecte en publico/.
Plantilla por paquete:

## <paquete> — <licencia SPDX>
- **Versión:** <x.y.z>
- **Copyright:** © <titular>
- **Licencia:** <nombre> — <url del texto de licencia>
- **Fuente:** <url del repo>
-->

---

### Condicional (solo si se adopta Speckle)

> Si finalmente se usa Speckle en `publico/`, añadir aquí su entrada **Apache-2.0** y su fichero `NOTICE`, y **verificar que NO se incluyen los módulos EE** (`workspaces/`, `gatekeeper/`), que son propietarios. *(Estado actual: NO se adopta Speckle — web-ifc puro, D-002.)*

### Excluido de `publico/` (no se distribuye aquí)

- **IfcOpenShell (LGPL-3.0-or-later)** — vive en `privado/` y se ejecuta server-side; no se incrusta en el cebo. No requiere atribución en este fichero salvo que se distribuya.

---

*Plantilla preparada por la IA · 2026-06-23 · rellenar y validar antes de publicar. Ver análisis en `../CHECK_LICENCIAS_publico.md`.*

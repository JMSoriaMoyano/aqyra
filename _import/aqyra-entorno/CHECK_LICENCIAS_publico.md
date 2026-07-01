# Check de licencias — `publico/` (cebo OSS)

**Proyecto Entorno · pendiente 4 (check legal antes de publicar `publico/`)**
**Estado:** PROPUESTA / evidencia preliminar — preparada por la IA · **Fecha** 2026-06-23
**Base:** licencias verificadas en `HILO-1_benchmark_entorno.md` (leídas del `LICENSE` de cada repo).

> ⚠️ **Aviso:** esto **no es asesoramiento jurídico**. Es la preparación de la evidencia. Antes de publicar, lo valida un jurista o JM. Y este mapa es **preliminar** (dependencias directas conocidas): la auditoría definitiva se cierra con el **árbol real de dependencias de V1**, incluidas las transitivas (ver §6).

---

## 1. Alcance

Solo cubre lo que se **publica/distribuye**: `publico/` (el cebo — visor + adaptadores OpenBIM + superficie NL). `privado/` **no se publica**, así que sus dependencias (p. ej. IfcOpenShell server-side en `puente-calculo`) **no entran en este check de publicación** mientras se queden en el servidor y no se distribuyan binarios.

## 2. Mapa de licencias del stack conocido

| Paquete | Rol en el producto | Dónde corre | Licencia | Tipo | ¿Se distribuye? |
|---|---|---|---|---|---|
| **web-ifc** (That Open) | lectura/escritura IFC en navegador | cliente (WASM/JS) | **MPL-2.0** | copyleft débil (por **fichero**) | **Sí** (ship al navegador) |
| **@thatopen/components** | componentes del visor (BCF, IDS, UI) | cliente | **MIT** | permisiva | Sí |
| **three.js** | render 3D | cliente | **MIT** | permisiva | Sí |
| **IfcOpenShell** | IFC/IDS server-side (en `privado/puente-calculo`) | servidor | **LGPL-3.0-or-later** | copyleft débil (por **librería**) | No (server-side, no se *conveys*) |
| **Speckle (server)** *(si se adopta)* | plataforma de datos | servidor | **Apache-2.0** + **módulos EE propietarios** | permisiva + open-core | Condicional |
| **specklepy** *(si se adopta)* | SDK Python | servidor | Apache-2.0 *(confirmar)* | permisiva | No |

> El benchmark inclinó hacia **web-ifc/That Open** sobre Speckle para el visor; Speckle queda como opción condicional. Si se adopta, **no usar ni redistribuir los módulos EE** (`workspaces/`, `gatekeeper/`): son propietarios, no Apache.

## 3. Qué obliga cada licencia (resumen práctico)

- **MIT** (three.js, components): permisiva. **Obligación:** conservar el aviso de copyright y el texto de licencia en la distribución. Sin fricción.
- **MPL-2.0** (web-ifc): copyleft **débil por fichero**. **Obligaciones:** (a) si **modificas ficheros de web-ifc**, esos ficheros modificados siguen bajo MPL y su fuente debe estar disponible; (b) puedes **combinar** web-ifc con tu código bajo otra licencia en una obra mayor (la frontera es el fichero, no el binario); (c) conservar sus avisos y poner a disposición la fuente de los ficheros MPL. Incluye concesión de patentes. → **Si solo lo consumes sin tocar sus ficheros, tu código sigue siendo tuyo; basta con notice + fuente de web-ifc.**
- **LGPL-3.0** (IfcOpenShell): copyleft **débil por librería**. **Obligaciones (al distribuir):** permitir al usuario **sustituir/recompilar** la librería y proveer su fuente + avisos. **En SaaS server-side sin distribuir binarios, las obligaciones son menores** (no hay *conveying*). → **Mantenerlo en `privado/` y server-side** es lo limpio; no incrustarlo en `publico/`.
- **Apache-2.0** (Speckle/specklepy): permisiva con **concesión de patentes** y propagación del **NOTICE**. **Obligaciones:** incluir licencia y `NOTICE`, declarar cambios. Compatible.

## 4. Análisis de compatibilidad con la licencia del cebo

**Recomendación de licencia para `publico/`: MIT o Apache-2.0** (Apache añade concesión de patentes explícita). Ambas son compatibles con publicar el cebo, **siempre que**:

1. **web-ifc (MPL-2.0):** se redistribuye con su aviso y su fuente disponible; si se modifican sus ficheros, esos quedan MPL. Tu código propio del visor puede ir bajo MIT/Apache.
2. **Three.js y components (MIT):** incluir avisos. Sin problema.
3. **IfcOpenShell (LGPL-3.0):** **no entra en `publico/`.** Vive en `privado/` y se ejecuta server-side. Línea roja.
4. **Speckle EE:** si se adopta Speckle, **excluir los módulos propietarios** del repo público.

> **Conclusión preliminar:** publicar `publico/` bajo **MIT/Apache-2.0 es viable** sin erosionar el moat, respetando las cuatro condiciones. El límite cebo/anzuelo del proyecto (público vs privado) **coincide** con la frontera de licencias: lo copyleft-de-librería y lo propietario-EE se quedan en `privado/`/servidor.

> **Decisión tomada (D-003, 2026-06-24):** la licencia del cebo es **Apache-2.0**. Ver `DECISIONES.md`.

## 5. Líneas rojas

- IfcOpenShell (LGPL) y cualquier módulo EE de Speckle **nunca** en `publico/`.
- No modificar ficheros de web-ifc sin publicar esas modificaciones (MPL).
- Conservar **todos** los avisos de copyright y licencia → fichero de atribuciones (`publico/THIRD-PARTY-NOTICES`, plantilla adjunta).

## 6. Paso operativo para cerrar la auditoría (cuando exista V1)

- Correr un escáner de licencias sobre el **árbol real de dependencias**:
  - npm: `license-checker --production --summary` (y revisar transitivas).
  - Python (si aplica server-side): `pip-licenses`.
- Volcar el resultado a `publico/THIRD-PARTY-NOTICES` (rellenar la plantilla).
- Revisar transitivas con copyleft fuerte (GPL/AGPL) → **bloqueantes** si aparecen en `publico/`.

## 7. Pendiente de JM / jurista

1. ~~**Elegir la licencia del cebo**~~ ✅ **Apache-2.0** (D-003).
2. **Validación jurídica** antes de publicar.
3. Confirmar si se **modificarán ficheros de web-ifc** (cambia la obligación MPL).
4. Confirmar adopción o no de **Speckle** (y exclusión de sus módulos EE) — *de momento NO, web-ifc puro (D-002).*

---

*Evidencia preparada por la IA · 2026-06-23 · para decisión y validación jurídica de JM. No es asesoramiento legal.*

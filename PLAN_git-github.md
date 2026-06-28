# Plan mínimo y seguro — git + GitHub para Aqyra

**Preparado por:** hilo de coordinación (Aqyra-Raiz) · 2026-06-28 · La IA prepara/propone; **decide y autoriza JM.**
**Principio rector:** primero **respaldo + gobierno en privado** (cero riesgo de fuga); publicar el cebo es un paso **posterior y deliberado**.

---

## 1. Idea en una frase

Poner cada carpeta del ecosistema bajo git y subir una copia **privada** a GitHub (caja fuerte en la nube), de modo que tengas **respaldo, historial, deshacer y el gate de aprobación (PR) = tu segunda llave**. El **foso nunca sale**; el cebo se publica solo cuando tú lo decidas (fase 2).

## 2. Qué repos, y público/privado

**Fase 1 — TODO PRIVADO** (respaldo y gobierno; nada visible fuera):

| Repo (sugerido) | Carpeta | Visibilidad | Por qué |
|---|---|---|---|
| `aqyra-motor` | `Estructurando` | **Privado** | El foso (motor-fem, motor-calculo, plugins). Ya tiene git. |
| `aqyra-contratos-golden` | `Estructurando 2.0` | **Privado** | Zona protegida (contratos + golden). **Aquí el PR es lo más valioso.** |
| `aqyra-entorno` | `Entorno` | **Privado** | El visor (cebo `publico/` + `privado/` juntos, de momento). |
| `aqyra-raiz` | `Aqyra-Raiz` | **Privado** | Sala de control + estrategia (cebo/anzuelo, precios). |

**Fase 2 — más adelante, deliberada:** cuando el cebo esté listo para ser abierto (es el hito "cebo desplegable" del roadmap), **extraer `Entorno/publico/visor` a un repo PÚBLICO** `aqyra-visor` con licencia **Apache-2.0**. Hasta entonces, nada público → cero riesgo.

*(Alternativa más simple: un único repo privado para todo. Más fácil de llevar, pero mezcla cebo y foso; por eso recomiendo separarlos desde el principio, para poder abrir solo el visor en la fase 2.)*

## 3. Qué se EXCLUYE (no sube nunca) — `.gitignore`

Detectado en disco y motivo:

- **`node_modules/`** — pesa cientos de MB y se regenera solo. (Estructurando ~570 MB, Entorno ~150 MB casi todo esto.) **Excluir siempre.**
- **`Entorno/publico/demo/.env`** — ⚠️ **secreto** (config/clave del proxy LLM). **Nunca subir.**
- **`__pycache__/`, `.venv/`, `venv/`** — temporales de Python.
- **`*.plugin`** (paquetes de release, varios y pesados) — son artefactos; se publican como "Releases", no en el historial. **El `release.manifest.json` y su `.asc` SÍ se versionan** (son la prueba de la 2ª llave).
- **Salidas/temporales** (`_resultados/`, `*_resultado.txt`, logs).
- **Datos crudos de cliente** (contrato C2): cualquier proyecto real de cliente queda fuera. Los **IFC de casos de prueba** (Decopak, casos 01–15) **sí se quedan** porque son *fixtures* del golden — salvo que alguno tenga datos confidenciales; eso lo confirmas tú.

## 4. Cómo se trabajaría (flujo)

- **Día a día:** cambio → `commit` (queda en el historial con fecha y motivo) → `push` (sube a la nube).
- **Zona protegida y releases (`aqyra-contratos-golden`, y firmas):** el cambio entra por **PR** → **tú lo apruebas** → se fusiona. Es tu **2ª llave, con botón y traza**.
- **Opcional (recomendado a futuro): CI.** GitHub corre la **golden automáticamente** en cada PR (lo que hoy haces con `VERIFICAR_V3.bat`). La 1ª llave se vuelve automática y visible (verde/rojo) antes de que firmes.

## 5. Quién hace qué (límites claros)

- **Yo puedo (local, sin credenciales, sin riesgo):** inicializar git donde falte, escribir los `.gitignore`, hacer las **primeras commits limpias**, redactar un `README` por repo y dejar todo **listo para subir**.
- **Tú haces (no manejo cuentas ni contraseñas):** crear la **cuenta de GitHub**, crear los **repos privados vacíos**, y **autorizar la subida** (token/credenciales). Te guío paso a paso mientras lo haces.

## 6. Aviso de limpieza (importante antes de subir)

`Estructurando` ya tiene git y pesa **1,2 GB** (incluye `node_modules`). Antes de subirlo hay que **comprobar que su git NO esté arrastrando `node_modules`** ni los `*.plugin`; si los arrastra, hay que limpiarlos del seguimiento para no subir cientos de MB inútiles. Lo reviso en la fase 0.

## 7. Coste

Para tu caso, **gratis**: GitHub incluye repos **privados** ilimitados y minutos de automatización (CI) suficientes en el plan free.

## 8. Fases (orden propuesto)

1. **Fase 0 — local (yo, cuando digas):** git + `.gitignore` + primeras commits + limpieza de `Estructurando`. **Cero nube, cero riesgo, reversible.** Ya te da historial y "deshacer".
2. **Fase 1 — nube privada (tú creas, yo guío):** creas los 4 repos privados y subimos. Respaldo + PR activos.
3. **Fase 2 — cebo público (más adelante, deliberado):** repo público del visor con Apache-2.0, cuando decidas abrir el cebo.

---

**Decisiones que solo cierras tú:** (a) ¿4 repos o mono-repo?; (b) ¿confirmas que ningún IFC de casos es dato confidencial de cliente?; (c) ¿arrancamos por la Fase 0 (local) ya?

*Procedencia: hilo de coordinación · Aqyra-Raiz · plan git/GitHub para revisión y decisión de JM · 2026-06-28.*

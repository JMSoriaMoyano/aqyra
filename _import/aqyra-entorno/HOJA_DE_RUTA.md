# Hoja de ruta — Visor OpenBIM asistido por IA (primer producto)

> **Estado:** propuesta de la IA (PM / Ing. BIM-IFC) para revisión, ajuste y firma de JM · 2026-06-24.
> **Estado de ejecución (2026-06-24):** **V1 PAUSADO en F2** (F0/F1/F2 hechos y verificados; backlog F3–F6 en `ESTADO_V1.md`). **V2 ABIERTO** en hilo propio (arranque en `HILO-V2_brief_preproceso.md`). Marca firmada: **Aqyra** (D-004).
> **Decisión de producto (JM):** el visor es el **primer entregable de producto**. Diferencial = **IA + lenguaje natural** sobre un **entorno propio** y abierto, aunque las funciones del visor compitan en un mercado maduro. Estándares OpenBIM + código abierto. Estrategia **cebo y anzuelo** hacia una **spin-off**.
> **Anclaje de la necesidad:** la experiencia de cálculo de **Decopak HQ** exige, para el ingeniero, **pre-proceso** (ver estructura y cargas) y **post-proceso** (ver esfuerzos y deformaciones) sobre el modelo. Ese es el caso de uso guía.

---

## 0. Visión en una frase

> **Un visor OpenBIM donde describes en tu idioma lo que quieres ver y hacer —cargas, combinaciones, deformada, aprovechamientos— y el modelo abierto responde. La función es commodity; la curva cero por lenguaje natural sobre formato abierto es el diferencial.**

El visor no gana por features (ese mercado está maduro: Solibri, Revizto, Trimble, Dalux — ver `../HILO-1_benchmark_entorno.md`). Gana por **disolver la curva de aprendizaje** y por ser **nuestro** (embebible, sin licencia, sin binario), de modo que sea a la vez la herramienta de pre/post que necesitamos dentro y el cebo de entrada fuera.

---

## 1. Principios de diseño (no negociables)

1. **Formato abierto, operación nativa.** Todo entra/sale como texto (IFC, BCF, IDS). Cero dependencia de binario propietario. La IA opera sobre el sustrato abierto.
2. **Web sin instalación + tablet.** La adopción del encargado y del comprador amplio depende de la curva ínfima y del acceso desde navegador/tablet.
3. **Lenguaje natural como interfaz primaria del pre y el post.** No es un extra; es la forma de trabajar.
4. **Gobierno heredado.** Consume el núcleo **anclado** (`integracion/versions.lock`); todo resultado de cálculo mostrado va **bajo dos llaves**. El visor **nunca** presenta como verificado lo no firmado.
5. **Límite cebo/anzuelo desde el día 1.** Lo publicable (visor, adaptadores OpenBIM) en `publico/`; el moat (criterio, corpus, motores) en `privado/`.

---

## 2. Estado de partida (V0)

`visor-ifc` (skill del ecosistema): visor IFC autocontenido con **web-ifc + Three.js** — navegación 3D (órbita/zoom/encuadre), selección con panel de propiedades y Psets, árbol de estructura espacial, color/visibilidad por clase IFC. **Nivel N0 artesanal**; crece por versiones. Es la base real sobre la que se construye: no se parte de cero.

> **Baseline ampliado:** además del visor, ya existe el **compilador narración→IFC** (plugin `iso19650-openbim v0.8.2`: spec paramétrico + generador IFC4/4X3 + primitivas + catálogo bsDD + validación). El siguiente gran bloque heredado es la **Capa 2** (visor de mirador → editor paramétrico: round-trip del spec). Detalle y *hazards* en `estado-inicial_narracion-IFC.md`.

---

## 3. Las versiones del producto (V1 → V5)

Cada versión es un entregable con su Definición de Hecho (DoD). El orden sigue la necesidad de Decopak HQ: primero ver el modelo (V1), luego el pre-proceso (V2), luego el post-proceso (V3) —que es lo que te resuelve a ti como ingeniero—, luego el copiloto NL que lo hace producto (V4), y por fin el cebo desplegable (V5).

### V1 — Visor OpenBIM industrializado *(base del cebo)*
**Objetivo:** convertir `visor-ifc` (N0) en visor de **producto** (N3): robusto, embebible, web sin instalación, tablet.
- Carga IFC sólida (IFC4 / IFC4.3), federación de modelos, rendimiento (formato **Fragments** de That Open para modelos grandes).
- Estándares OpenBIM: **BCF** (ver/crear incidencias), **IDS** (validación de requisitos), **bsDD**.
- Industrialización: monorepo, contrato declarado, tests, empaquetado SemVer (alinea con `../HILO-2_diseno_tecnico_industrializacion.md`).
- **DoD:** abre cualquier IFC en navegador y tablet; navega, inspecciona Psets, ve/añade incidencias BCF; embebible en nuestro entorno.

### V2 — Pre-proceso estructural visual
**Objetivo:** ver **"estructura + cargas"** sobre el modelo (la necesidad de Decopak HQ, lado pre).
- Leer el **dominio de análisis estructural** del IFC (o del modelo neutro): barras, nudos, apoyos, secciones, materiales.
- Visualizar: modelo idealizado (analítico), apoyos, **cargas** (puntuales/distribuidas), **casos** y **combinaciones** (ELU/ELS).
- Edición ligera sobre el modelo (añadir/editar carga o apoyo) que **escribe de vuelta** al IFC/modelo neutro (texto, *diff*-able). *Esto materializa la **Capa 2·C** (round-trip del spec) heredada — ver `estado-inicial_narracion-IFC.md`; resolver aquí la decisión abierta de dónde se ejecuta la regeneración.*
- **DoD:** cargar Decopak HQ y ver su estructura idealizada + cargas + casos/combinaciones; editar una carga y verla persistir en el IFC.

### V3 — Post-proceso de resultados *(el entregable que resuelve al ingeniero)*
**Objetivo:** ver **esfuerzos y deformaciones** sobre el modelo (la necesidad de Decopak HQ, lado post).
- Consumir resultados del **motor-fem / motor-cálculo** anclado (contrato `C5`): deformada, diagramas **N/V/M**, reacciones, **aprovechamientos**.
- Visualizar: **deformada escalable**, mapas de color por esfuerzo/aprovechamiento, diagramas por barra, **elementos críticos** (p. ej. aprovechamiento > 0,9), envolventes por combinación.
- **Bajo dos llaves:** los resultados se muestran con su estado (propuesta / verificado-firmado); nunca se pinta como válido lo no certificado.
- **DoD:** sobre Decopak HQ, ver la deformada bajo una combinación ELU, colorear por aprovechamiento EC3 y listar los elementos al límite.

### V4 — Copiloto en lenguaje natural *(el hecho diferencial)*
**Objetivo:** el usuario maneja **pre y post hablando**. Aquí aflora la **capa 6 (operador IA)** por la superficie del visor.
- NL → acciones del visor: *"muéstrame la deformada de la combinación ELU2"*, *"colorea por aprovechamiento"*, *"oculta la arquitectura"*, *"filtra los pilares por encima de 0,9"*.
- NL → pre-proceso: *"añade una sobrecarga de uso de 5 kN/m² en la planta 3"*, *"pon un empotramiento en este nudo"*.
- NL → consulta e incidencias: *"¿qué vigas no cumplen flecha?"*, *"crea una incidencia BCF aquí"*.
- **DoD:** las operaciones clave de V2/V3 se ejecutan por lenguaje natural; un usuario sin formación opera el pre/post (curva ≈ cero).

### V5 — Cebo desplegable + ganchos al anzuelo *(spin-off)*
**Objetivo:** el cebo en el mercado, con el modelo de ingresos detrás.
- Despliegue **web SaaS**, **tier gratuito/subvencionado** (el cebo), onboarding mínimo.
- **OSS/licencias:** publicar la capa `publico/` con licencia clara; **verificar web-ifc paquete a paquete** (MPL-2.0 vs MIT — pendiente del Hilo 1) antes de cerrar.
- **Ganchos al anzuelo:** del visor al **cálculo de firma** (dos llaves), a la **reaplicación del corpus golden**, a features premium → **ingresos recurrentes**.
- **Telemetría** de adopción (enlaza con `metricas/` de 2.0).
- **DoD:** un usuario externo (objetivo **Can Cabassa**) usa el visor gratis y existe el camino de upgrade al anzuelo.

---

## 4. Carriles transversales (a todas las versiones)

- **Estándares OpenBIM:** IFC (4/4.3), **BCF**, **IDS**, **bsDD**, ISO 19650. El visor habla estándar, no formato propio.
- **Open source / licencias:** estrategia de licencia del cebo; verificación paquete a paquete del ecosistema That Open (MPL-2.0 / MIT); el moat nunca entra en el repo público.
- **Gobierno compartido:** consumo del núcleo anclado (`versions.lock`); resultados de cálculo bajo **dos llaves**; separación productor/QA; la IA opera, JM firma.
- **UX / adopción:** curva cero, tablet, web sin instalación — la barrera de entrada es el enemigo, no la falta de features.
- **Límite cebo/anzuelo:** revisado en cada versión; lo que se publica vive en `publico/`, el criterio/corpus en `privado/`.

---

## 5. Hitos y secuencia

| Hito | Entrega | Prueba |
|---|---|---|
| **H0** | Extraer repo + crear proyecto Cowork propio | Proyecto en marcha con sus instrucciones |
| **H1** | V1 visor industrializado | Abre IFC en tablet; BCF básico |
| **H2** | V2 + V3 sobre **Decopak HQ** | El ingeniero ve cargas (pre) y deformada/aprovechamiento (post) de Decopak HQ |
| **H3** | V4 copiloto NL | Pre/post por lenguaje natural; curva ≈ cero |
| **H4** | V5 cebo desplegable | Usuario externo (Can Cabassa) usa el visor; existe el gancho al anzuelo |

> **Demo guía (la que vende y la que necesitamos):** cargar el IFC de Decopak HQ y, hablando, ver las cargas, lanzar/inspeccionar el cálculo certificado y ver la deformada y los aprovechamientos sobre el modelo. Pre + post + lenguaje natural + formato abierto, en una sola pantalla.

---

## 6. Riesgos y decisiones abiertas para JM

**Riesgos**
- **Competir en mercado maduro de visores.** *Mitigación:* no competir en features; el diferencial es NL + curva cero + entorno propio + doble uso interno. El cebo no necesita ganar a Solibri en clash; necesita quitar la barrera de entrada.
- **Licencia OSS del stack.** web-ifc es MPL-2.0 (copyleft débil por fichero); verificar paquete a paquete antes de publicar (Hilo 1).
- **Fidelidad pre/post sobre el modelo.** Mapear resultados FEM al IFC sin pérdida es delicado. *Mitigación:* dos llaves; Decopak HQ como prueba.
- **Que el cebo canibalice esfuerzo del anzuelo.** *Mitigación:* el cebo es "lo justo + subvencionado"; el grueso defendible sigue en el corpus (disciplina de la tesis).

**Decisiones abiertas (la IA propone; JM cierra)**
1. ~~Nombre del producto~~ **RESUELTO (2026-06-24):** la marca es **Aqyra** (paraguas: CDE + visor + entorno). Ver `DECISIONES.md` D-004.
2. **Alcance de V1** (¿BCF e IDS desde V1 o se difieren a V2?).
3. **Modelo OSS exacto del cebo** (open-core, freemium, qué se publica abierto).
4. **Stack de datos:** Git+web-ifc puro vs **Speckle** como capa (decisión heredada del Hilo 1).
5. **Orden V2/V3:** ¿pre antes que post, o ambos en paralelo sobre Decopak HQ?

---

*Procedencia: hoja de ruta del primer producto (visor OpenBIM asistido por IA) · Estructurando 2.0 / proyecto Aqyra (IA · PM) · 2026-06-24 · para revisión, ajuste y firma de JM.*

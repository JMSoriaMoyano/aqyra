# Entorno — Hilo de inicio: V1 · Visor OpenBIM industrializado

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como primer mensaje del hilo de desarrollo del proyecto **Entorno** (ya extraído a su repo propio). Es autocontenido. Corresponde a **H1 / V1** de `HOJA_DE_RUTA.md`.

---

## 0. Objetivo

Convertir el visor base (`visor-ifc`, nivel **N0 artesanal**) en un **visor OpenBIM de producto (N3)**: robusto, embebible, **web sin instalación y en tablet**, sobre estándares abiertos. Es la **base del cebo** y la herramienta de visualización sobre la que después se montarán el pre-proceso (V2) y el post-proceso (V3).

## 1. Punto de partida (V0)

- **Visor:** `visor-ifc` — web-ifc + Three.js, navegación 3D (órbita/zoom/encuadre), selección con panel de propiedades y Psets, árbol de estructura espacial, color/visibilidad por clase IFC.
- **Baseline ampliado:** existe ya el **compilador narración→IFC** (`iso19650-openbim v0.8.2`) con su pipeline (`visor/pipeline.mjs` → `.frag` + props). Ver `estado-inicial_narracion-IFC.md` (incluye *hazards* técnicos del entorno).
- **No se parte de cero:** V1 industrializa lo que existe.

## 2. Alcance de V1

1. **Carga IFC sólida:** IFC4 e IFC4.3; **federación** de varios modelos; rendimiento en modelos grandes (formato **Fragments** de That Open).
2. **Estándares OpenBIM (en `publico/openbim/`):**
   - **BCF** — ver y **crear** incidencias.
   - **IDS** — validación de requisitos de información sobre el modelo.
   - **bsDD** — lectura de clasificación/propiedades.
3. **Web sin instalación + tablet:** navegador, responsive, usable en obra. *La curva de entrada es el enemigo, no la falta de features.*
4. **Embebible:** el visor se integra como componente en nuestro entorno.
5. **Industrialización (de N0 a N3):** monorepo, **contrato declarado**, tests, empaquetado **SemVer**. (Alinea con el diseño técnico de industrialización del producto.)

## 3. Fuera de alcance de V1 (no dispersar)

- **Pre-proceso** (estructura + cargas) → V2.
- **Post-proceso** (esfuerzos, deformada, aprovechamientos) → V3.
- **Copiloto en lenguaje natural** → V4. *(En V1 el NL no es el foco; la superficie NL vive en `publico/ui-nl/` y se enciende en V4.)*
- **Despliegue SaaS / cebo desplegable** → V5.
- **Capa 2 (editor paramétrico, round-trip del spec):** se prepara el terreno, pero su decisión abierta (dónde regenera) se resuelve en V2.

## 4. Principios no negociables

1. **Formato abierto, operación nativa.** Todo entra/sale como texto (IFC, BCF, IDS). Cero binario propietario.
2. **Web sin instalación + tablet** desde el día uno.
3. **Gobierno heredado.** El Entorno es **consumidor** del núcleo anclado (`integracion/versions.lock`). Aunque V1 todavía no muestre resultados de cálculo, la regla se respeta: **nunca** se pinta como verificado lo no firmado (dos llaves).
4. **Límite cebo/anzuelo.** Todo lo de V1 es **cebo**: vive en `publico/` (visor + adaptadores OpenBIM). Nada del moat (criterio, corpus, motores) entra aquí.

## 5. Definición de Hecho (DoD)

- Abre **cualquier IFC** (4 / 4.3) en **navegador y tablet**, sin instalación.
- Navega el modelo, inspecciona **Psets**, federación de ≥2 modelos.
- **Ve y añade incidencias BCF**; valida un requisito con **IDS**.
- Es **embebible** en nuestro entorno.
- Repo industrializado: contrato declarado, tests en verde, paquete **SemVer** publicado.

## 6. Decisiones abiertas (la IA propone; JM cierra)

1. **¿BCF e IDS completos en V1, o IDS se difiere a V2?** (acotar el alcance del primer entregable).
2. **Stack de datos:** web-ifc puro vs **Speckle** como capa — decisión heredada del benchmark (`HILO-1_benchmark_entorno.md`).
3. **Licencia OSS del cebo:** verificar el ecosistema That Open **paquete a paquete** (web-ifc es **MPL-2.0**; conviven posibles MIT) antes de publicar.
4. **Marca** del producto (placeholder "Entorno").

## 7. Primer paso del hilo (extracción ya hecha en H0)

- **Confirmar qué viaja con el Entorno** y qué se referencia del ecosistema 2.0: el benchmark y una copia/instantánea del gobierno viajan; el contrato **C8 (CDE)** y el corpus golden se quedan en la zona protegida de 2.0 y solo se **consumen** (anclados). Resolver esto antes de escribir código.

## 8. Método y reglas

- Antes de cada tarea, **leer los README** de las carpetas implicadas (`README.md`, `publico/`, `privado/`, `integracion/`).
- **Search-first** para estándares y licencias (BCF/IDS/bsDD, That Open); **citar fuente y fecha**; distinguir verificado de inferido.
- **Formato:** Markdown en el repo; sin .docx salvo petición explícita.
- La IA opera y prepara evidencia; **JM decide y firma**.

## 9. Entregables

- Visor V1 industrializado en `publico/visor/` + adaptadores en `publico/openbim/`.
- Tests y paquete SemVer.
- Demo de DoD (IFC en tablet + BCF + IDS).
- Registro de decisiones cerradas por JM (puntos del §6).

---

*Brief preparado por la IA (PM / Ing. BIM-IFC) · proyecto Entorno · 2026-06-23 · para lanzar el hilo de desarrollo de V1.*

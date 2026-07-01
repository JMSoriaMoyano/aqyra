# Aqyra — Hilo de inicio: V2 · Pre-proceso estructural visual

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como **primer mensaje** del nuevo hilo de desarrollo de **V2** (en el mismo proyecto Cowork *Aqyra*). Es autocontenido. Corresponde a **V2** de `HOJA_DE_RUTA.md`. V1 (visor) queda pausado en F2; su estado y backlog F3–F6 están en `ESTADO_V1.md`.

---

## 0. Objetivo

Llevar a Aqyra del **visor** (V1) al **pre-proceso estructural visual**: que el ingeniero **cargue el IFC y vea, hablando, la estructura idealizada y las cargas** sobre el modelo — y pueda **editar una carga o un apoyo y que persista** al modelo abierto. Es el lado **"pre"** de la necesidad de **Decopak HQ** y el primer entregable que de verdad resuelve al **Calculista** (la persona prioritaria; dirección de producto D-007).

## 1. Punto de partida (lo que ya existe)

- **Visor V1 (F0–F2) en `publico/`** — monorepo pnpm con el contrato **`AqyraViewer`** (`@aqyra/embed`), motor `@aqyra/visor` (carga IFC4/4.3 con web-ifc, federación, Psets, render three.js, cámara, selección, color/visibilidad por clase, **árbol de estructura espacial**). **12 tests verdes**; verificado en navegador real con Decopak HQ. Ver `ESTADO_V1.md` y `publico/DEV.md`.
- **Superficie de producto (D-007):** skin **Calculista** (`demo/calculista.html`) — lienzo limpio, **barra de comandos en lenguaje natural** (hoy stub de reglas → contrato), menús contextuales, deshacer. **Ya reserva** los comandos de pre-proceso ("añade una sobrecarga…", "apoyo…") respondiendo "llega en V2". Aquí aterriza V2.
- **Baseline Capa 2 (heredado):** el compilador **narración→IFC** (`iso19650-openbim`) y su pipeline; el siguiente bloque heredado es la **Capa 2·C (round-trip del spec)** — enlazar modelo↔spec, editar y regenerar. Ver `estado-inicial_narracion-IFC.md`.
- **web-ifc lee y ESCRIBE IFC en el navegador** (probado en V1). Esto es clave para el round-trip (ver §6).

## 2. Alcance de V2

1. **Leer el dominio de análisis estructural** del modelo: barras/nudos idealizados, **apoyos**, secciones, materiales. Fuente a decidir (§6): dominio estructural del IFC si existe · derivar del modelo físico · **modelo neutro** anclado del núcleo.
2. **Visualizar el "pre":** modelo **idealizado** (analítico) sobre/junto al físico, **apoyos**, **cargas** (puntuales/distribuidas), y **casos** y **combinaciones** (ELU/ELS) — con su estado de dato (`proposal`).
3. **Edición ligera con write-back:** añadir/editar una **carga** o un **apoyo** sobre lo que se ve, y **persistirlo al IFC/modelo neutro** como **texto diff-able** (cero binario). Materializa la **Capa 2·C**.
4. **Superficie:** las acciones de pre-proceso se exponen por la skin Calculista (contextual + barra de comandos), extendiendo el contrato `AqyraViewer`, sin ensuciar la UI.

## 3. Fuera de alcance de V2 (no dispersar)

- **Post-proceso** (esfuerzos, deformada, aprovechamientos, consumo del `motor-fem` · contrato C5) → **V3**.
- **Copiloto NL "de verdad"** (criterio del corpus) → **V4**; en V2 el NL sigue siendo el stub de reglas de la superficie pública.
- **BCF / IDS** (V1 · F3/F4, sesgo BIM Manager) — paralelos, no de V2.
- **Editor paramétrico completo / edición narrada en contexto** (Capa 2·A y ·B) — se prepara el terreno; el grueso es posterior.

## 4. Principios no negociables (heredados)

1. **Formato abierto, operación nativa.** IFC entra/sale como texto; el write-back de cargas/apoyos es *diff-able*. Cero binario propietario.
2. **Web sin instalación + tablet.** El pre-proceso se maneja en el navegador (coherente con D-002: web-ifc puro, sin servidor obligatorio).
3. **Dos llaves.** Las cargas/apoyos que el usuario define son **entradas** (`proposal`), no resultados verificados. El visor nunca pinta como firmado lo no firmado. La IA opera; **JM firma**.
4. **Límite cebo/anzuelo.** La **visualización y el write-back (mecánica)** son cebo → `publico/`. El **criterio** (qué cargas/combinaciones tocan según norma/corpus) es anzuelo → `privado/`, y se enciende con el copiloto (V4). El **puente al motor de cálculo** (C5) es de V3 y vive en `privado/`.

## 5. Definición de Hecho (DoD)

- Cargar **Decopak HQ** y ver su **estructura idealizada + apoyos + cargas + casos/combinaciones** sobre el modelo, en navegador.
- **Editar una carga** (o un apoyo) desde la superficie (contextual o comando) y verla **persistir en el IFC/modelo neutro** (re-abrir y sigue ahí).
- Todo lo nuevo en `publico/` (mecánica), con el estado de dato `proposal`; tests en verde; sin romper el contrato `AqyraViewer` (extensión SemVer MINOR).

## 6. Decisiones abiertas (la IA propone; JM cierra)

1. **Fuente del modelo analítico** *(la grande)*: (a) leer el **dominio estructural del IFC** (`IfcStructuralAnalysisModel`, miembros/conexiones/acciones) si el modelo lo trae; (b) **derivar** un idealizado del modelo físico (ejes de barras a partir de vigas/pilares); (c) consumir el **modelo neutro** anclado del núcleo. *Probable: (a) si existe, con fallback (b); (c) como puente para lo que el núcleo ya idealiza.*
2. **Dónde se ejecuta el round-trip / write-back** *(decisión heredada de Capa 2·C)*: **proceso local Python (IfcOpenShell)** vs **agente como backend** vs **— recomendación de la IA —** persistir **client-side con web-ifc** (que ya escribe IFC), manteniendo el principio "sin servidor" de D-002. *La IA propone empezar por write-back client-side de cargas/apoyos; reservar el backend solo si la regeneración paramétrica completa lo exige.*
3. **Modelo de datos de cargas/combinaciones:** representarlas en IFC estructural nativo vs en un **Pset/anejo propio** *diff-able* mientras IFC structural no esté garantizado en los modelos de entrada.
4. **Extensión del contrato `AqyraViewer`:** qué métodos añade el pre-proceso (p. ej. `getStructuralModel`, `addLoad`, `setSupport`, `listLoadCases`) y cómo se versiona (MINOR).

## 7. Primer paso del hilo

- **Antes de escribir código:** (1) inspeccionar un IFC real de **Decopak HQ** para ver **si trae dominio estructural** (`IfcStructuralAnalysisModel`) o solo físico — eso decide §6.1; (2) cerrar §6.2 (dónde regenera) con la recomendación client-side; (3) acotar el primer corte: *leer+visualizar* apoyos y una carga, y *un* write-back mínimo demostrable.

## 8. Método y reglas

- Antes de cada tarea, **leer los README** de las carpetas implicadas (`publico/`, `privado/`, `integracion/`) y `ESTADO_V1.md`.
- **Search-first** para estándares (IFC structural, IfcStructuralLoad*, combinaciones EC0/EC1) y para lo que toque del ecosistema; **citar fuente y fecha**; distinguir verificado de inferido.
- **Formato:** Markdown en el repo; sin .docx salvo petición explícita.
- **Consumo anclado** del núcleo vía `integracion/versions.lock`; no bifurcar el núcleo. La IA prepara la evidencia; **JM decide y firma**.

## 9. Entregables

- Lectura + **visualización del pre** (idealizado, apoyos, cargas, casos/combinaciones) en `publico/`.
- **Edición ligera + write-back** de una carga/apoyo al IFC (texto diff-able).
- Superficie en la skin Calculista (contextual + comandos), contrato extendido (SemVer).
- Tests y demo del DoD sobre Decopak HQ.
- Registro de decisiones cerradas por JM (§6) en `DECISIONES.md`.

---

*Brief preparado por la IA (PM / Ing. BIM-IFC) · proyecto Aqyra · 2026-06-24 · para lanzar el hilo de desarrollo de V2. V1 pausado en F2 (ver `ESTADO_V1.md`).*

# Estado de V1 — Aqyra (snapshot)

> **Qué es:** foto del avance de V1 (visor OpenBIM industrializado) tras cerrar **F2**. Sirve para retomar sin contexto y para ordenar lo que falta. Markdown en el repo; la IA opera, **JM firma**.
> **Fecha:** 2026-06-24.

---

## 1. Qué está construido y verificado

**Decisiones cerradas (firma JM):** D-001 a D-007 en `DECISIONES.md` — alcance BCF/IDS, web-ifc puro, licencia Apache-2.0, marca **Aqyra**, frontera/`versions.lock`, stack técnico (pnpm/Vite/Web Component/`@aqyra/*`), y dirección de producto (lienzo limpio + NL contextual).

**Código (`publico/`, monorepo pnpm):**

| Fase | Entregado | Verificación |
|---|---|---|
| **F0** | Monorepo (`visor`/`openbim`/`embed`/`ui-nl`/`demo`), **contrato** `AqyraViewer`, Web Component `<aqyra-viewer>`, CI + gate de licencias | typecheck + tests verdes |
| **F1** | Carga **IFC4 / IFC4.3** (web-ifc), **federación ≥2 modelos**, **Psets**, teselado → **three.js**, cámara (girar/zoom-al-cursor/pan-mano) | **navegador real con Decopak HQ** (3 IFC federados) + tests headless + e2e Playwright (CI) |
| **F2** | **Selección** por clic con resaltado, **Psets** del elemento, **color/visibilidad por clase**, **árbol de estructura espacial**, **aislado por elemento** | tests headless + validación en demo |

**Skin Calculista** (`demo/calculista.html`): prototipo de la dirección de producto — lienzo limpio, **barra de comandos NL** (stub de reglas → contrato), menús contextuales, **deshacer/historial**, listado **"clases"** interactivo (color/visibilidad/aislar), árbol sumonable.

**Tests:** **12/12 verdes** (`pnpm test`): carga, esquema, federación, Psets, teselado, grafo three.js, control por clase, árbol espacial. `pnpm typecheck` y build de paquetes OK. Gate de licencias activo (bloquea GPL/AGPL).

---

## 2. Gobierno realizado en código

- **Frontera cebo/anzuelo:** todo vive en `publico/`. La superficie NL es pública (`ui-nl/` + stub Calculista); el **criterio** del copiloto es de `privado/` (V4). El motor de cálculo no se toca aquí.
- **Dos llaves:** el contrato reserva el estado de dato `proposal` / `verified-signed`; el visor nunca pintará como verificado lo no firmado (relevante en V3).
- **Formato abierto:** IFC/BCF/IDS como texto; cero binario propietario.
- **Consumo anclado:** `integracion/versions.lock` (tags N1.1; sello de release pendiente de JM).

---

## 3. Lo que falta de V1 — backlog ordenado (F3 → F6)

| Fase | Objetivo | DoD | Notas |
|---|---|---|---|
| **F3 · BCF** | Ver y **crear incidencias** BCF sobre el modelo; import/export `.bcfzip` | Crear una incidencia con viewpoint, exportarla y reimportarla | Punto del DoD de V1. Sobre `@thatopen/components` `BCFTopics`. Encaja como acción contextual ("crear incidencia aquí"). |
| **F4 · IDS + bsDD** | **Cargar un IDS y validar** requisitos de información; lectura bsDD | Validar un requisito (p. ej. `IfcDoor`→`FireRating`) y mostrar el informe | Punto del DoD. `IDSSpecifications`. Autoría de IDS → V2. |
| **F5 · Tablet + hardening** | Responsive/táctil, gestos, rendimiento; **presupuesto de FPS** sobre modelo grande | Usable en tablet real sin instalación | Cierra el "tablet día uno". Mide FPS con Decopak HQ. |
| **F6 · Cierre de producto** | Cobertura de tests del contrato, `THIRD-PARTY-NOTICES` real, **release SemVer**, demo del DoD | Paquete publicado (registro privado); demo reproducible | Antes de publicar: check legal D-003. |

**Recomendación de la IA (JM decide):** **F3 (BCF)** a continuación — completa un punto claro del DoD, es independiente y demoable, y encaja con la UX contextual. F5 (tablet) puede solaparse en paralelo.

### Carril transversal de V1 · "Higiene BIM / saneamiento" (D-008) — EN CURSO

Aqyra organiza el modelo por **ejes/lentes** (1 espacial + N funcionales). Secuencia firmada:

1. **Sanear el eje espacial** (reasignar por geometría: cota/centroide → planta) + **consulta NL simple** ("¿cuántas ventanas en P1?") — *primer corte, en marcha*.
2. **Navegación multi-lente** (leer/derivar ejes funcionales: zonas, sistemas, estructural) — incremento.
3. **Autoría asistida de estructuras funcionales** (proponer/escribir `IfcZone`/`IfcSystem`/`IfcGroup` por criterio) — incremento, anzuelo fuerte.

Gobierno: lo que la IA deriva/crea es `proposal`; write-back con preview + aprobación; original preservado para deshacer. Mecánica = cebo; criterio = anzuelo (corpus).

---

## 4. Residuales abiertos (de `DECISIONES.md`)

1. **Sello del release N1.1** del núcleo: golden verde + tag GPG firmado (JM).
2. **Verificación de marca/dominio** de Aqyra (EUIPO/USPTO/WHOIS) y relación con Aqyra-CDE (paraguas único, D-004).
3. **Check legal** de atribuciones antes de publicar `publico/` (D-003) + escaneo del árbol real de dependencias.
4. **Benchmark `HILO-1`**: ya en repo y cotejado ✅.

---

## 5. Cómo retomar / probar

```bash
cd publico
pnpm install
pnpm test                              # 12/12
pnpm --filter @aqyra/demo dev          # demo clásica: localhost:5173
                                       # skin Calculista: localhost:5173/calculista.html
```

Arrastra IFC (Decopak HQ en `…/Estructurando 2.0/pilotos/decopak-hq`). Lanzador en Windows: `INICIAR_DEMO_AQYRA.bat`.

---

*Procedencia: estado de V1 · proyecto Aqyra · IA (PM / Ing. BIM-IFC) · 2026-06-24 · para seguimiento y firma de JM.*

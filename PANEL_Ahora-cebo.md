# Panel de mando — horizonte "Ahora" (cebo)

> **Qué es:** el panel maestro que gobierna la ejecución del horizonte **Ahora** del `ROADMAP_cebo-anzuelo.md`. No contiene código (Aqyra-Raiz observa, no copia); enrola los proyectos de producto contra su contrato, su golden y el sello de dos llaves.
>
> **Fecha:** 2026-06-26 · **Decisión de corte:** 3 contenedores (no 5), por acoplamiento real de substrato/contrato.

---

## 1. Los tres proyectos del "Ahora"

| # | Proyecto | Dónde vive el código | Contrato | Hilo supervisor |
|---|---|---|---|---|
| **P1** | **Visor/Editor IFC** (base + edición + skin Diseño + auditoría básica) | `Entorno/publico/visor` (+ `iso19650-openbim` para auditoría) | **C1** (parser/IFC) | `INICIO-hilo_P1-visor-editor.md` |
| **P2** | **Predim Estructuras** (aflora el motor en el visor, gratis, sin export firmable) | superficie en `Entorno`; motor en `Estructurando` (`motor-fem`/`motor-calculo`) | **C5** (motor-fem, **firmado**) | `INICIO-hilo_P2-predim-estructuras.md` |
| **P3** | **Plataforma — Tope de uso justo** (guardarraíl de token) | runtime del producto (`Entorno`) + telemetría | *fuera del esquema C1–C8 (capa operativa/plataforma)* | `INICIO-hilo_P3-plataforma-tope-uso.md` |

## 2. Grafo de dependencias (no son hermanos)

```
        P1 Visor/Editor  ── es el espinazo, todo aflora aquí
            │
            ▼  (necesita dónde mostrarse)
        P2 Predim Estructuras  ── consume C5 (ya firmado)

        P3 Tope de uso ── envuelve a P1 y P2 (mide su uso);
                          se instrumenta pronto, se hace vinculante después.
                          NO bloquea a P1/P2.
```

- **P2 depende de P1:** el predim necesita la superficie del visor para aflorar.
- **P3 es transversal:** no se "termina"; instrumenta el COGS pronto y limita cuando hay volumen.
- **P1 no depende de nadie:** arranca ya. Es la prioridad.

## 3. Modelo de gobierno (qué hace que sea "gobernado", no informal)

Cada proyecto es **consumidor de un contrato** y su *definition of done* **no es "funciona"** — es el **sello de dos llaves**, igual que C5:

1. **Atado a contrato + versión.** P1→C1, P2→C5. Anclar la versión consumida en el `versions.lock` que corresponda (`Entorno/integracion/versions.lock`); **adoptar solo si la golden está en verde**.
2. **Llave 1 = golden verde.** Cada proyecto necesita su golden propio (como C5 tiene las DEC-*). Ver §4.
3. **Llave 2 = firma de JM** para liberar versión. La IA prepara y propone; **no certifica**.
4. **Supervisión.** Un hilo por proyecto (los `INICIO-hilo_P*`) mantiene el proyecto honesto contra su contrato + golden, gestiona las dependencias cruzadas y gatea las releases. **Este panel es el roll-up**; el `ROADMAP_cebo-anzuelo.md` es el plano.

## 4. Golden previsto por proyecto (el blanco a verde)

| Proyecto | Golden (Llave 1) — verde = adoptar |
|---|---|
| P1 Visor | abre el IFC de referencia, propiedades/Psets/árbol coherentes, no rompe |
| P1 Auditoría | reporta las no-conformidades correctas del IFC de referencia |
| P2 Predim | coincide con la golden de su familia (DEC-*) dentro de tolerancia; marcado `proposal`; **sin export firmable** |
| P3 Tope | un free que supera el cap es frenado/derivado a Pro; COGS por usuario acotado |

## 5. Reglas heredadas del gobierno (no romper)

- Un fallo no se arregla aflojando la golden — **solo corrigiendo el código**.
- **Solo JM** firma releases (Llave 2) y cierra las decisiones marcadas en cada hilo.
- El consumidor nunca consume "latest" ni rama viva: **bump → golden → adoptar si verde**.
- **Formato abierto** en toda frontera. Predim y visor son **cebo**: se sienten gratis (sin export firmable, sin medidor visible).
- **No mezclar build interno y tag de release** (ver la nomenclatura de versiones del ecosistema).

## 6. Cómo se opera (sala de control vs hilos de trabajo)

Dos niveles de hilos, no mezclar:

- **Hilos de trabajo — dentro de P1/P2/P3.** Donde se construye. El `INICIO-hilo_P*` arranca el hilo, que es a la vez **ingeniero y supervisor** de su línea: hace el trabajo y se autogobierna contra su contrato + golden. **El seguimiento del día a día de cada proyecto vive en su propio proyecto**, no aquí.
- **Hilo de coordinación — dentro de Aqyra-Raiz.** **Uno, no tres.** No construye: **coordina.** Cometidos: foto de conjunto contra el roadmap, vigilar dependencias cruzadas (P2 espera a P1; P3 envuelve a ambos), preparar las releases que necesitan la firma de JM (2ª llave) y mantener este panel y el roadmap al día. Arranque: `INICIO-hilo_coordinacion.md`.

**Mecanismo — coordinación por artefactos, no por chat entre hilos** (los proyectos están aislados): cada hilo de trabajo deja su estado en sitios compartidos —golden verde en `contratos-golden`, versión anclada en `versions.lock`, su fila en este panel—. El hilo de coordinación **los lee**. Los ficheros son el bus de sincronización.

**Cadencia:**

1. Se trabaja en los hilos de P1/P2/P3; cada uno **actualiza el estado compartido** al cerrar un hito.
2. Para la foto global (semanal / ante una release / ante una decisión transversal), el hilo de coordinación lee panel + roadmap + `versions.lock` + estado de golden y reporta dónde está todo, qué se ha desbloqueado y **qué falta firmar**.
3. JM firma la release (2ª llave) → se actualizan los artefactos → el hilo de coordinación lo refleja.

## 7. Estado (act. 2026-06-28)

- **Contratos base:** C1 (iso19650-openbim 0.8.2), C5 (motor-fem, **firmado** 2026-06-26). **Numeración reconciliada** (C1–C8 + CN-1/CN-2/CN-3, firmada 2026-06-27); registro único en `contratos-golden/README.md`.
- **P1 Visor/Editor:** **2 releases firmadas (28-jun)** → **`@aqyra/visor 0.4.0` anclado** (`visor-ifc` en `integracion/versions.lock`), C1 sin cambios:
  - **0.3.0** — Georreferenciación + Norte real/soleamiento.
  - **0.4.0** — Entorno («planta del entorno» Catastro/CartoCiudad→GeoJSON) + terreno/topografía. *Abierto no-bloqueante: confirmar BU/viales en vivo.*
  - Golden común VERDE (17 ficheros/119 tests) en `VERIFICAR_V3` (28-jun).
  - **Núcleo-elementos (cebo, `publico/demo`) — FIRMADO (28-jun):** capa de elementos físicos **IfcColumn** (retícula → pilares por planta) + **IfcSlab** (forjados automáticos, plantas 1..cubierta). Puente a `reticulas_pilares` + `forjados:true` (frontera-cero, C1 sin bump). **Golden 13/13 verde** (`columns.golden`). Mejoras: resaltado de selección árbol→dibujo, pilares segmentados por planta, planta tipo 2D con retícula; fix del cliente bsDD (`CLASS_URI` colgante). — Llave 1 ✔ · Llave 2 (firma JM) ✔
  - **Cola lista para firmar (golden ya verde):** parking en peine (`parking.golden`, 7/7) — commit aparte.
- **P2 Predim:** bloqueado, esperando superficie estable de P1 (ya empieza a haberla).
- **P3 Tope de uso:** sin arrancar (sin telemetría aún).
- **Siguiente acción:** firmar el parking en peine (commit aparte); luego seguir la capa de elementos con muros/carpintería (mismo molde: `ElementInstance` + otra `ifcClass`).

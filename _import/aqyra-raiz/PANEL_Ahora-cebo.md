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

- **Contratos base:** C1 (**iso19650-openbim 0.10.0**, evolución «apertura familias P1» FIRMADA 28-jun), C5 (motor-fem, **firmado** 2026-06-26). **Numeración reconciliada** (C1–C8 + CN-1/CN-2/CN-3, firmada 2026-06-27); registro único en `contratos-golden/README.md`.
- **P1 Visor/Editor:** **2 releases firmadas (28-jun)** → **`@aqyra/visor 0.4.0` anclado** (`visor-ifc` en `integracion/versions.lock`), C1 sin cambios:
  - **0.3.0** — Georreferenciación + Norte real/soleamiento.
  - **0.4.0** — Entorno («planta del entorno» Catastro/CartoCiudad→GeoJSON) + terreno/topografía. *Abierto no-bloqueante: confirmar BU/viales en vivo.*
  - Golden común VERDE (17 ficheros/119 tests) en `VERIFICAR_V3` (28-jun).
  - **Núcleo-elementos (cebo, `publico/demo`) — CAPA COMPLETA y FIRMADA (28-jun):** elementos físicos **IfcColumn** (retícula → pilares por planta) · **IfcSlab + huecos** (forjados automáticos, plantas 1..cubierta) · **IfcWall** (fachada/tabique/divisoria/núcleo-pasante) · **IfcDoor/IfcWindow** · **IfcStair**. **Dos llaves puestas:** Llave 1 = VERIFICAR verde (typecheck limpio + golden `columns.golden` **35/35**, suite **144/144**); Llave 2 = **tag git firmado** `cebo-elementos-2026-06-28` (`Good signature` GPG 8FD1E413…0942). Commit `9816593` en `aqyra-entorno`/main. *(Antes de firmar se cerraron 3 errores de typecheck en `demo/src` —incl. un TS2367 que era rama muerta real: la carpintería no se podía borrar; ver `DIAGNOSTICO_typecheck_cebo-firma.md`.)*
  - **Parking en peine — FIRMADO (28-jun):** Llave 1 = golden `parking.golden` **7/7**; Llave 2 = **tag** `cebo-parking-2026-06-28` (`Good signature`). Mismo commit `9816593`.
  - **RFC C1 — evolución completa para las 3 familias de P1 (A edificación · B trazado · C normativa), `RFC_C1-apertura_familias-P1.md`:** **una sola evolución de C1, completa y diseñada — NO parches** (decisión JM 28-jun: «no más parches»). Principio doble: (1) `alto.json` **forward-open** → el cebo emite por delante, el contrato nunca bloquea el preview; (2) **capacidad-completa** → cuando algo entra en C1 entra **entero y genérico**, para no re-tocar el contrato por cada variante. **Contenido:** huecos **generalizados** (cualquier anfitrión) + catálogo de **clases abierto** (`elementos[].ifcClass`, cubre ascensor y futuras sin re-bump) + **alineaciones completas** (planta+alzado+sección+peralte, reutilizando lo que C1 **ya parsea y genera** en Ola 5) + esquema forward-open. *A* y *C* frontera-cero; *B* es wiring de una capacidad existente. **Una golden** prueba la versión entera. El alcance de las 3 familias está **CERRADO** en `CIERRE-ALCANCE_P1-A-B-C.md` y en la cabecera de cada `INICIO-hilo_P1-A/B/C` (auditoría básica P1·C = nomenclatura `AQ-*` + **doble clasificación bsDD + Uniclass**, JM 28-jun). Implementada por el hilo de `Estructurando` (entrega en `ENTREGA_C1-apertura/`). **Estado: ✅ FIRMADA (28-jun) — dos llaves puestas:** Llave 1 = golden **`C1-APERTURA-01` VERDE** (alineación clotoide+acuerdo CUMPLE · huecos losa+muro · IfcTransportElement · 7/7 bsDD+Uniclass); Llave 2 = tags firmados **`c1-evolucion-2026-06-28`** (`aqyra-motor` 039176e) + **`c1-golden-2026-06-28`** (`aqyra-contratos-golden` 7a180b4). **Anclado: `iso19650-openbim 0.10.0`** en `versions.lock` (`aqyra-entorno` 9937852). El lado cebo (emitir `huecos`/`ifcClass`/`alineaciones[]`/Uniclass) queda para P1·A/B/C en `Entorno`, ya contra el contrato completo. Higiene no bloqueante: el CHANGELOG de `iso19650-openbim` salta 0.7.0→0.10.0 (tag previo v0.8.2) — reconciliar el historial en el hilo de motor.
- **P2 Predim:** bloqueado, esperando superficie estable de P1 (ya empieza a haberla).
- **P3 Tope de uso:** sin arrancar (sin telemetría aún).
- **Respaldo git/GitHub — Fase 1 COMPLETA (verificado en disco 28-jun):** los **4 repos privados** están en GitHub, rama `main`, con `local == origin/main` (en sync): `aqyra-motor` **039176e** (=`Estructurando`; +C1 evolución, tag `c1-evolucion`), `aqyra-entorno` **9937852** (=`Entorno`; cebo firmado + anclaje `iso19650-openbim 0.10.0`), `aqyra-contratos-golden` **7a180b4** (=`Estructurando 2.0`; golden `C1-APERTURA-01` + tag `c1-golden`), `aqyra-raiz` **6e92a24** (=`Aqyra-Raiz`; docs de la sesión 28-jun subidos: RFC C1, cierre de alcance, hilos P1·A/B/C/motor, paquetes y `.bat`/`.ps1` de firma). **Los 4 repos al día.** Caja fuerte en la nube + PR = 2ª llave operativos. **Sello de 2ª llave del visor = tag git firmado** (decisión JM 28-jun). Detalle del día a día en `INICIO-hilo_git-firmas-operaciones.md`. *(Fase 2 = cebo público, aún sin arrancar, deliberada.)*
- **Siguiente acción:** (a) ✅ HECHO — capa de elementos + parking firmados (28-jun); (b) ✅ HECHO — **evolución de C1 «apertura familias P1» FIRMADA** (iso19650-openbim 0.10.0; golden `C1-APERTURA-01`; tags `c1-evolucion` + `c1-golden`; anclado en `versions.lock`) → **las 3 familias P1·A/B/C quedan desbloqueadas contra el contrato completo**; (c) **arrancar P1·A/B/C** en `Entorno` (emitir `huecos`/`ifcClass`/`alineaciones[]`/Uniclass) y **commitear/pushear los docs de esta sesión en `aqyra-raiz`**. Cosmético pendiente: reconciliar docs de estado de C5 y el historial de CHANGELOG de `iso19650-openbim` (0.7.0→0.10.0) **sin tocar el manifiesto firmado del motor**.

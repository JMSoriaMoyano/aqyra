# Plan de consolidación del ecosistema Aqyra

> **Propósito:** convertir el desorden detectado en `MAPA_ECOSISTEMA.md` en acciones priorizadas. Nada de esto se ha ejecutado: es una propuesta para que JM decida. Las acciones destructivas (borrar/mover/renombrar) están marcadas y **requieren tu confirmación explícita**.
>
> **Fecha:** 2026-06-26 · **Principio:** mínimo movimiento, máxima claridad. No reorganizar por reorganizar.

---

## Resumen: 6 focos de desorden

| # | Foco | Gravedad | Riesgo de tocarlo | Acción tipo |
|---|---|---|---|---|
| 1 | Deriva de marca (Aquira / Aqyra) | ✅ RESUELTO | Bajo | Decidido 2026-06-26 |
| 2 | Triplicación de "Estructurando" | **Alta** | Medio | Aclarar verdad + archivar |
| 3 | `versions.lock` desincronizados | **Alta** | Bajo | Sincronizar |
| 4 | Artefactos `.plugin` duplicados (lastre) | Media | Bajo | Archivar/limpiar |
| 5 | Placeholders vacíos | Baja | Nulo | Retirar |
| 6 | Cierre formal del release N1.1 | Media | — | Proceso (JM firma) |

---

## Foco 1 — Deriva de marca: Aquira vs Aqyra  ✅ RESUELTO (2026-06-26)

**Qué pasaba:** la decisión **D-004** (firmada 2026-06-24) fijaba la marca en **«Aqyra»**, pero quedaba abierto cómo se relacionaba con el CDE, y la carpeta raíz se llamaba `Aquira Alfa` (grafía con "u/i" incorrecta).

**Hallazgo (verificado en disco):** la grafía "Aqyra" **ya era consistente en 39 documentos** del ecosistema. La única deriva textual estaba en el nombre de la carpeta raíz; no había que limpiar documentos.

**Decisiones tomadas por JM (ver `MARCA_Y_NOMENCLATURA.md`):**
1. **Grafía oficial única: `Aqyra`** (a-q-y-r-a, sin "u"). Cierra la ambigüedad.
2. **Marca paraguas única:** Aqyra = CDE + visor + entorno + ecosistema. Los módulos se nombran descriptivamente ("el visor de Aqyra"). Resuelve el punto abierto de D-004.
3. **Renombrado de la raíz:** `Aquira Alfa` → `Aqyra-Raiz`, lo ejecuta JM desde Windows; tras renombrar, reconectar el proyecto en Cowork.

**Pendiente (no bloqueante):** verificación externa de dominio/marca/scope (heredada de D-004) — ver `MARCA_Y_NOMENCLATURA.md §5`.

**✅ Hecho (2026-06-26):** cierre anotado en `Entorno/DECISIONES.md` (D-004), preservando el texto firmado original y añadiendo el bloque de cierre con grafía y estructura de marca.

---

## Foco 2 — Triplicación de "Estructurando"  ✅ HECHO (2026-06-26)

**Qué pasaba:** tres cosas con nombre casi idéntico:
- `Estrucutrando/` — el taller real (errata incluida; ya renombrado a `Estructurando`), 1,1 GB, productor vivo.
- `Estructurando 2.0/` — la capa de gobierno/consumidor, limpia, reciente.
- `Estrucutrando/Estructurando-2.0/` — una copia anidada del concepto 2.0 dentro del taller.

**Verdad canónica:** `Estructurando 2.0/` (raíz) = gobierno; `Estructurando/` = taller/productor.

**Acciones:**
1. ✅ **Copia anidada eliminada (2026-06-26).** Verificado antes de borrar: era una foto del 23-jun sin ningún contenido único (subconjunto de la raíz). Cero pérdida.
2. ✅ **Errata corregida `Estrucutrando` → `Estructurando` (2026-06-26),** renombrada por JM desde Windows. Riesgo confirmado nulo en código: las referencias a la errata en `.py/.json/.txt/.yml` eran rutas de sesiones antiguas del sandbox (ya muertas) o artefactos de build regenerables. Menciones cosméticas en `.md` refrescadas.

---

## Foco 3 — `versions.lock` desincronizados  ✅ HECHO (2026-06-26)

**Qué pasaba:** tres punteros con valores distintos:
- `Entorno/integracion/versions.lock` → base anclada N1.1 (motor-fem 0.1.0, iso19650 0.8.2…).
- `Estructurando 2.0/versions.lock` → plantilla, todo a `0.0.0`.
- Plan N1.1 (en 2.0) → tags del primer corte.

**Acción ejecutada:** `Estructurando 2.0/versions.lock` rellenado a **paridad con Entorno** (misma base anclada N1.1). Los dos consumidores anclan ahora lo mismo y se mueven juntos. No toca código, solo alinea punteros.

**⚠️ Brecha descubierta (importante):** el productor (`Estructurando`) ya ha **empaquetado versiones mucho más nuevas** que la base anclada que consumen ambos:

| Componente | Anclado (consumidores) | Empaquetado en disco | Salto |
|---|---|---|---|
| iso19650-openbim | 0.8.2 | **0.9.2** | menor |
| motor-calculo | 0.1.0 | **0.23.0** | **grande** ⚠️ |
| motor-fem | 0.1.0 | **0.3.0** | medio |
| puentes | 0.0.0 | **0.6.0** | nuevo |
| obras-lineales | 0.0.0 | **0.4.0** | nuevo |
| instalaciones | 0.0.0 | **0.3.0** | nuevo |

Esto queda registrado en el bloque `disponible-no-adoptado:` del propio lock de 2.0. **No se ha subido a estas versiones**: hacerlo exige golden en verde + firma de JM (es el **Foco 6 / cierre N1.1**). El salto de `motor-calculo` (0.1.0 → 0.23.0) es el que más cuidado pide: 22 versiones MINOR pueden haber cambiado contratos.

---

## Foco 4 — Artefactos `.plugin` duplicados  ✅ HECHO (2026-06-26)

**Qué pasaba:** 35 ficheros `.plugin` (versiones históricas de los 6 plugins) en la raíz del taller, mezclando "fuente" con "releases empaquetados" y tapando cuál es la versión viva.

**Matiz:** pesaban solo **2,5 MB en total** — NO eran el lastre del 1,1 GB (eso es `node_modules`/IFCs). El problema era de claridad, no de espacio.

**Acción ejecutada:** las **27 versiones históricas** de la raíz movidas a `Estructurando/_releases-historico/`. A la vista quedan solo las **7 versiones vivas** (motor-calculo 0.23.0 + el `.plugin` sin versionar, iso19650 0.9.2, motor-fem 0.3.0, puentes 0.6.0, obras-lineales 0.4.0, instalaciones 0.3.0). El `.plugin` v0.22.0 anidado en `Casos-de-uso/caso-15` se dejó intacto (es contextual a ese caso).

---

## Foco 5 — Placeholders vacíos  ✅ HECHO (2026-06-26)

**Qué pasaba:** `Visor IFC/` (0 ficheros) y la raíz estaban vacías.

**Acción ejecutada:** `Visor IFC/` **retirada** (el visor vive en `Entorno/publico/visor` y en el taller). `Aqyra-Raiz/` ya no está vacía: es el panel raíz.

---

## Foco 6 — Cerrar el release N1.1  📋 ENCARRILADO (2026-06-26)

**Diagnóstico (2026-06-26):** N1.1 **no es cerrable hoy**. No es "firmar y listo": el **corpus golden está vacío**, hay un **defecto abierto (DEC-A1, NO APTO)**, la QA se corrió **sin PyNite** y **sobre versión no anclada**, y falta la **firma de JM**. La "brecha" de versiones es en parte nomenclatura (build interno del taller vs tag de release).

**Entregado:** la secuencia de cierre está en **`FOCO6_cierre_N1.1.md`** (5 pasos: sembrar golden → corregir A1 → re-ejecutar con PyNite → anclar versión → sello de dos llaves), con las decisiones que solo cierra JM.

**Siguiente:** ejecutar en un **hilo dedicado** — texto de arranque listo en **`INICIO-hilo_Foco6_cierre-N1.1.md`**. Empezar por P1 (sembrar el corpus golden con los 6 casos de Decopak HQ), idealmente en entorno con PyNite instalable.

---

## Orden recomendado (de mayor beneficio / menor riesgo a mayor)

1. ~~**Foco 1** (marca Aqyra)~~ ✅ **HECHO 2026-06-26.**
2. ~~**Foco 3** (sincronizar versions.lock)~~ ✅ **HECHO 2026-06-26** (2.0 a paridad con Entorno; brecha hacia versiones nuevas registrada).
3. ~~**Foco 2** (triplicación "Estructurando")~~ ✅ **HECHO 2026-06-26** (anidada borrada, errata corregida, menciones refrescadas).
4. ~~**Foco 4** (archivar `.plugin` históricos)~~ ✅ **HECHO 2026-06-26** (27 archivados, 7 vivos).
5. ~~**Foco 5** (retirar vacíos)~~ ✅ **HECHO 2026-06-26** (`Visor IFC` retirada).
6. **Foco 6** (cerrar N1.1 + decidir el salto a las versiones nuevas) — **único pendiente.**

---

## Qué necesito de ti para avanzar

- ~~Decisión de marca (Foco 1)~~ ✅ hecha: Aqyra, paraguas única.
- ~~Foco 3 (sincronizar `versions.lock`)~~ ✅ hecho.
- ~~OK para cerrar D-004 en `Entorno/DECISIONES.md`~~ ✅ hecho.
- **Autorización por foco** para lo destructivo (renombrar / mover / borrar). Sin tu OK, no toco nada.
- **Decisión pendiente (Foco 6):** ¿cuándo subir los consumidores a las versiones nuevas del taller (golden + tu firma)? El salto de `motor-calculo` 0.1.0 → 0.23.0 es el crítico.

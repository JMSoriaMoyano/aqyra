# Paquete de firma — cebo: capa de elementos + parking en peine

> **Para JM (2ª llave).** Preparado por el hilo de coordinación (Aqyra-Raiz, 2026-06-28). La IA **prepara y verifica la Llave 1; tú pones la Llave 2**. El *cómo* operativo (los `.bat`, los comandos GPG) lo ejecuta el **hilo de Git/Firmas** (`INICIO-hilo_git-firmas-operaciones.md`); este documento dice **qué** se sella, **qué falta** y **qué decides tú**.

---

## 1. Qué se sella (2 piezas, commits aparte)

| # | Pieza | Repo / carpeta | Golden (Llave 1) |
|---|---|---|---|
| **A** | **Capa de elementos del cebo** — IfcColumn · IfcSlab+huecos · IfcWall (fachada/tabique/divisoria/núcleo-pasante) · IfcDoor/IfcWindow · IfcStair | `aqyra-entorno` → `Entorno/publico/demo` | `test/columns.golden.test.ts` (**JM: 35/35**) |
| **B** | **Parking en peine** | `aqyra-entorno` → `Entorno/publico/demo` | `test/parking.golden.test.ts` (**7/7**) |

**No entra en este paquete:** el parche `losas[].huecos` (frontera C1 abierta). Esa pieza es **firma de C1**, no del cebo, y sigue su propio camino (parche → bump `iso19650-openbim` → golden de C1 → anclar en `versions.lock` → firma). No mezclar en el mismo commit/firma.

---

## 2. ⛔ Llave 1 — gate ANTES de firmar (acción tuya)

**No es verificable desde disco a día de hoy.** El último resultado guardado, `Entorno/VERIFICAR_V3_resultado.txt`, es del **25-jun (17 ficheros / 119 tests)** y **no contiene** ninguno de los dos golden: los ficheros `columns.golden.test.ts` y `parking.golden.test.ts` se crearon el **27-jun**, después de ese resultado. Y ese run no mostraba tests del workspace `publico/demo`.

Antes de firmar, hay que dejar Llave 1 **fresca y trazada**:

1. Ejecutar `Entorno\VERIFICAR_V3.bat` (con **Enter**; el doble clic a veces solo selecciona).
2. **Confirmar en el nuevo resultado** que aparecen y pasan: `columns.golden.test.ts` (capa de elementos) y `parking.golden.test.ts`. *Comprobar de paso que el scope del `.bat` (`pnpm test` en `publico/`) llega al workspace `publico/demo`; si no salieran, correr `pnpm -C publico/demo test` y adjuntar ese log.*
3. Guardar el `VERIFICAR_V3_resultado.txt` fresco como **evidencia** de la Llave 1 (se commitea con el paquete).

> Regla de oro: un golden en rojo no se arregla aflojando tolerancia ni editando el valor esperado — solo corrigiendo el código.

---

## 3. Llave 2 — qué firmas (hay que elegir mecanismo)

**Hueco detectado:** el visor **no tenía mecanismo de firma en disco**. El motor sella `Estructurando/release.manifest.json` + su `.asc`. En `Entorno` no había manifiesto, ni `.asc`, ni tag firmado — las "firmas" 0.3.0/0.4.0 quedaron declaradas en docs/`versions.lock` pero sin artefacto criptográfico.

> ✅ **DECISIÓN JM (2026-06-28): Opción 1 — tag git firmado.** Este es el mecanismo de 2ª llave del cebo (visor). Queda fijado para futuras releases del visor.

**Opción 1 (ELEGIDA) — tag git firmado.** El motor sella un `.plugin` distribuible (por eso usa manifiesto con `sha256` del artefacto). El visor es un **workspace de fuente sin `.plugin`**: su ancla natural es el **commit**. → Una **etiqueta anotada y firmada con GPG** sobre el commit del paquete es el cierre:

```
# (lo prepara el hilo Git/Firmas como .bat; lo ejecutas tú)
git tag -s cebo-elementos-2026-06-28 -m "Cebo capa de elementos · golden columns.golden 35/35 verde · run VERIFICAR <fecha>"
git tag -s cebo-parking-2026-06-28   -m "Cebo parking en peine · golden parking.golden 7/7 verde · run VERIFICAR <fecha>"
git push origin --tags
```

El mensaje del tag embebe el run_id/fecha del VERIFICAR verde (ancla la Llave 1). Verificable con `git tag -v`.

**Opción 2 (descartada) — manifiesto por espejo del motor.** Crear `Entorno/release.manifest.json` + `.asc`. Más pesado y necesita un `sha256` de artefacto que el visor no produce hoy; acabaría anclando el commit, que es justo lo que la Opción 1 hace de forma nativa. *No se usa.*

> En ambos casos: clave **GPG ed25519 8FD1…0942** (la misma del motor). **No tocar el artefacto después de firmar** (invalida la firma). La firma la pones **tú en tu máquina**; la IA no maneja tu clave privada.

---

## 4. Qué se commitea y dónde

Repo **`aqyra-entorno`** (`Entorno`), rama **`main`** (commits aparte, A y B):

- Los dos golden (`publico/demo/test/columns.golden.test.ts`, `parking.golden.test.ts`) y sus `fixtures/` — ya están en disco.
- El `VERIFICAR_V3_resultado.txt` **fresco** (evidencia de Llave 1).
- Si eliges Opción 2: `release.manifest.json` + `.asc`.

Todo vía `.bat` que ejecutas tú (lo prepara el hilo Git/Firmas). **Puerta de secretos** antes del push: confirmar que `Entorno/publico/demo/.env` (clave del proxy LLM) sigue ignorado y no entra.

---

## 5. Resumen del estado

- **Llave 1:** pendiente de **re-verificar** (el resultado en disco es viejo y no cubre estos golden) → correr `VERIFICAR_V3.bat`.
- **Llave 2:** mecanismo **decidido = tag git firmado** (Opción 1). Pendiente: que el hilo Git/Firmas prepare el `.bat` con los dos `git tag -s` y que tú firmes.
- **Tras firmar:** reflejar en `PANEL_Ahora-cebo.md` §7 (mover de "cola" a "firmado") y, si procede, en `versions.lock`.

## 6. Secuencia lista para la pasada única (spec del `.bat` del hilo Git/Firmas)

Parches de typecheck **aplicados y verificados en disco** (28-jun): `diseno.ts` (union `target` + `"openings"`), `model.ts` (`DEFAULT_RISER` borrado), `diseno.ts` (`starterChips` borrado). Falta solo el VERIFICAR verde. En cuanto lo esté, ejecutar (lo envuelve el hilo Git/Firmas en `.bat`: limpieza de `index.lock`, puerta de secretos):

```bat
REM  en Entorno/  (repo aqyra-entorno, rama main)
git add publico/demo/src/diseno.ts publico/demo/src/model.ts ^
        publico/demo/test/columns.golden.test.ts publico/demo/test/parking.golden.test.ts ^
        publico/demo/fixtures
REM  (VERIFICAR_V3_resultado.txt está gitignorado → la referencia de Llave 1 va en el mensaje del tag, no en el commit)
REM  PUERTA DE SECRETOS: confirmar que publico/demo/.env NO está en el add
git commit -m "Cebo: capa de elementos (IfcColumn/Slab+huecos/Wall/Door/Window/Stair) + parking; golden 35/35 + 7/7; typecheck limpio"
git tag -s cebo-elementos-2026-06-28 -m "Cebo capa de elementos · columns.golden 35/35 · suite 144/144 · VERIFICAR 28/06 verde"
git tag -s cebo-parking-2026-06-28   -m "Cebo parking en peine · parking.golden 7/7 · VERIFICAR 28/06 verde"
git push origin main --follow-tags
git tag -v cebo-elementos-2026-06-28   &  git tag -v cebo-parking-2026-06-28   REM verificar firmas
```

Firma con la clave **GPG 8FD1…0942**. *(Si prefieres commits aparte para cada pieza, el hilo Git/Firmas divide el `add`/`commit` en dos; los dos tags pueden de todas formas apuntar al mismo commit, cada uno documentando su golden.)*

*Procedencia: Aqyra-Raiz · hilo de coordinación · paquete de firma para JM · 2026-06-28.*

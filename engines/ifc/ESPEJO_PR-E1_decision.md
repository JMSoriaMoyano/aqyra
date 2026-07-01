# PR-E1 · Retirada del espejo del engine — Nota de decisión

**Fase I · hilo 2.** Resuelve el fork de apertura del hilo (con JM) y ancla el alcance de PR-E1.
DoD-1: *modelo de fuente única elegido; alcance fijado; sin código tocado aún.* La zona firmada
`_import/` **no se reescribe**. Plan base: `engines/ifc/ESPEJO_plan-retirada.md`.

## Decisiones resueltas (JM, 2026-07-01)

| # | Fork | Decisión |
|---|---|---|
| 1 | Modelo de fuente única | **C — Piloto + contrato.** Re-home de UN solo plugin (`iso19650-openbim`, el que lleva el engine). El núcleo (`ifc_utils`/`grafo_red` en 4 plugins) va a hilo aparte (PR-E2…E5). |
| 2 | Alcance de este hilo | **Solo el espejo del engine (PR-E1).** El espejo del núcleo queda fuera. |
| 3 | Publicación del 0.10.0 | **Desde el monorepo, firmada.** `release.yml` verifica golden verde (Llave 1) + firma del tag (Llave 2, JM). El `.plugin` viejo 0.9.2 en `_import` queda frozen e intacto. |
| 4 | Consumo del engine | **Copia en build desde `engines/ifc`.** El empaquetado copia `engines/ifc/narracion-ifc/*` → `skills/narracion-a-ifc/scripts/` al construir el `.plugin`. La carpeta del skill se **genera** (gitignored, nunca commiteada). Única fuente editable = `engines/ifc`. |
| 5 | Ubicación del miembro | Nuevo `plugins/iso19650-openbim/` (nombrado en el plan base). Primer poblador de una carpeta `plugins/` de gobierno. |

## Hallazgo que corrige la premisa del INICIO-hilo (verificado en el árbol)

El INICIO-hilo asumía una **copia viva editable** del compilador dentro del plugin, a borrar.
No es así:

- En todo el monorepo, `spec_to_ifc.py`/`catalogo_ifc.py` viven en **exactamente dos** sitios:
  `engines/ifc/narracion-ifc/` (canónico) y `_import/aqyra-motor/narracion-ifc/` (procedencia
  frozen). Ninguna tercera copia editable.
- El empotramiento en `skills/narracion-a-ifc/scripts/` **solo se materializa dentro del `.plugin`
  ZIP** (artefacto de empaquetado). Confirmado: `iso19650-openbim-v0.9.2.plugin` lo lleva; el
  working-tree del plugin en `_import/aqyra-motor/iso19650-openbim/` **ya está en 0.10.0 y ya no
  lleva el compilador** (skills: bep-eir, bsdd-clasificacion, cde-audit, ifc-create, ifc-validate,
  loin-matrix).
- El `.plugin` **0.10.0 nunca se ha empaquetado** (histórico llega a 0.9.1 + el 0.9.2 suelto).
- No hay carpeta `plugins/`; `apps/` solo tiene el visor; no hay pipeline que empaquete `.plugin`
  en la zona de gobierno.

**Consecuencia:** PR-E1 no *borra* una copia, sino que **crea** el miembro buildable `plugins/
iso19650-openbim/` cuyo compilador **proviene** de `engines/ifc` por copia en build. El "espejo"
que se retira es la capacidad de que un futuro empaquetado embeba una copia propia divergente: se
sustituye por un build que deriva del canónico, verificado por guardián.

## Mapa preciso de PR-E1 (qué es engine y qué no)

El engine canónico (`engines/ifc`, corte mínimo C1, anclado por md5 en `versions.lock`) son **9
ficheros**: los 8 de `narracion-ifc/` + `scripts/lineal/generate_test_ifc_lineal.py`.

Al re-home del plugin, la **copia en build** puebla:

- `skills/narracion-a-ifc/scripts/` ← `engines/ifc/narracion-ifc/*` (el compilador) + los
  auxiliares del skill que no son corte C1 (`construir_catalogo.py`, `generar_galeria.py`) desde su
  procedencia frozen, marcados como no-engine.
- El fichero de engine de `scripts/lineal/` ← `engines/ifc/scripts/lineal/generate_test_ifc_lineal.py`.

**Fuera del engine (se quedan como propiedad del plugin en PR-E1):**

- El resto de `scripts/lineal/` (export_gis, ifc_to_model_lineal, validacion_alineacion, test_lineal):
  utillería de obra lineal, no compilador.
- `scripts/nucleo/` (`ifc_utils.py`, `grafo_red.py`): **espejo del núcleo**, explícitamente
  PR-E2…E5. No se toca en este hilo.
- `scripts/estructural/`, `scripts/mep/`: dominios del plugin, sin relación con el engine.

## Guardián de no-regresión (PR-E1)

Nuevo test en el gate que **falla si reaparece una copia del engine fuera de `engines/ifc`**:
escanea el árbol de `plugins/**` buscando `spec_to_ifc.py`/`catalogo_ifc.py` (u otros ficheros del
corte) **commiteados** (la carpeta generada en build está gitignored, así que su presencia en el
árbol de git = regresión). Se cablea por `tools/affected.py`, `justfile` (`check`) y `ci.yml`
(Paso 1), junto a `test_identidad_ifc` y `test_espejo_ifc`.

## Secuencia

1. **(hecho)** Resolver el fork → esta nota. *Sin código tocado.*
2. Crear `plugins/iso19650-openbim/` desde la base frozen 0.10.0 (leída de `_import`, sin tocarla),
   sin el compilador; `.gitignore` para la carpeta generada del skill.
3. Script de empaquetado: copia `engines/ifc` → `skills/narracion-a-ifc/scripts/`, zipa el `.plugin`
   0.10.0, pasa `verificar_empaquetado.py` (puerta reutilizada) contra el 0.9.2 como `--ref` con
   `--allow-shrink` auditado por el salto 0.9.2→0.10.0.
4. Guardián anti-reaparición en el gate.
5. `versions.lock`: `[engines.ifc] estado` (espejo del engine retirado; consumo por build desde
   plugins/) y nota en `[core] estado` (núcleo sigue pendiente). Nota de cierre + guion PR-E2…E5.
6. PR con gate verde (rama → PR → `gate` verde → merge). Tag firmado por JM para el release 0.10.0.

## Reglas heredadas

- **No** tocar `_import/` ni los tags firmados. El canónico es `engines/ifc`; la copia se retira de
  su punto de uso (el empaquetado), no se mueve ni edita en `_import`.
- Operaciones de red/git en la terminal PowerShell abierta (una instrucción por línea; `git add` en
  una sola línea; sin `&&`/`^`). Puerta de secretos antes de cada push. La firma (Llave 2) es de JM.
- Los guardianes mandan: si retirar la copia deja algo sin fuente, se conecta al canónico; no se
  re-duplica ni se afloja el guardián.

*Procedencia: Aqyra · Fase I · hilo 2 · para JM. Monorepo `main` `7a25c98`. Base: `ESPEJO_plan-retirada.md`.*

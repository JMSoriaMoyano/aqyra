# Estado inicial — Compilador narración→IFC + visor (baseline de Aqyra)

> Punto de partida real del proyecto Aqyra, heredado del hilo «compilador narración → IFC». **El visor no se parte de cero: ya existe**, y con él un compilador de lenguaje natural a IFC. Resumido de `Estructurando2.0_Narracion-IFC_alcance-y-pendiente.md` (2026-06-23).

**Entregable base:** `iso19650-openbim v0.8.2` (APTO, a instalar) — incluye la skill `narracion-a-ifc` junto a `ifc-create`, `bsdd-clasificacion`, `ifc-validate`.

---

## 1. Lo que ya existe (cubierto)

**Arquitectura en dos capas con frontera limpia:**

```
prosa → <m>.alto.json → compilar_spec.py → <m>.spec.json → spec_to_ifc.py → <m>.ifc
      → visor/pipeline.mjs → .frag + props → Visor IFC
```

- **Capa semántica** (lenguaje → intención): el agente traduce prosa a un *spec de alto nivel*.
- **Capa determinista** (intención → geometría): `compilar_spec.py` expande macros y valida; `spec_to_ifc.py` genera IFC con IfcOpenShell.

**Núcleo del compilador:** spec paramétrico canónico con contrato JSON Schema (`spec.schema.json`, todo en metros); expansor determinista (retícula de pilares, niveles); generador IFC4/IFC4X3 con geometría real.

**Primitivas con geometría realista:** pilares (rect/circular), muros con **huecos reales** (IfcOpeningElement/RelVoids + puerta/ventana con RelFills), forjados (macizo, nervado, reticular, unidireccional con bovedillas), vigas perfil I (IPE/HEB), zapatas, puertas/ventanas, rampas (rectas/tijera/peldañeadas), escaleras (meseta, giro en U, zanca).

**Catálogo bsDD:** `catalogo_ifc.py` deriva del esquema IFC4X3 las ~150 clases concretas de `IfcElement`; cada una con arquetipo geométrico, `PredefinedType`, Psets `*Common` estándar y URI del diccionario IFC de bsDD. Primitiva genérica `elementos` («pon una viga / zapata / puerta…»).

**Validación integrada (doble modo):** `validar.py` — *Informe* (ERROR/AVISO/INFO, no bloquea) y *Puerta* (`--estricto`: falla si hay ERROR duro: esquema, unidad SI, contexto geométrico, GlobalId duplicado, RelVoids/RelFills íntegros, representación no vacía).

**Empaquetado:** todo en el plugin `iso19650-openbim v0.8.2`; pasa la puerta de empaquetado (núcleo espejado intacto por md5).

## 2. Lo pendiente — Capa 2: visor de mirador → editor paramétrico

Es el **siguiente gran bloque** y, a la vez, **el sustrato de la misión 1** (pre/post): para hacer pre-proceso hay que poder definir/editar cargas y apoyos sobre lo que se ve, y que persista al IFC.

- **C — Round-trip del spec (cimiento):** enlazar modelo↔spec; cambio → regenerar → recargar en caliente preservando vista. Habilita a A y B.
- **A — Panel de propiedades editable** (depende de C).
- **B — Edición narrada en contexto** («sube los pilares a 4 m»; lo más potente, semántica más difícil).

**Decisión abierta clave:** dónde se ejecuta la regeneración — el visor es HTML offline (web-ifc) y el generador es Python/IfcOpenShell → o un **proceso local** de backend, o el **agente** como backend en Cowork. Se resuelve dentro de C. *Recomendación registrada: C + gancho mínimo demostrable, luego A, luego B.*

## 3. Mapeo a la hoja de ruta de Aqyra

| Estado narración→IFC | Versión de Aqyra (`HOJA_DE_RUTA.md`) |
|---|---|
| Visor `visor-ifc` + pipeline (mirador) | **V0/V1** — base del cebo |
| Capa 2 · C (round-trip) + edición ligera write-back | **V2** — pre-proceso (edición de cargas/apoyos persistida al IFC) |
| Capa 2 · B (edición narrada en contexto) | **V4** — copiloto NL (superficie en `publico/ui-nl/`) |
| Validación IDS/BCF, catálogo bsDD | carriles transversales OpenBIM (V1+) |

## 4. Mejoras menores pendientes (del generador)

- Encadenar `ifc-validate` para auditoría de **dominio** (continuidad MEP, alineación/georref en obra lineal).
- Más familias con geometría real: cubierta inclinada, reticular con casetones, muro multicapa.
- `PredefinedType` por defecto «típico» por clase (hoy toma el primer valor del enum).

## 5. Hazards técnicos del entorno (para quien continúe)

- **Toolchain:** IfcOpenShell 0.8.5 + jsonschema. Tras reinicio del sandbox, `/tmp` se vacía → reinstalar en `/var/tmp/pylibs` con `PYTHONPATH=/var/tmp/pylibs:/tmp/pylibs`.
- **`/tmp` es tmpfs pequeño:** usar `TMPDIR=/var/tmp/...` (pip y empaquetado fallan por *No space left*).
- **Bug IfcOpenShell:** `use-world-coords=True` da coordenadas basura en extrusiones rectangulares → verificar con verts locales + matriz. No afecta al entregable (el visor usa web-ifc, lee el STEP directo).
- **Mount:** el shell puede leer/escribir copias **truncadas** de ficheros del montaje → editar markdown/manifest **solo con herramientas de fichero**.
- **Empaquetado:** plugin read-only (copiar a /tmp + chmod); no sobrescribir el `.plugin` versionado; `description` ≤ 500 chars; **no tocar `scripts/nucleo/`** (espejo byte a byte).

## 6. Operativa inmediata

- **Reinstalar `iso19650-openbim v0.8.2`** en Cowork para que `narracion-a-ifc` quede activa en cualquier hilo.

---

*Baseline preparado por la IA · 2026-06-23 · a partir del traspaso del hilo narración→IFC, para el arranque del proyecto Aqyra.*

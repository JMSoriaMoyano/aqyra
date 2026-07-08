# Diseño · Los cortes nacen del IFC (E2.1)

> Cómo se materializa y **qué debe ratificar JM (D20–D23) antes del código**. Regla sagrada heredada
> (C1/C3/C4/C5): **añadir claves, nunca cambiar semántica**. Un fallo se corrige en el código, jamás
> aflojando una golden. Gobierna **N-06** (D-028): agrupaciones nativas del IFC + frontera 50/50 +
> criterio como *fallback*, ya ratificada a nivel de negocio.

## 1 · El modelo mental (de N-06)

El motor de cortes reconoce **tres mecanismos de agrupación nativos** del IFC, más el criterio como
*fallback* degradado:

| Eje de corte | Mecanismo IFC | Atribución | `fuente` |
|---|---|---|---|
| `espacial` | Árbol `IfcProject→IfcSite→IfcFacility/IfcBuilding→IfcFacilityPart/IfcBuildingStorey→IfcSpace` (4.3 incl. `IfcBridge`/`IfcRoad`) | **Directa** (`IfcRelContainedInSpatialStructure`: 1 elemento → 1 nodo) | `ifc` |
| `funcional` (elementos) | `IfcSystem` (agrupa elementos, típ. MEP) | **Directa** (el sistema agrupa el elemento) | `ifc` |
| `funcional` (espacios) | `IfcZone`→`IfcSpace`, atribución espacio→elemento vía `IfcRelSpaceBoundary` | **Indirecta** (reparto de frontera, §3) | `ifc` |
| `funcional` (degradado) | tabla `reglas_sistema` del criterio (clase/uso → sistema grueso) | **Directa** (etiqueta por clase) | `criterio` |
| `uniclass` / `gubim` | Código de clasificación por objeto (ya lo lee el parser) | **Directa** (etiqueta en el objeto) | `ifc` |

`IfcZone` e `IfcSystem` son especializaciones de `IfcGroup` (no jerárquicas; un objeto puede estar en
varios grupos). El parser las trata de forma uniforme: lee el grupo declarado y agrupa por él.

## 2 · Decisión D20 · Forma de `cortes{}` — **lista de pertenencias**, no string

**Propuesta (a ratificar).** Cada objeto medido gana `cortes` (opcional). Cada eje es una **lista de
pertenencias**:

```jsonc
"cortes": {                                  // NUEVO, aditivo, opcional
  "espacial":  [ { "grupo": "Edificio-A/Planta-01", "fraccion": 1.0, "fuente": "ifc" } ],
  "funcional": [ { "grupo": "Sys/Clima/AireP1",     "fraccion": 1.0, "fuente": "ifc" } ],
  "uniclass":  [ { "grupo": "Ss_25_11_16",          "fraccion": 1.0, "fuente": "ifc" } ],
  "gubim":     [ { "grupo": "1.2.3",                "fraccion": 1.0, "fuente": "ifc" } ]
}
```

- `grupo`: etiqueta estable del grupo (ruta espacial, id de sistema/zona, o código de clasificación).
- `fraccion`: número en `(0, 1]` (default `1.0`); **suma 1.0 por eje** cuando el objeto está atribuido
  (invariante que E2.2 usa para `Σ == total`). Habilita el **reparto 50/50** (§3) y la **pertenencia
  múltiple** (un objeto en varios `IfcSystem`/`IfcZone`).
- `fuente`: **enum `{ifc, criterio}`** (D-028: traza si el corte nace del modelo o de una convención).

**Por qué lista y no string (como esbozaba el BRIEF §2.2).** Un string único no puede representar (i) el
reparto 50/50 ratificado (N-06) de un elemento de frontera compartido, ni (ii) la pertenencia de un
objeto a varios grupos (un muro en dos sistemas). El BRIEF es anterior a N-06; N-06 fija que la
atribución fraccionaria vive en el modelo → la lista con `fraccion` es la forma mínima que la soporta.
Ausencia de un eje = sin agrupación conocida → clave ausente, nunca error (forward-open).

**Alternativa (si JM prefiere):** eje = string simple + un mapa `fracciones` aparte solo para `funcional`.
Se descarta por asimetría (dos formas para el mismo concepto) y por complicar el invariante de E2.2.

## 3 · Decisión D21 · Reparto de frontera — **50/50 fijo, materializado en el parser**

N-06 ya ratificó (opción b) el **reparto 50/50** del elemento de frontera compartido; esta decisión
**no lo reabre**, ancla su **materialización** a nivel C5:

- El 50/50 se resuelve **al construir el modelo neutro** (en el parser), **no** en `proyectar` (N-06,
  «el corte sigue siendo consulta»). El objeto lleva ya `funcional:[{grupo:ZonaA,fraccion:0.5,…},
  {grupo:ZonaB,fraccion:0.5,…}]`.
- **Regla de atribución espacio→elemento** (vía `IfcRelSpaceBoundary`): para un elemento que delimita
  `N` espacios distintos, `fraccion = 1/N` a cada espacio, **agregada por zona**. Un tabique entre dos
  aulas (2 espacios) → 0,5/0,5 (= el «50/50» de N-06). Un elemento en la frontera de un único espacio
  → 1,0 a su espacio/zona. Dos espacios de la **misma** zona → 1,0 a esa zona.
- **Refinamiento (c)** «por superficie de frontera» queda como **gancho forward** (residual N-06), sin
  implementar en v0: el objetivo es valoración *rápida*, y 50/50 es barato, determinista y golden-able.

**Precondición de calidad del modelo (honesta).** El corte por zona **solo existe si el modelo trae
espacios + zonas + fronteras**; su exigencia es competencia del **QA/IDS de C4** aguas arriba. Sin
ellos, el parser degrada `funcional` al criterio (§4), no inventa zonas.

## 4 · Decisión D22 · *Fallback* funcional — **`criterio/AQ/v2` nuevo** (no re-anclar v1)

Cuando el modelo **no** declara agrupación funcional nativa (ni `IfcSystem`, ni `IfcZone`/espacios), el
eje `funcional` se deriva de una tabla **`reglas_sistema`** (clase/uso → sistema grueso) con
`fuente = criterio` (N-06: `IfcWall` exterior → «Envolvente»; `IfcSlab`/`IfcColumn` → «Estructura»…).

`reglas_sistema` **no existe** hoy y el pack `criterio/AQ/v1` está **anclado por hash** (referenciado
por `GOL-PRE-01/02` y verificado por `run_case_c5`).

**Propuesta (a ratificar): materializarlo como `criterio/AQ/v2` = `v1` + `reglas_sistema`.** Deja `v1`
y sus goldens **intactos** (mismo precedente que la inyección de `Qto`, D_modelo: no se edita lo
anclado, se crea nuevo con su propia ancla). El mapeo clase→partida de v2 es **idéntico** al de v1
(se mide igual); v2 solo añade la tabla de *fallback*. Las goldens de cortes (E2.2) usan v2; `GOL-PRE-01`
sigue en v1.

- **Emparejamiento POR JERARQUÍA (ratificado por JM 2026-07-08):** una regla casa si su `clase` es la
  clase del elemento **o cualquiera de sus SUPERTIPOS** IFC (el parser pasa la ascendencia de tipos).
  Así **~10 familias por dominio** (Estructura, Envolvente, Particiones, Instalaciones, Carpintería,
  Acabados, Cimentación, Urbanización, Mobiliario, + catch-all «Elementos constructivos») cubren el
  **centenar de clases** del estándar sin enumerarlas (una sola regla `IfcDistributionElement` cubre
  toda la MEP). Orden = precedencia (específico→general); `default` = «Sin clasificar». El *fallback*
  solo aplica a objetos **medidos** (los que llevan partida) → su universo real es lo que el criterio mide.
- **Taxonomía del sistema grueso:** anclar a la tabla *Systems* de Uniclass (`Ss`) en vez de inventar
  taxonomía propia (residual N-06, recomendado).
- **Alternativas (si JM prefiere):** (a) **re-anclar `v1`** in situ (editar `criterio.json`, re-hashear
  en `versions.lock`) — más simple pero toca lo anclado; (c) **diferir el *fallback*** a un change
  posterior y que E2.1 solo lea cortes nativos — no cumple el criterio de aceptación de E2.1
  («sin agrupación, `funcional` por criterio con `fuente=criterio`»).

## 5 · Decisión D23 · Fixtures y golden — **nuevas fixtures + caso NUEVO (E2.2)**

- Las fixtures de `GOL-PRE-01` (`ARQ.ifc`/`EST.ifc`, md5 `0b998513…`/`0d7e7f20…`) **no traen**
  `IfcZone`/`IfcSystem`/fronteras y son **intocables**. Los cortes usan **fixtures nuevas o aumentadas**
  con árbol 4.3 + `IfcSystem` + `IfcZone`+espacios+`IfcRelSpaceBoundary`, con **md5 propios** (patrón de
  la inyección de `Qto`).
- E2.1 entrega un **test de parser** sobre esas fixtures: verifica que se producen `cortes` completos,
  que sin agrupación `funcional` sale por criterio (`fuente=criterio`), y el **50/50 en un tabique
  compartido** entre dos zonas.
- La **golden de vista** (invariante `Σ proyección == Σ estado_mediciones`, con las 5 vistas) es un
  **caso NUEVO `GOL-PRE-03`** (patrón `GOL-PRE-02`), y se entrega en **E2.2**, nunca editando
  `GOL-PRE-01`.

## 6 · Verificación (dos llaves)

- **Sandbox (path puro):** el reparto y la forma de `cortes` se pueden probar en el sandbox sobre un
  modelo neutro sintético (sin IFC) — invariante `Σ fraccion == 1` por eje atribuido.
- **Local (conda `mcp-bim`):** el parser sobre las fixtures IFC (con `ifcopenshell`) corre en la máquina
  de JM antes de CI (el sandbox no tiene `ifcopenshell`).
- **Llave 1:** gate verde en CI (`run_case_c5` deja `GOL-PRE-01/02`/`GOL-DOC-01` byte-idénticas; el test
  de parser de cortes pasa). **Llave 2:** merge/firma de JM. **Sin release.**

## 7 · Qué desbloquea

- **E2.2** — `proyectar(presupuesto, eje, corte)`: un `group-by` puro sobre los `cortes` que E2.1 dejó
  en el modelo + `valores[eje]` (o el coste canónico), con `GOL-PRE-03` (5 vistas) y el invariante Σ.
- **E6** (dashboard): la `fuente` viaja al `proyectar` para mostrar si el corte nace del modelo o de una
  convención (residual N-06).

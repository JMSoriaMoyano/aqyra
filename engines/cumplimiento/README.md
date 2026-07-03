# engines/cumplimiento — engine C3 (cumplimiento normativo multi-código)

`verificar(maestro, uso, localizacion, pack) → veredicto` **por exigencia + resumen + veredicto
global**. Hace VIVO el contrato C3 (`packages/contracts/C3-cumplimiento/`): el 3.2 dejó el
contrato anclado (2 esquemas + pack CTE/2019 + golden `GOL-CTE-01` con checklist firmado como
oráculo); este engine DA el veredicto y el runner de la golden **antepone** su recompute contra el
MISMO `expected` (la costura que cerró C1 en Fase I y C4 en Fase II·h2).

## Idea central (D8): el código es un PACK anclado, no un `if`

El engine mantiene una **librería FINITA de evaluadores deterministas** (`evaluadores.py`) y el
**pack declara**, por exigencia, cuál usar (`evaluador` + `parametros`). Cambiar de año / mercado /
municipio = cambiar de **pack** (nuevas exigencias); un método genuinamente nuevo = un evaluador
nuevo (honesto, raro). No hay `if id == ...` cableado.

Evaluadores de v0.1 (los que ejercita `GOL-CTE-01`):

| evaluador | mira | resultado |
|---|---|---|
| `presencia-tipo-ifc` | ≥1 entidad de una clase (opcional `PredefinedType`) | cumple / no-cumple |
| `presencia-propiedad-pset` | una propiedad (p. ej. `FireRating`) en el Pset de cada elemento de unas clases | cumple / no-cumple + `por_modelo` |
| `aplica-solo-uso` | si el `uso` declarado rige la exigencia | no-aplica (o su `resultado_si_aplica`) |
| `requiere-motor` | nada — declara la frontera | no-verificable + `motivo` |

## Frontera (D7): abre el derivado, NO federa

El engine **abre el IFC derivado** (la vista del Maestro que produce C4, D26/D30) y usa la
**procedencia del manifiesto** (fuente de verdad, D1) para atribuir `por_modelo` — el derivado funde
los modelos preservando GUIDs (D28), y el manifiesto declara de qué modelo vino cada uno. **No**
federa ni re-ejecuta `services/federacion` (eso es C4); **no** adivina uso ni localización (se
DECLARAN, ADR). La regeneración del Maestro para la golden la hace el **runner** (costura), no el
engine.

## Estructura

```
src/aqyra_cumplimiento/
  cumplimiento.py   verificar() — orquesta: pack → evaluar cada exigencia → resumen + veredicto (D4)
  evaluadores.py    registro FINITO de evaluadores deterministas (D8)
  modelo.py         abre el derivado + reconstruye GUID→modelo desde el manifiesto (D7)
  cli.py            aqyra-cumplimiento (inspección manual / C7)
tests/              unitarios (IFC sintéticos, sin service); el checklist real lo cierra el runner
```

## Uso (CLI)

```
aqyra-cumplimiento --manifiesto M.json --base-dir DIR \
  --pack data/packs/normativa/CTE/2019 --derivado federado.ifc \
  --uso "Residencial Vivienda" --pais España --municipio Jaén --zona-climatica-he C4
```

Decisiones de contrato: `packages/contracts/C3-cumplimiento/DECISIONES.md` (D1–D5 contract-first,
D6–D10 este engine). Versión anclada en `versions.lock [contracts.C3]`. Release firmado:
`cumplimiento-v0.1.0` (Llave 2).

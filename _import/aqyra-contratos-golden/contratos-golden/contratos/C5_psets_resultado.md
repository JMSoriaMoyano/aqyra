# C5 v0 — Psets de resultado `Pset_AqyraStructuralResult_*`

**Anexo del contrato C5** · zona protegida · v0.1.0 DRAFT · 2026-06-26 · pendiente de firma de JM

> Define **cómo se escriben los resultados del motor-fem (O1–O5) de vuelta al IFC**, como Psets Aqyra
> *diff-able*. Extiende la convención de entrada `Pset_AqyraStructural_*` (D-011) y el mecanismo de
> *append* diff-able (`appendStructuralPset`, D-013): líneas STEP al final del DATA, sin re-serializar,
> idempotente y reversible (`stripStructuralPset`). Es el espejo en IFC del `C5_resultados.schema.json`.

## 1. Principios

1. **Espejo del schema.** Cada Pset de resultado corresponde a una colección del `C5_resultados.schema.json`.
   El JSON es la representación canónica; el Pset es su persistencia en el IFC. Deben coincidir 1:1.
2. **Familia separada de la entrada.** La entrada (apoyos/cargas/casos/combinaciones) vive en
   `Pset_AqyraStructural` (`proposal`). El resultado vive en `Pset_AqyraStructuralResult_*` para no
   mezclar lo autorado con lo calculado.
3. **Estado explícito.** Todo resultado nace `proposal`; pasa a `verified` solo con golden verde + QA
   limpio + **firma de JM** (dos llaves). El estado viaja en `Pset_AqyraStructuralResult_Meta`.
4. **Serialización diff-able.** Valores como `IfcPropertySingleValue` con texto `clave=valor;clave=valor;…`
   (mismo patrón que la entrada), adjuntos al elemento (`IfcElement`/miembro analítico) o al modelo
   (`IfcProject`/grupo) según el ámbito. Idempotente y reversible.
5. **Unidades SI** declaradas (m, N, Pa, kg, Hz); se heredan de `Pset_AqyraStructural`.

## 2. Catálogo de Psets de resultado

| Pset | Ámbito (a qué se adjunta) | Campos (clave=valor) | Schema (C5_resultados) |
|---|---|---|---|
| `Pset_AqyraStructuralResult_Meta` | modelo (`IfcProject`) | `motor_version; build_interno; estado; oraculo; normas; run_id` | `meta` |
| `Pset_AqyraStructuralResult_Displacement` | nodo / elemento | `combinacion; ux; uy; uz; rx; ry; rz` | `desplazamientos` |
| `Pset_AqyraStructuralResult_Reaction` | nodo de apoyo | `combinacion; Fx; Fy; Fz; Mx; My; Mz` | `reacciones` |
| `Pset_AqyraStructuralResult_MemberForce` | barra (`IfcMember`/`IfcBeam`/`IfcColumn`) | `combinacion; x_rel; N; Vy; Vz; Mt; My; Mz; envolvente` | `esfuerzos_barra` |
| `Pset_AqyraStructuralResult_ShellForce` | lámina (`IfcSlab`/`IfcWall`/`IfcPlate`) | `combinacion; punto; mx; my; mxy; nx; ny; nxy; vx; vy` | `esfuerzos_lamina` |
| `Pset_AqyraStructuralResult_Modal` | modelo (`IfcProject`) | `modo; f; T; masa_x; masa_y; masa_z` | `modal` |
| `Pset_AqyraStructuralResult_Utilization` | elemento | `comprobacion; norma; Ed; Rd; u; veredicto` | `aprovechamientos` |

> **Multivalor (varias combinaciones / varios modos):** se permite repetir la propiedad con sufijo de
> índice (`...MemberForce` con `c1=…`, `c2=…`) o adjuntar varias instancias del Pset por combinación,
> según convenga al mecanismo de *append*. La envolvente se marca `envolvente=true`.

## 3. Ejemplo (serialización diff-able)

Aprovechamiento del montante DEC-B4 (barra `#113`), escrito como anejo al final del DATA:

```
/* Pset_AqyraStructuralResult_Utilization @ #113 */
comprobacion=pandeo; norma=EC3 6.3.1; Ed=392e3; Rd=632e3; u=0.62; veredicto=CUMPLE
/* Pset_AqyraStructuralResult_Meta @ IfcProject */
motor_version=0.1.0; estado=proposal; oraculo=pynite; run_id=N1.1-decopak-2026-06-26
```

(En IFC real cada línea es un `IfcPropertySingleValue` con `NominalValue=IfcText('clave=valor;…')`
agrupado en un `IfcPropertySet` de nombre `Pset_AqyraStructuralResult_*` ligado por `IfcRelDefinesByProperties`.)

## 4. Puntos abiertos (a confirmar con JM / iso19650-openbim)

- ¿Emisión **nativa** `IfcStructuralLoad*` / `IfcStructuralResult*` (diferida a ≈V3, D-011) o solo Pset Aqyra en v0?
- Sufijo exacto para multivalor (índice vs instancia repetida) — fijar uno para que el diff sea estable.
- Mapeo de ámbito cuando el resultado es por nodo y el IFC no tiene nodo analítico explícito (adjuntar al elemento contenedor).

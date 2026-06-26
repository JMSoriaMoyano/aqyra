# Caso de prueba — comparación de versiones (v1.1)

Dos versiones controladas de un mismo modelo (derivadas de `clasif-demo`: 4 pilares, 4 zapatas,
4 vigas, 1 forjado). Sirven para validar el diff de la v1.1 de forma **determinista**.

- **cmp-A** (`models/cmp-A.{ifc,frag,props.json}`) — versión base, **sin Viga_3**.
- **cmp-B** (`models/cmp-B.{ifc,frag,props.json}`) — **sin Viga_4**, con **Pilar_2 desplazado +2 m en X**
  y el **Pset del forjado modificado**.

Ambas comparten `GlobalId` para los elementos comunes (es el supuesto "dos versiones del mismo
modelo"). 28 ítems / 12 con geometría cada una.

## Verdad de terreno del diff A → B (verificado en Node)

| Estado | Elemento | GlobalId | Detalle |
|--------|----------|----------|---------|
| **Nuevo** (en B, no en A) | Viga_3 | `1f_5YTfGjBdgzh32$3k$QP` | viga presente solo en B |
| **Eliminado** (en A, no en B) | Viga_4 | `1pbVB1idHDGQ5Db8F5_NVy` | viga presente solo en A |
| **Modificado** (datos) | Forjado_cubierta (IfcSlab) | `0NOtbTXaHB1vP4gniGSf4w` | `Pset_Estructurando_Forjado`: `Canto_m` 0.25 → 0.30 ; `Material` 'C30/37' → 'C35/45' |
| **Desplazado** (geometría) | Pilar_2 (IfcColumn) | `0A7IMBbTD91PrLqjhr$r0e` | origen de placement (6,0,0) → (8,0,0); +2 m en X. **No** se ve en `props.json` (mismo dato); se detecta por `getBoxes`/centroide en el `.frag` |
| **Sin cambios** | resto (Pilar_1/3/4, Zapata_1-4, Viga_1/2, forjado salvo Pset, proyecto/sitio/edificio/plantas) | — | idénticos |

## Cómo se generaron (reproducible)

Cirugía de texto sobre `clasif-demo.ifc` (sin IfcOpenShell) + conversión con `pipeline.mjs`:
- Eliminar una viga = borrar su línea `IFCBEAM` y depurar su `#id` de las listas
  `IFCRELCONTAINEDINSPATIALSTRUCTURE` y `IFCRELASSOCIATESCLASSIFICATION` (la geometría huérfana
  queda, es IFC válido y no se renderiza).
- Desplazar = editar el `IFCCARTESIANPOINT` del placement.
- Modificar Pset = editar el `NominalValue` del `IFCPROPERTYSINGLEVALUE`.
- `node pipeline.mjs models/cmp-X.ifc models cmp-X` → `.frag` + `.props.json`.

> Nota: están en el manifest con `"load": false` (no se cargan al arrancar). Para la v1.1 se
> cargan las dos y se comparan A (base) vs B (nueva).

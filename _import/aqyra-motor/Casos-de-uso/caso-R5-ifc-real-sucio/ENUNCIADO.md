# Caso R5 — IFC físico "real-sucio" de un exportador concreto (cierre de INC-07)

**Quinto y último peldaño de la Dirección 2.** Endurecer el puente físico→analítico
ante geometría real: ejes no centrados/offsets, barras no conectadas, huecos, troceo
en cruces T/X con offset, nomenclatura de exportador y unidades no-metro.

## Punto de partida
Plugin `motor-calculo-estructural` v0.19.0 (acumulativo: `sismico/`, `pretensado/`,
`clasificador.py`/`run_all_edificio.py` y `puente_analitico/` con R1+R2+R3+R4).

## La brecha
R1–R4 derivaron de IFC físicos **limpios** (ejes baricéntricos centrados que se cortan
en los extremos, fusión por tolerancia trivial de 1 mm, nomenclatura controlada, sin
elementos sobrantes). Un entregable BIM **real** es "sucio": ejes físicos ≠ ejes
analíticos (offset por *cardinal point*), barras que no se cortan en el nudo (huecos y
solapes), elementos no estructurales/no conectados, nomenclatura de exportador y
unidades no-metro. R5 endurece el puente para recuperar el mismo modelo analítico que
un modelo limpio equivalente y calcularlo sin sesgo.

## El modelo
`caso-R5.ifc` (IFC4) reproduce el pórtico del caso 1 / R1 (2 `IfcColumn` HEB 200 +
1 `IfcBeam` IPE 330, S275, luz 6 m, altura 4 m, G=12 / Q=10 kN/m) **inyectando** de
forma parametrizada: unidades en **milímetro**; ejes con **CardinalPoint** ≠ 5 (1/3/8,
ecc ~141/141/165 mm); **solape** de 40 mm en cabeza de pilar y **hueco** de 30 mm en
cada extremo del dintel; un `IfcRailing`, un `IfcBuildingElementProxy` y un `IfcBeam`
suelto (a filtrar); nomenclatura de exportador (nombres GUID-like, `PredefinedType`
variados, perfiles "HE 200 B" / "IPE330" alias, placements anidados).

## Trabajo del hilo
1. Generar `caso-R5.ifc` + `validacion-IFC.txt` (suciedades inyectadas, parametrizadas).
2. Endurecer `puente_analitico/puente.py`: (a) recuperar el eje analítico por
   CardinalPoint/usage y guardar la excentricidad; (b) grafo de nudos con snap
   parametrizable + bridging + troceo T/X con offset (proyección); (c) filtrar
   no-estructurales/no-conectados; (d) alias de perfiles; (e) factor de unidades.
   **R1–R4 intactos** (tolerancia por defecto + sin offset → comportamiento idéntico).
3. Reejecutar `run_all_real.py` sobre el IFC real-sucio (motor SIN CAMBIOS).
4. Validar: reproduce R1 (93,60 kN/apoyo; HEB 200 ~32 %; IPE 330 44,6 %; validación
   cruzada PyNite vs anaStruct CONFORME; equilibrios ~0 %). Documentar excentricidad
   recuperada por barra, tolerancia de snap, elementos filtrados, cruces troceados.
5. Entregables: `modelo_neutro.json` (con excentricidades + registro de limpieza),
   `clasificacion.json`, `verificacion.json`, memoria Word (sección de robustez del
   puente) y diagramas.
6. Registrar lección + métricas, cerrar INC-07 y la serie R / Dirección 2, subir el
   plugin al siguiente minor y reempaquetar el `.plugin` acumulativo.

## Criterios de aceptación
- El modelo neutro tras la limpieza coincide con el del caso limpio (4 nudos / 3 barras,
  salvo las excentricidades documentadas).
- Reacción 93,60 kN/apoyo (exacta); HEB 200 ~32 %; IPE 330 44,6 %; cruzada CONFORME.
- R1–R4 idénticos en IFC limpio (regresión).
- Resultado de predimensionado, a revisar y firmar por técnico competente.

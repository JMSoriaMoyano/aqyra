# caso-PUE-05 — variante IFC-driven (lector estructural, PT 7.3.1)

Misma pila que el caso paramétrico (H = 8 m, 1,5 × 1,5 m HA-30, apoyo elastomérico,
zapata 6 × 6 m), pero **el cálculo arranca de un IFC**, no de `entrada_caso.json`
tecleado. Sirve de **plantilla de documentación** para los casos IFC-driven
PUE-07…PUE-16. **Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo (IFC-driven)

```
caso-PUE-05.ifc  (IFC4X3, geometría extruida real + Psets no geométricos)
   → ifc_to_model_estructural.py  (parser C1: clasifica, extrae sección de la
       geometría real, resuelve asociaciones pila↔zapata y pila↔apoyo)
   → desde_ifc.py  (adaptador de puentes: modelo neutro → entrada_caso)
   → run_all_pila.py  (idealización → motor-fem C5 → IAP-11 → EC2/EC7)
   → resultado + mapping de write-back
   → writeback  → caso-PUE-05-resultados.ifc  (Pset_Estructurando_ResultadoPuente)
```

## Qué se lee de la geometría y qué de los Psets

- **De la geometría extruida real** (decisión PT 7.3.1): altura de pila (longitud de
  extrusión del `IfcColumn`), sección y propiedades mecánicas A, Iy, Iz, J (del perfil
  rectangular del fuste), dimensiones de la zapata (B, Lf, canto del `IfcFooting`) y del
  aparato de apoyo (a, b, Te del `IfcBearing`), y las posiciones que resuelven las
  asociaciones por proximidad.
- **De `Pset_Estructurando_*`** (datos NO geométricos): resistencias del material
  (fck, E, ν), rigideces del suelo (kx, kz, kry), rigideces/capas del apoyo
  (t_capa, n_capas), reacciones del tablero (cargas) y parámetros de comprobación
  (d, As, β, q_adm, μ).

## Round-trip (validación del lector)

El `entrada_caso` reconstruido por el lector (`entrada_caso_desde_ifc.json`) reproduce
el del caso paramétrico (`entrada_caso.json`) con una única diferencia: **J = 0,713 m⁴**
(derivado de la geometría real del rectángulo) frente a 0,71 abstracto del paramétrico
(**+0,4 %**, gobierna torsión, efecto despreciable en este caso).

| Magnitud | Paramétrico | IFC-driven | Dif. relativa |
|---|---|---|---|
| Aprovechamiento máx | 0,784761 | 0,784761 | **3,6 × 10⁻⁷** |
| Veredicto | CUMPLE | CUMPLE | — |
| f₁ | 4,51 Hz | 4,51 Hz | — |
| Cimentación (EC7) | zapata / CUMPLE | zapata / CUMPLE | — |

Dentro de la tolerancia objetivo (geometría 1 × 10⁻⁶; aprovechamientos 1 × 10⁻³).

## Ejecución

```
PYTHONPATH=$PYLIBS:$ISO/scripts/estructural:$ISO/scripts/nucleo:$ISO/scripts/lineal:\
$MOTORFEM/scripts:$PUENTES/scripts:$PUENTES/scripts/idealizacion:... \
python3 puentes/scripts/run_all_pila.py --ifc caso-PUE-05.ifc resultado_pila_desde_ifc.json
```

## Archivos (variante IFC-driven)

- `caso-PUE-05.ifc` — IFC4X3 de entrada (geometría + Psets).
- `entrada_caso_desde_ifc.json` — entrada reconstruida por el lector.
- `resultado_pila_desde_ifc.json` — resultado e2e desde el IFC.
- `mapping_resultado_ifc.json` — mapping de write-back.
- `caso-PUE-05-resultados.ifc` — IFC con `Pset_Estructurando_ResultadoPuente` escrito.

> Los ficheros del caso paramétrico (`entrada_caso.json`, `resultado_pila.json`,
> `memoria-pila-PUE05.md`, …) se conservan como referencia del round-trip.

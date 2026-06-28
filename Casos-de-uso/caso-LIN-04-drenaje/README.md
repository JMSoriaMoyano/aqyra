# caso-LIN-04-drenaje — drenaje superficial y transversal 5.2-IC

Caso e2e de la disciplina **`obras-lineales`** (PT 6.1, Ola 6), vertical **drenaje**.
Sobre el mismo eje (`caso-LIN-01`), a partir de la **hidrología** (caudales de cálculo
por el método racional modificado de la **Norma 5.2-IC**) comprueba la **capacidad de
una cuneta** (drenaje superficial) y de una **ODT** (drenaje transversal) y **rellena el
gancho `drenaje`** del modelo neutro lineal (clave nueva; el PT 5.1 lo dejaba inexistente).

Es el análogo, para el agua de lluvia, de lo que trazado (3.1-IC) y firmes (6.1-IC)
hicieron con la geometría y el firme. **Cálculo local por elemento (Manning de sección
simple), sin grafo de red** — las redes de colectores/abastecimiento son el PT 6.2.

## Cadena de extremo a extremo

```
modelo_neutro_lineal.json  +  datos_drenaje.json (cuencas + cunetas + ODT)
   -> obras-lineales/scripts/drenaje/run_all_drenaje.py  --tr-cuneta 25 --tr-odt 100
   -> hidrología (caudal racional 5.2-IC por cuenca)
   -> cuneta.py (Manning) + odt.py (control entrada/salida)
   -> RELLENA  drenaje  ->  modelo_neutro_lineal_drenaje.json
   -> write-back Pset al IFC (iso19650-openbim:ifc-create) -> eje-resultado.ifc
   -> export GIS de la planta -> eje-drenaje.geojson
```

```bash
python3 obras-lineales/scripts/drenaje/run_all_drenaje.py \
        modelo_neutro_lineal.json . --datos datos_drenaje.json --tr-cuneta 25 --tr-odt 100
```

## Resultado

**Hidrología (método racional modificado 5.2-IC):**

- Cuenca **C-plataforma** (plataforma + márgenes, A=0,0096 km², L=400 m, J=2 %,
  Pd=80 mm, Po=1 mm impermeable, **T=25**): tc=0,31 h, I=55,0 mm/h, C=0,98 →
  **Q ≈ 0,147 m³/s**.
- Cuenca **C-vertiente** (cuenca natural, A=0,85 km², L=1,6 km, J=3,5 %, Pd=95 mm,
  Po=18 mm, **T=100**): tc=0,81 h, I=44,7 mm/h, C=0,46 → **Q ≈ 5,07 m³/s**.

**Drenaje superficial — cuneta `CUN-MD`** (triangular 1V:3H, h=0,30 m, hormigón,
J=2 %): capacidad útil (resguardo 0,05 m) **0,427 m³/s ≥ Q 0,147**; calado normal
0,16 m; velocidad 1,8 m/s en rango → **CUMPLE**.

**Drenaje transversal — ODT `ODT-1`** (tubo circular Ø1,80 m, hormigón, J=1,5 %):
capacidad **7,59 m³/s** (gobierna el **control de entrada**) **≥ Q vertiente 5,07**;
dimensión 1,80 m ≥ mínima; velocidad 3,4 m/s en rango → **CUMPLE**.

- **Gancho `drenaje` relleno** en `modelo_neutro_lineal_drenaje.json`
  (`cuencas`/`cunetas`/`odt`). `firme`/`secciones_tipo`/`terreno` quedan como estaban
  (solo se **añaden** claves; modelo hermano retrocompatible, C1 §4bis).

## Extras (no bloqueantes)

- **Write-back al IFC** (`eje-resultado.ifc`): `Pset_Estructurando_ResultadoLineal` en el
  `IfcAlignment` con el resumen de drenaje (veredicto, nº cunetas/ODT, Q máx). Re-parseado
  y revalidado **CUMPLE** (continuidad 0,0001 m, georref EPSG:25830 intacta) — el
  enriquecimiento no rompe el modelo. Mapping en `mapping_resultado_lineal.json`.
- **GIS** (`eje-drenaje.geojson`): planta del eje (81 vértices) en EPSG:25830, puente a
  cartografía/cuencas.

## Notas

- La **lectura del IFC y la cuenca georreferenciada** son de `iso19650-openbim`; aquí
  vive la **hidrología (CN-3)** y el **dimensionado/comprobación de cunetas y ODT (5.2-IC)**.
  El **dato del GIS/Pset prevalece** sobre los valores por defecto.
- **Sensibilidad:** si la ODT fuese Ø1,00 m, fallaría por dimensión mínima
  (conservación/limpieza) aunque tuviera capacidad; si la cuneta recibiese un caudal
  ~5 m³/s desbordaría. El plugin **no rediseña**: reporta CUMPLE/NO CUMPLE + el elemento
  gobernante.
- Predimensionado/asistencia; NDP **[confirmar AN]** (Pd/I1Id/Po regionales del mapa de
  máximas lluvias diarias, periodos de retorno, n de Manning, velocidades admisibles,
  dimensión mínima de ODT). Revisar y firmar por técnico competente (ICCP).

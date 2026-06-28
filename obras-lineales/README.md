# obras-lineales — disciplina de obra lineal (carreteras)

Plugin de **disciplina vertical** del ecosistema *Estructurando*. Monta la disciplina
de **obra lineal** sobre el **soporte georreferenciado** que abrio el PT 5.1
(`iso19650-openbim` v0.5.0): consume el **modelo neutro lineal** (IFC 4.3 `IfcAlignment`
+ georreferencia, referenciado por **PK**) y aporta la **normativa** (3.1-IC, 6.1-IC) y
la **orquestacion** (agente + subagentes). Es el analogo lineal de lo que `instalaciones`
hizo sobre el modelo neutro de red MEP.

> **Trazado, firmes y drenaje son geometria + normativa: NO hay FEM ni grafo de red**
> (la alineacion es referenciacion lineal por PK, curva 1D; el drenaje 5.2-IC es
> hidrologia + cunetas/ODT por Manning de **seccion simple**, calculo **local por
> elemento**). El **SANEAMIENTO** (PT 6.2, Ola 6) **SI cruza la frontera de red**:
> colectores en **lamina libre** resueltos por **Manning sobre el grafo del nucleo**
> (espejado byte a byte); nace el **solver de Manning de red** y se consume el **IFC MEP
> de saneamiento**. El **ABASTECIMIENTO a presion** (PT 6.3,
> Ola 6, **cierra la ola**) tambien **cruza la frontera de red**: distribucion **a presion**
> resuelta por **Darcy-Weisbach sobre el grafo** (solver **copiado byte a byte** de
> `instalaciones`), con fuente = **deposito por cota** o **bombeo**; se consume el **IFC MEP
> de abastecimiento** (WATERSUPPLY).

## Arquitectura

```
obras-lineales/
├── .claude-plugin/plugin.json
├── agents/
│   ├── ingeniero-de-obra-lineal.md   # clasifica -> enruta -> orquesta -> verifica -> memoria
│   ├── proyectista-de-trazado.md     # subagente 3.1-IC
│   ├── proyectista-de-firmes.md      # subagente 6.1-IC
│   ├── proyectista-de-drenaje.md       # subagente 5.2-IC
│   ├── proyectista-de-saneamiento.md   # subagente EN 752 (lamina libre, red)
│   └── proyectista-de-abastecimiento.md# subagente EN 805 (presion, red)
├── scripts/
│   ├── trazado/   parametros_3_1_IC · comprobacion_trazado · verificacion_trazado · run_all_trazado · test_trazado
│   ├── firmes/    bases_firme · catalogo_6_1_IC · seleccion_firme · verificacion_firme · run_all_firme · test_firme
│   ├── drenaje/   hidrologia · cuneta · odt · verificacion_drenaje · run_all_drenaje · test_drenaje
│   ├── red/       SANEAMIENTO: bases_saneamiento · solver_lamina_libre · verificacion_red_lineal · run_all_obras_hidraulicas · resultado_red_lineal · test_obras_hidraulicas
│   │               ABASTECIMIENTO: bases_abastecimiento · solver_presion (copia de instalaciones) · verificacion_red_presion · run_all_abastecimiento · resultado_red_presion · test_abastecimiento
│   └── nucleo/    grafo_red · ifc_utils · test_grafo_red   (ESPEJO byte a byte del motor)
│   └── comun/     resultado_ifc_lineal (semantica del Pset de resultado para el write-back)
└── skills/criterios-memoria/SKILL.md  # C2/C3
```

## Frontera (contratos C1/CN-3)

- **C1 — lectura/coherencia IFC: de `iso19650-openbim`** (`scripts/lineal/`,
  PT 5.1): parser `ifc_to_model_lineal.py` (IFC 4.3 -> modelo neutro lineal),
  `validacion_alineacion.py` (continuidad/tangencia/PK/georref) y `export_gis.py`.
- **C1 §4bis — ganchos rellenados aqui:** el modelo neutro lineal dejaba
  `secciones_tipo`/`firme`/`terreno` = `None`; este plugin **rellena** `firme` (firmes),
  una `secciones_tipo` basica y la clave **nueva** `drenaje` (caudales + cunetas + ODT).
  `terreno` queda para geotecnia/movimiento de tierras (no es de este PT).
- **CN-3 — datos de proyecto: aqui.** Vp (trazado), IMDp/explanada (firmes) y la
  **hidrologia** (cuenca A/L/J, lluvia Pd/I1Id/Po, periodo de retorno T) en drenaje. El
  **dato del IFC/GIS prevalece**; si falta, lo inyecta el agente (`[confirmar AN]`).
- **Sin espejo de nucleo:** no se lee IFC ni se usa `grafo_red`; se trabaja sobre el JSON
  neutro. La puerta `verificar_espejo_nucleo.py` **no aplica**.

## Uso rapido

```bash
# Trazado (3.1-IC) para una velocidad de proyecto:
python3 scripts/trazado/run_all_trazado.py modelo_neutro_lineal.json out --vp 60

# Firmes (6.1-IC) a partir de IMD + %pesados y explanada (rellena el gancho firme):
python3 scripts/firmes/run_all_firme.py modelo_neutro_lineal.json out \
        --imd 8000 --pct 12 --calzada-unica --ev2 150

# Drenaje (5.2-IC): hidrologia + cunetas + ODT (rellena el gancho drenaje):
python3 scripts/drenaje/run_all_drenaje.py modelo_neutro_lineal.json out \
        --datos datos_drenaje.json --tr-cuneta 25 --tr-odt 100
```

El calculo de trazado/firmes/drenaje es **stdlib pura** (sin dependencias). El parser/
validador/export GIS de `iso19650-openbim` requieren `ifcopenshell` (IFC4X3).

## Estado y alcance

- **v0.1.0 (PT 5.2, Ola 5):** nacen el agente `ingeniero-de-obra-lineal` y los subagentes
  **trazado (3.1-IC)** y **firmes (6.1-IC)**. Casos e2e `caso-LIN-02-trazado` y
  `caso-LIN-03-firmes`. Write-back de `Pset_Estructurando_ResultadoLineal` y export GIS.
- **v0.2.0 (PT 6.1, Ola 6):** nace el subagente **drenaje (5.2-IC)**: hidrologia por el
  metodo racional modificado (tc de Temez, IDF, coef. de escorrentia), capacidad de
  **cunetas** (Manning de seccion simple) y de **ODT** (control de entrada/salida);
  rellena el gancho **`drenaje`** del modelo neutro. Caso e2e `caso-LIN-04-drenaje`.
- **v0.3.0 (PT 6.2, Ola 6):** nace el subagente **saneamiento (EN 752)** y el solver de
  **Manning de red** (lamina libre) sobre el grafo del nucleo (espejado); IFC MEP de
  saneamiento. Caso `caso-LIN-05-saneamiento`.
- **v0.4.0 (PT 6.3, Ola 6 · CIERRE):** nace el subagente **abastecimiento (EN 805)** y se
  **reutiliza —copia byte a byte— el solver Darcy** de `instalaciones` (`scripts/red/
  solver_presion.py`): red **a presion**, arbol **desde la fuente** (deposito por cota /
  bombeo) + Hardy-Cross en mallas; demanda EN 805 + **hidrante concurrente**; comprueba
  velocidad 0,5–2,0 m/s, presion >= 250 kPa y DN minimo. IFC MEP de abastecimiento
  (WATERSUPPLY; fuente = deposito `IfcTank`). Caso `caso-LIN-06-abastecimiento`. **Cierra
  la Ola 6.**
- **Ola 7:** el eje/alineacion verificado aqui lo reutilizara el **puente** (estructuras).

> Todo es **predimensionado/asistencia** y debe ser **revisado y firmado por tecnico
> competente** (Ingeniero de Caminos). NDP marcados `[confirmar AN]`.

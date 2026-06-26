# Texto de inicio del Caso 10 — para pegar en un hilo nuevo

> Copia y pega el bloque siguiente al iniciar el hilo del Caso 10 en el proyecto
> **Estructurando**. Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **Caso 10 — edificio integrado** (décimo y último peldaño de la primera tanda) del programa de aprendizaje. Lee primero `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y `CHANGELOG-plugin.md`; luego `Casos-de-uso/caso-10-edificio-integrado/ENUNCIADO.md` y trabaja sobre `caso-10.ifc` con el agente `ingeniero-estructurista`.

**Punto de partida:** plugin **motor-calculo-estructural v0.11.0** (en el caso 9 quedó resuelta la **cimentación profunda** —vía ortodoxa de pilote/encepado/pantalla, `IfcCircleProfileDef` en `barras/perfiles_db`, y la **clasificación/enrutado por Pset** de tres sistemas en un mismo IFC—). Con v0.11.0 **cada módulo ya tiene su vía ortodoxa** (`parse_ortodoxo()` + `parse_auto()`, prioritaria; Pset como respaldo), y cada parser **selecciona su propio elemento** por Pset/geometría (casos 7–9). El parser genérico `scripts/laminas/ifc_to_model_3d.py` **ya lee** sobre `caso-10.ifc` las 5 barras (2 pilares HEB 240 + dintel IPE 360 + viga mixta IPE 400, todas `tipo` por geometría; pilar HA 0,40 rectangular) y las 3 superficies (losa mixta t=0,12, muro t=0,20, zapata t=0,60) con su sección/material, más las cargas (línea, superficie por fase y puntuales) y los apoyos/lecho —verificado (ver `validacion-IFC.txt`)—. Lo que **falta** es el nivel superior: iterar TODO el IFC y clasificar/enrutar CADA elemento (hasta ahora se leía un único elemento con `by_type[0]`).

**El modelo (sintético, realista):** un **único IFC ortodoxo multi-elemento** (`caso-10.ifc`) que reúne, en un solo `IfcStructuralAnalysisModel`, los **cuatro sistemas estructurales** del catálogo separados en planta, cada uno con su marcador Pset:

- **A) Pórtico de acero** → `barras` (EC3, como caso 1): 2 pilares **HEB 240** + dintel **IPE 360** (S275), luz 6 m, altura 4 m; carga de línea en el dintel **G=12 / Q=10 kN/m** (`IfcStructuralCurveAction`). Marcador `Pset_Estructurando_Portico`.
- **B) Forjado mixto / viga mixta** → `mixtas` (EC4, como caso 6): viga **IPE 400** (S275) L=8 m + losa colaborante **C25/30 t=0,12** (hp58/hc62, chapa perpendicular, sin apear), sep=3,0 m; cargas por **fase** (`IfcStructuralSurfaceAction`, grupos `*_construccion` / `*_mixta`). Conectores y chapa en `Pset_Estructurando_Conectores`/`_Losa`. Marcador `Pset_Estructurando_Mixta`.
- **C) Muro de carga / núcleo** → `laminas` (EC2 esbeltez, como caso 7): superficie vertical **C30/37 H=3,0 t=0,20**, faja 1,0, arriostrado; carga de cabeza excéntrica **N_G=250 / N_Q=120 kN, e=25 mm** (`IfcStructuralPointAction` N + M). Marcador `Pset_Estructurando_MuroCarga`.
- **D) Cimentación superficial** → `cimentaciones` (EC2+EC7, como caso 5): pilar HA **0,40×0,40** (`IfcRectangleProfileDef`) sobre zapata aislada **2,5×2,5 t=0,60** en lecho **ks=40 MN/m³** (`IfcBoundaryNodeCondition` en las 4 esquinas), **R_d=250 kPa**; carga de cabeza del pilar **N_G=700 / N_Q=250 kN + M=80/40 kN·m**. `Pset_Estructurando_Suelo` (ks, Rd) + `_Zapata` (geometría).

Conectores/chapa de la mixta, faja/arriostramiento/excentricidad del muro y ks/Rd/geometría de la zapata van en Pset (respaldo y portador del marcador de sistema), igual que casos 5/6/8/9.

**Trabajo del hilo (cierre de INC-03 — multi-elemento):**

1. **Clasificador/enrutador multi-elemento** (p. ej. `scripts/clasificador.py`) que reciba el IFC, construya el modelo neutro genérico (`laminas/ifc_to_model_3d`) y devuelva, **por elemento**, `(clase, módulo, run_all, datos)`, **iterando TODO el IFC** (no `by_type[0]`). Reglas por **geometría + sección del perfil + material + Pset marcador**: barra vertical de acero I → pilar EC3; barra horizontal de acero I **aislada** → viga/dintel EC3; barra horizontal de acero I **asociada a una losa** → viga mixta EC4; superficie vertical de hormigón con carga de cabeza → muro de carga EC2; superficie horizontal de hormigón **con lecho** → zapata EC7; barra vertical de hormigón rectangular sobre zapata → cadena pilar→cimiento. Generaliza la clasificación por geometría+Pset ya probada en los casos 7 (muro carga/contención) y 9 (pilote/pantalla/encepado).

2. **Asociaciones dentro del IFC**: viga↔losa (mixta) por proximidad/nombre y pilar↔zapata por coincidencia de pie, sin Pset si es posible.

3. **Orquestador integrado** (`run_all_edificio.py`) que invoque el `run_all*` de cada subsistema con su porción del IFC y consolide resultados y memoria. Corrección **acotada pero estructural** (es el objetivo del caso), sin romper los casos 1–9.

4. Resuelve los **6 elementos resolubles** y valida contra los criterios de cada módulo (ya probados): **pórtico EC3** (N-M de pilares, flexión/flecha del dintel); **viga mixta EC4** (b_eff, M_pl,Rd con grado de conexión, conectores, cortante, fases, flecha); **muro EC2** (esbeltez columna modelo M0+M2, N-M); **cimentación EC2+EC7** (hundimiento por área eficaz, flexión/punzonamiento/cortante/fisuración, asiento). Picos como envolvente; aprovechamientos ≤ 1.

5. **Memoria(s)** Word y diagramas por subsistema, más un **índice integrado** del edificio. Entrega en `caso-10-edificio-integrado/`: `modelo_neutro.json`, `verificacion*.json` por subsistema, memoria(s) y diagramas.

6. Registra: lección del caso 10 (clasificación/enrutado multi-elemento; cierre de INC-03) y fila de métricas en `REPOSITORIO-aprendizaje.md` —**cierre de la primera tanda**—, corrección en `CHANGELOG-plugin.md`, sube el plugin a **0.12.0** (minor: clasificador/enrutador multi-elemento + orquestador integrado) y reempaqueta el `.plugin` (excluyendo `node_modules`/`__pycache__`).

7. (Opcional) Define la **segunda tanda** (casos 11+): pantallas a cortante + sísmico EC8, Mononobe-Okabe, pretensado, no-lineal.

**Notas de método (casos 1–9):** escribe el código del plugin por heredoc en el sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); empaqueta el `.plugin` con el módulo `zipfile` de Python construyéndolo en una carpeta escribible (p. ej. dentro del workdir, no en `/tmp` raíz) como `.zip` con nombre nuevo y copiándolo después con extensión `.plugin`; instala `ifcopenshell`/`PyNiteFEA`/`numpy`/`matplotlib` (pip `--break-system-packages`) y `docx` localmente (no global) para la memoria; **clasifica e itera TODOS los elementos antes de enrutar** (es el objetivo del caso: 4 sistemas distintos en un mismo IFC); cuidado con los **módulos homónimos** entre paquetes (`solver_*`, `combinaciones`, `plots_*`, `run_all*`…) al cruzar imports —carga por ruta explícita con salvaguarda de `sys.path`—; no uses el pico singular de esfuerzo/presión como valor de diseño; el solver de barras / la malla fina son lentos en el sandbox (ejecuta por subsistema o separa solver / verificación / mapas si el orquestador supera 45 s); las herramientas de fichero (Read/Write/Edit, rutas del proyecto) son la fuente de verdad de la carpeta conectada —el shell del sandbox puede ver copias truncadas de ficheros preexistentes—; resultado de **predimensionado**, a revisar y firmar por técnico competente, con los NDP marcados `[confirmar AN]`.

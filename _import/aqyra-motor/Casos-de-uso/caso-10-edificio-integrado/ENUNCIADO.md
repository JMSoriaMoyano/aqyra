# Caso 10 — Edificio integrado: pórtico + forjado mixto + muro/núcleo + cimentación

> Décimo y último peldaño de la primera tanda. Antes de empezar, lee
> `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y
> `CHANGELOG-plugin.md`. Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.11.0** (en el caso 9 quedó
> resuelta la **cimentación profunda** —vía ortodoxa de pilote/encepado/pantalla,
> `IfcCircleProfileDef` en `perfiles_db`, y la **clasificación/enrutado por Pset**
> de tres sistemas en un mismo IFC—).

## 1. Contexto y objetivo

Se entrega un **único IFC ortodoxo multi-elemento** (`caso-10.ifc`) que reúne, en
un solo `IfcStructuralAnalysisModel`, los **cuatro sistemas estructurales** del
catálogo, separados en planta:

- **A) Pórtico de acero** (`barras`, EC3): 2 pilares HEB 240 + dintel IPE 360
  (S275), luz 6 m, altura 4 m; carga de línea G/Q en el dintel.
- **B) Forjado mixto / viga mixta** (`mixtas`, EC4): viga IPE 400 (S275) L=8 m +
  losa colaborante C25/30 t=0,12 (chapa perpendicular, sin apear), sep=3,0 m;
  cargas por **fase** (grupos `*_construccion` / `*_mixta`).
- **C) Muro de carga / núcleo** (`laminas`, EC2 esbeltez): superficie vertical
  C30/37 H=3,0 t=0,20, carga de cabeza excéntrica N+M.
- **D) Cimentación superficial** (`cimentaciones`, EC2+EC7): pilar HA 0,40 sobre
  zapata 2,5×2,5 t=0,60 en lecho ks=40 MN/m³, carga de cabeza N+M.

Es el peldaño que culmina **INC-03 (multi-elemento)**: por primera vez el agente
debe **iterar todos los elementos** del IFC y **clasificar y enrutar CADA uno** a
su módulo, en lugar de leer un único elemento con `by_type[0]`.

Doble objetivo, como en cada peldaño:

- **Calcular** los cuatro subsistemas con el motor (cada uno con su `run_all*`) y
  validar contra los criterios de cada módulo (que ya están probados en casos 1–9).
- **Cerrar la brecha estructural**: un **clasificador/enrutador multi-elemento**
  que recorra el modelo neutro genérico (`laminas/ifc_to_model_3d`) y, por la
  combinación de **geometría + sección del perfil + material + Pset marcador**,
  asigne cada elemento a `barras`, `mixtas`, `laminas` o `cimentaciones`,
  resolviendo además las **asociaciones** viga↔losa (mixta) y pilar↔zapata.

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. El IFC es **ortodoxo**:
cada elemento es una entidad estándar de análisis con su sección de perfil
(`IfcIShapeProfileDef` / `IfcRectangleProfileDef`), su superficie con espesor
(`Thickness`), sus apoyos/lecho (`IfcBoundaryNodeCondition`) y sus cargas
(`IfcStructuralCurveAction` / `IfcStructuralSurfaceAction` / `IfcStructuralPointAction`
con su `IfcStructuralLoadGroup`). Los únicos datos sin entidad de análisis estándar
(conectores y chapa de la mixta, faja/arriostramiento del muro, ks/Rd y geometría
de la zapata) van en Pset, **respaldo** y portador de los marcadores de sistema.

## 3. Brecha conocida (lo que hay que corregir)

Con el plugin v0.11.0, cada módulo ya tiene su **vía ortodoxa**, pero cada parser
**selecciona su propio elemento** (por Pset, en casos 7–9). Falta el nivel
superior:

1. **Clasificador/enrutador multi-elemento.** Un módulo (p. ej.
   `scripts/clasificador.py`) que reciba el IFC, construya el modelo neutro
   genérico y devuelva, por elemento, `(clase, módulo, run_all, datos)`. Reglas:
   barra vertical de acero I → pilar EC3; barra horizontal de acero I aislada →
   viga/dintel EC3; barra horizontal de acero I **asociada a una losa** → viga
   mixta EC4; superficie vertical de hormigón con carga de cabeza → muro de carga
   EC2; superficie horizontal de hormigón **con lecho** → zapata/raft EC7; barra
   vertical de hormigón rectangular sobre zapata → cadena pilar→cimiento.
2. **Orquestador integrado** (`run_all_edificio.py`) que invoque el `run_all*` de
   cada subsistema con su porción del IFC y consolide resultados y memoria.
3. **Asociaciones dentro del IFC**: viga↔losa (mixta) por proximidad/nombre, y
   pilar↔zapata por coincidencia de pie, sin Pset si es posible.

Corregir de forma **acotada pero estructural** (es el objetivo del caso). Anotar en
`CHANGELOG-plugin.md` y subir el plugin a **0.12.0** (minor: clasificador/enrutador
multi-elemento + orquestador integrado).

## 4. Criterios de aceptación

1. **Clasificación/enrutado**: el agente identifica y enruta los **6 elementos
   resolubles** (2 pilares + dintel del pórtico; viga+losa mixta; muro; pilar+zapata)
   a `barras`, `mixtas`, `laminas` y `cimentaciones`, **iterando todo el IFC**.
2. **Pórtico (EC3)**: esfuerzos del pórtico, N-M de pilares y flexión/flecha del
   dintel; aprovechamientos ≤ 1 (como caso 1).
3. **Viga mixta (EC4)**: b_eff, M_pl,Rd con grado de conexión, conectores, cortante,
   fases y flecha; aprovechamientos ≤ 1 (como caso 6).
4. **Muro de carga (EC2)**: esbeltez por columna modelo (M0+M2), N-M; aprov. ≤ 1
   (como caso 7).
5. **Cimentación (EC2+EC7)**: hundimiento por área eficaz, flexión/punzonamiento/
   cortante/fisuración y asiento; aprov. ≤ 1 (como caso 5).
6. **Memoria(s)** Word y diagramas por subsistema, más un **índice integrado** del
   edificio. Picos como envolvente; resultado de predimensionado.

## 5. Entregables del hilo

- Clasificador/enrutador multi-elemento + orquestador integrado, plugin
  reempaquetado **v0.12.0** y `CHANGELOG-plugin.md` actualizado.
- En `caso-10-edificio-integrado/`: `modelo_neutro.json`, `verificacion*.json` por
  subsistema, memoria(s) y diagramas.
- `REPOSITORIO-aprendizaje.md`: lección del caso 10 (clasificación/enrutado
  multi-elemento; cierre de INC-03) y fila de métricas. Cierre de la primera tanda.
- (Opcional) Definir la **segunda tanda** (casos 11+): pantallas a cortante +
  sísmico EC8, Mononobe-Okabe, pretensado, no-lineal.

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso10_ifc.py
# 2) tras el clasificador/enrutador y el orquestador integrado:
cd <plugin>/scripts && python3 run_all_edificio.py <proj> <ruta>/caso-10.ifc
# o, por subsistema, con cada run_all* sobre el mismo IFC (cada parser ya
# selecciona su elemento por Pset/geometria — vias ortodoxas v0.11.0).
```

> Recuerda: **clasifica e itera TODOS los elementos** antes de enrutar (es el
> objetivo del caso). No uses el pico singular como esfuerzo de diseño. Solver de
> barras / malla fina lentos en sandbox: ejecuta por subsistema si superas 45 s.
> Cuidado con los módulos homónimos entre paquetes (carga por ruta explícita con
> salvaguarda de `sys.path`). Resultado de **predimensionado**, a revisar y firmar
> por técnico competente; marca `[confirmar AN]` los NDP.

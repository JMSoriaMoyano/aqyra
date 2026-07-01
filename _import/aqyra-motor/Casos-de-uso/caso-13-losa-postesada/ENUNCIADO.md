# Caso 13 — Losa plana postesada (EC2 §5.10 + §6.4.4)

> **Tercer peldaño de la segunda tanda. Continúa la tipología de pretensado y la lleva
> a 2D.** Antes de empezar, lee `Casos-de-uso/PROGRAMA-aprendizaje.md`,
> `REPOSITORIO-aprendizaje.md`, `CHANGELOG-plugin.md` y la
> `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0, Dirección 1). Trabaja con el
> agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.16.0** (acumulativo: `sismico/`,
> `pretensado/` y `puente_analitico/` R1+R2 ya incluidos). El caso 13 toma **0.17.0**.

## 1. Contexto y objetivo

Se entrega un **IFC ortodoxo** con una **losa plana postesada** (post-tensioned flat
slab) de un forjado de oficinas. Hormigón **C40/50**, espesor **t=0,25 m**, planta
**16,0 × 16,0 m** (dos vanos × dos vanos de 8,0 m) sobre una **retícula 3×3 de pilares
0,45 × 0,45 m** (L/h ≈ 32). El **pretensado postesado no adherente** (monotorones
Y1860S7 0,6", Ap=150 mm²/cordón) sigue un **trazado parabólico** con drape **a=0,17 m**,
con **tendones banded sobre las líneas de pilares en X** y **distribuidos en Y**. Los
datos del pretensado van en `Pset_Estructurando_Pretensado` de la **superficie** (sin
entidad de análisis estándar, igual que ks/Rd, conectores, terreno, sismo, pretensado de
los casos 5/6/7/9/11/12).

Es el caso que **lleva el pretensado a 2D**: reutiliza el módulo `pretensado/` (EC2
§5.10, caso 12) y la losa plana `laminas/flat` (placa MITC4 + punzonamiento, caso 3).
Doble objetivo:

- **Calcular** la losa postesada (balance de cargas 2D con tendones banded+distribuidos
  y, en paralelo, fuerza+excentricidad por franjas), con pérdidas, y **verificarla**
  (tensiones por fibra en transferencia y servicio, **punzonamiento con efecto favorable
  del pretensado** §6.4.4, ELU de flexión por fibras con armadura activa+pasiva,
  fisuración y flecha).
- **Ampliar** el motor con el **balance de cargas 2D** y el **punzonamiento con
  pretensado** (§6.4.4), reutilizables por el caso 15 (tablero) y por proyectos reales.

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. Losa en el plano XY (z=0).

- **Losa** `IfcStructuralSurfaceMember` horizontal C40/50, **Thickness=0,25 m**, planta
  16,0 × 16,0 m (`IfcFaceSurface`/`IfcPolyLoop`). Por metro: A=0,25 m²/m,
  I=1,302·10⁻³ m⁴/m, W=0,010417 m³/m, c=0,125 m.
- **Pilares** (9) `IfcStructuralCurveMember` verticales C40/50, sección
  `IfcRectangleProfileDef` **0,45 × 0,45 m**, H=3,0 m, retícula {0, 8, 16} m, empotrados
  en su base (z=−3,0). Las **cabezas (z=0)** son los apoyos puntuales de la losa.
- **Cargas** por la vía ortodoxa (`IfcStructuralSurfaceAction` + `IfcStructuralLoadGroup`):
  - **G** carga muerta **g2 = 2,75 kN/m²** (solado/tabiquería; grupo permanente).
  - **Q** sobrecarga de uso **q = 5,0 kN/m²**, **ψ₂=0,3** (grupo variable).
  - El **peso propio g0 = t·25 = 6,25 kN/m²** lo añade el solver (como en el caso 12);
    permanente total g0+g2 = 9,0 kN/m².
- **Pretensado** en `Pset_Estructurando_Pretensado` de la losa: sistema **postesado no
  adherente (monotorón)**, **Ap=150 mm²/cordón**, **fpk=1860**, fp0,1k=1640, Ep=195 GPa;
  **trazado parabólico** drape **a=0,17 m** (recubrimiento al eje ≈0,04 m); **layout
  banded_X + distribuido_Y**; por dirección **P/m ≈ 212 kN/m** (≈1,27 cordón/m), σp0≈1339
  (0,72·fpk), σp,∞≈1116 (0,60·fpk), **σcp≈0,85 MPa**, **w_balance=9,0 kN/m²**;
  coeficientes de pérdidas de monotorón engrasado (**μ=0,06 rad⁻¹, k=0,005 m⁻¹**,
  penetración de cuña 6 mm, relajación clase 2). Marcar **[confirmar AN]** (EC2 §5.10 /
  §6.4.4 NDP España).

## 3. Brecha conocida (lo que hay que CREAR)

El plugin v0.16.0 tiene `laminas/flat` (caso 3) y `pretensado/` 1D (caso 12), pero **no
el balance de cargas 2D de losa postesada ni el punzonamiento con efecto favorable del
pretensado** (§6.4.4). Corrección **acotada** (nuevo orquestador + ampliación de
punzonamiento, sin tocar los casos 1–12):

1. **Orquestador de losa postesada** (`run_all_losa_postesada.py`, en `pretensado/` o
   `laminas/`): parser ortodoxo de losa+pilares (reutiliza `laminas/flat`) + lectura del
   `Pset_Estructurando_Pretensado` de la **superficie** (banded/distribuido, drape, P/m
   por dirección, σp0/σp,∞, pérdidas). Idealización de placa sobre apoyos puntuales.
2. **Balance de cargas 2D** (amplía la biblioteca `pretensado/`): cargas equivalentes de
   los tendones banded (X) + distribuidos (Y) como **presión hacia arriba w_p por
   dirección** + **axil de precompresión σcp** en el plano; aplicar como **caso P** en la
   placa MITC4; residual = cargas externas − balance. Contraste por **fuerza+excentricidad
   por franjas** (debe coincidir, como en el caso 12).
3. **Punzonamiento con pretensado (EC2 §6.4.4):** ampliar el punzonamiento de
   `laminas/flat` con (a) **v_Rd,c += k₁·σcp** (k₁=0,1 `[confirmar AN]`) y (b) el
   **descuento de la componente vertical de los tendones que cruzan el perímetro de
   control** de V_Ed. Verificación de tensiones por fibra (transferencia/servicio), ELU
   de flexión por fibras con activa+pasiva, fisuración §7.3 y flecha con pretensado.

Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.17.0** (minor: losa postesada 2D
+ punzonamiento con pretensado §6.4.4), reempaquetando el `.plugin` de forma
**acumulativa** **partiendo del v0.16.0 instalado** (preservando `sismico/`,
`puente_analitico/` R1+R2 y `pretensado/`). La viga hiperestática (caso 14) y el tablero
prefabricado (caso 15) quedan como continuación.

## 4. Criterios de aceptación

1. **Balance de cargas 2D**: w_p,x + w_p,y ≈ permanente (9,0 kN/m²), residual ≈ 0 %;
   **P/m ≈ 212 kN/m** por dirección; **σcp ≈ 0,85 MPa**; σp,∞ ≈ 0,60·fpk; en transferencia
   σp0 ≈ 0,72·fpk (pérdidas ≈ 16–18 %).
2. **Cargas no equilibradas (servicio)**: cuasipermanente ≈ 1,5 kN/m²; rara ≈ 5,0 kN/m².
3. **Tensiones (fibra, por franja)**: bajo cuasipermanente todo comprimido o tracción
   reducida; bajo la rara, tracción de fondo controlada (< fctm=3,5). Compresión ≤
   0,6·fck(t) en transferencia y ≤ 0,45·fck en cuasipermanente.
4. **Punzonamiento §6.4.4 (lo nuevo)**: pilar interior, V_Ed,ELU ≈ **1.258 kN** (área
   tributaria 8×8=64 m²; pico elástico como envolvente). Con **efecto favorable del
   pretensado** (σcp en v_Rd,c + componente vertical de tendones) el aprovechamiento debe
   **relajarse** frente al cálculo sin pretensado; reportar ambos.
5. **Contraste cargas equivalentes vs fuerza+excentricidad** (por franja) → mismo estado
   tensional.
6. **ELU** M_Rd ≥ M_Ed por fibras (activa+pasiva); **flecha** controlada (residual de
   permanente ≈ 0 → flecha reducida). Aprovechamientos ≤ 1; picos como envolvente.
7. **Salidas**: planta de tendones (banded/distribuido), cargas equivalentes 2D, mapas de
   momento/tensión, perímetro de control con los tendones que lo cruzan, ELU por franja,
   flecha; memoria de cálculo. Resultado de **predimensionado**.

## 5. Entregables del hilo

- Orquestador de losa postesada + ampliación de balance 2D y punzonamiento §6.4.4, plugin
  reempaquetado **v0.17.0 acumulativo** y `CHANGELOG-plugin.md` actualizado.
- En `caso-13-losa-postesada/`: `caso-13.ifc`, `validacion-IFC.txt`, `modelo_neutro.json`,
  `verificacion_losa_postesada.json`, memoria(s) Word y diagramas (planta de tendones,
  cargas equivalentes 2D, mapas de momento/tensión, perímetro de punzonamiento con
  tendones, interacción/ELU por franja, flecha). Código fuente en `_codigo/`.
- `REPOSITORIO-aprendizaje.md`: lección del caso 13 (balance de cargas 2D; punzonamiento
  con efecto favorable del pretensado §6.4.4; tensiones/ELU/flecha de losa postesada) y
  fila de métricas. **Lleva la tipología de pretensado a 2D.**

## 6. Cómo ejecutar (orientación)

```bash
# 1) generar el IFC del caso:  python3 generate_caso13_ifc.py   (YA GENERADO: caso-13.ifc)
# 2) tras crear el orquestador de losa postesada:
cd <plugin>/scripts && python3 pretensado/run_all_losa_postesada.py <proj> <ruta>/caso-13.ifc
# 3) memoria:
python3 pretensado/generate_memoria_losa_postesada.py <proj>
```

> Recuerda: el pretensado entra como **cargas equivalentes** (balance 2D) y como
> **fuerza+excentricidad** por franja; ambos deben dar el **mismo estado tensional**. El
> **punzonamiento con pretensado** (§6.4.4) es la novedad: σcp en v_Rd,c + componente
> vertical de los tendones que cruzan u1; reportar con y sin efecto favorable. La
> no-linealidad de la sección en ELU se trata por **fibras** (como en EC4 / caso 12). No
> uses el pico singular como valor de diseño (envolvente). Escribe el código por **heredoc**
> y valida con `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo
> `node_modules`/`__pycache__` y de forma **acumulativa partiendo del v0.16.0 instalado**
> (preserva `sismico/`, `puente_analitico/` R1+R2 y `pretensado/`); si hay un hilo de la
> Dirección 2 (R3) en paralelo, reempaqueta acumulativo y avisa de la coordinación. Las
> herramientas de fichero (Read/Write/Edit) son la fuente de verdad de la carpeta del
> proyecto (el shell puede ver copias truncadas de ficheros preexistentes). Resultado de
> **predimensionado**, a revisar y firmar por técnico competente; marca `[confirmar AN]`
> los NDP (EC2 §5.10/§6.4.4: pérdidas, límites de tensión del acero activo, μ/k de
> rozamiento, k₁ de punzonamiento — Anejo Nacional España).

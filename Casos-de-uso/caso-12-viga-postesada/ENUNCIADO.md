# Caso 12 — Viga postesada isostática (EC2 §5.10)

> **Segundo peldaño de la segunda tanda. Abre la tipología de elementos pretensados.**
> Antes de empezar, lee `Casos-de-uso/PROGRAMA-aprendizaje.md`,
> `REPOSITORIO-aprendizaje.md`, `CHANGELOG-plugin.md` y la
> `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0, Dirección 1). Trabaja con el
> agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.14.0** (acumulativo: módulos
> `sismico/` y `puente_analitico/` ya incluidos). El caso 12 toma **0.15.0**.

## 1. Contexto y objetivo

Se entrega un **IFC ortodoxo** con una **viga postesada isostática** (simplemente
apoyada) de un forjado/cubierta de gran luz. Hormigón **C40/50**, sección rectangular
**b=0,50 × h=1,30 m**, **L=20,0 m** (canto/luz ≈ 1/15). El **pretensado postesado**
(1 tendón de 13 cordones Y1860S7, Ap=1.950 mm², conducto inyectado/adherente) sigue un
**trazado parabólico** anclado en el c.d.g. en apoyos (e=0) y con excentricidad
**e=0,50 m** en centro de vano. Los datos del pretensado van en
`Pset_Estructurando_Pretensado` (sin entidad de análisis estándar, igual que ks/Rd,
conectores, terreno, sismo de los casos 5/6/7/9/11).

Es el caso que **abre la tipología de pretensado**: por primera vez el motor incorpora
la **acción de pretensado** (P) y la biblioteca **EC2 §5.10**. Doble objetivo:

- **Calcular** la viga postesada (pretensado como cargas equivalentes / load balancing
  y, en paralelo, como fuerza+excentricidad), con pérdidas instantáneas y diferidas, y
  **verificarla** (tensiones en transferencia y servicio por fibras, ELU de flexión con
  armadura activa+pasiva, fisuración, cortante con pretensado).
- **Crear** el **módulo `pretensado/`** y la **biblioteca EC2 §5.10**, que reutilizarán
  los casos siguientes (losa postesada, viga hiperestática con momentos secundarios,
  tablero prefabricado).

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. Eje de la viga en X.

- **Viga** `IfcStructuralCurveMember` horizontal C40/50, sección
  `IfcRectangleProfileDef` **b=0,50 × h=1,30 m**, **L=20,0 m**, biapoyada. Propiedades:
  A=0,65 m², I=0,091542 m⁴, W_sup=W_inf=0,140833 m³, c.d.g. a 0,65 m.
- **Apoyos** `IfcStructuralPointConnection` + `IfcBoundaryNodeCondition`: apoyo fijo en
  x=0 (Ux,Uy,Uz) y apoyo móvil en x=L (Uy,Uz) → isostático biapoyado.
- **Cargas** por la vía ortodoxa (`IfcStructuralCurveAction` + `IfcStructuralLoadGroup`):
  - **g2** carga muerta = **5,0 kN/m** (grupo permanente).
  - **q** sobrecarga de uso = **12,0 kN/m**, **ψ₂=0,3** (grupo variable).
  - El **peso propio g0=16,25 kN/m** (= A·ρ·g, A·25) lo añade el solver a partir de la
    sección y la densidad del material (marcado en el modelo neutro).
- **Pretensado** en `Pset_Estructurando_Pretensado` del curve member: P0 (o σp0),
  **Ap=1.950 mm²**, 1 tendón **13×Y1860S7 0,6"**, **fpk=1860 MPa**, fp0,1k=1640 MPa,
  Ep=195 GPa; **trazado parabólico** e=0,50 m en centro y e=0 en apoyos (recubrimiento
  mecánico 0,15 m al fondo); **conducto adherente**; coeficientes de pérdidas
  (μ=0,19 rad⁻¹, k=0,01 m⁻¹, penetración de cuña 6 mm, relajación clase 2). Marcar
  **[confirmar AN]** (EC2 §5.10 NDP España).

## 3. Brecha conocida (lo que hay que CREAR)

El plugin v0.14.0 **no tiene módulo de pretensado ni biblioteca EC2 §5.10**. Corrección
**estructural pero acotada** (nuevo grupo, sin tocar los casos 1–11):

1. **Nuevo módulo `pretensado/`**: parser ortodoxo de la viga (geometría, sección
   `IfcRectangleProfileDef`, material, apoyos y cargas g2/q por la vía estándar,
   reutilizando `laminas/ifc_to_model_3d` cargado por ruta explícita con salvaguarda de
   `sys.path`) + lectura del `Pset_Estructurando_Pretensado`. Idealización isostática
   biapoyada.
2. **Nueva biblioteca EC2 §5.10** (`ec2_pretensado.py`):
   - **Pretensado como cargas equivalentes** (load balancing: w_p = 8·P·e/L²; fuerzas de
     desvío + axil y momentos de anclaje) y, en paralelo, como **fuerza+excentricidad**.
   - **Pérdidas instantáneas** (rozamiento μ·(θ+k·x), penetración de cuña, acortamiento
     elástico) y **diferidas** (retracción, fluencia, relajación) §5.10.6.
   - **Combinaciones** característica/frecuente/cuasipermanente con el pretensado como
     acción P.
3. **Verificación de la viga** (`verificacion_pretensado.py`): **tensiones en
   transferencia y servicio por fibras** (compresión ≤ 0,6·fck(t) en transferencia y
   ≤ 0,45·fck en cuasipermanente; tracción/descompresión §5.10.2.2/§7), **ELU de flexión
   por fibras** con armadura activa+pasiva (M_Rd ≥ M_Ed), **fisuración §7.3**, **cortante
   con pretensado** (V_Rd,c con σcp).

Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.15.0** (minor: módulo pretensado
+ biblioteca EC2 §5.10), reempaquetando el `.plugin` de forma **acumulativa**
(preservando `sismico/` y `puente_analitico/`). La losa postesada (caso 13), la viga
hiperestática (caso 14) y el tablero prefabricado (caso 15) quedan como continuación.

## 4. Criterios de aceptación

1. **Equilibrio de cargas (load balancing)**: w_p equilibra la permanente (residual
   ≈ 0 %); **P_m,∞ ≈ 2.125 kN**, **σp,∞ ≈ 0,59·fpk**; en transferencia **P0 ≈ 2.535 kN**,
   σp0 ≈ 0,70·fpk (pérdidas totales ≈ 16 %).
2. **Momentos**: M_g0=812, M_perm=1.062, M_q=600, M_cuasiperm=1.242, M_rara=1.662 kN·m;
   **ELU M_Ed ≈ 2.334 kN·m**.
3. **Tensiones (fibra, compresión negativa)**: transferencia (P0+g0) sup −0,67 / inf
   −7,13 MPa (todo comprimido); servicio cuasipermanente sup −4,55 / inf −1,99 MPa (sin
   descompresión del fondo); servicio rara sup −7,53 / **inf +0,99 MPa** (tracción <
   fctm=3,5, controlada). Compresión ≤ 0,6·fck(t) en transferencia y ≤ 0,45·fck en
   cuasipermanente.
4. **Contraste cargas equivalentes vs fuerza+excentricidad** → mismo estado tensional.
5. **ELU** M_Rd ≥ M_Ed por fibras (armadura activa+pasiva). Aprovechamientos ≤ 1; picos
   como envolvente.
6. **Salidas**: trazado del tendón, cargas equivalentes, leyes M/V, tensiones por fibra
   en transferencia y servicio, diagrama de interacción/ELU, pérdidas a lo largo del
   tendón; memoria de cálculo. Resultado de **predimensionado**.

## 5. Entregables del hilo

- Módulo `pretensado/` + biblioteca EC2 §5.10, plugin reempaquetado **v0.15.0
  acumulativo** y `CHANGELOG-plugin.md` actualizado.
- En `caso-12-viga-postesada/`: `caso-12.ifc`, `validacion-IFC.txt`, `modelo_neutro.json`,
  `verificacion_pretensado.json`, memoria(s) Word y diagramas (trazado, cargas
  equivalentes, M/V, tensiones por fibra transferencia y servicio, interacción/ELU,
  pérdidas). Código fuente en `_codigo/`.
- `REPOSITORIO-aprendizaje.md`: lección del caso 12 (pretensado EC2 §5.10; load
  balancing; pérdidas; tensiones por fibra; ELU con activa+pasiva) y fila de métricas.
  **Apertura de la tipología de pretensado.**

## 6. Cómo ejecutar (orientación)

```bash
# 1) generar el IFC del caso:  python3 generate_caso12_ifc.py
# 2) tras crear el modulo pretensado:
cd <plugin>/scripts && python3 pretensado/run_all_pretensado.py <proj> <ruta>/caso-12.ifc
# 3) memoria:
python3 pretensado/generate_memoria_pretensado.py <proj>
```

> Recuerda: el pretensado entra como **cargas equivalentes** (load balancing) y como
> **fuerza+excentricidad**; ambos métodos deben dar el **mismo estado tensional**
> (validación cruzada). La no-linealidad de la sección en ELU se trata por **fibras**
> (como en EC4). No uses el pico singular como valor de diseño. Escribe el código por
> heredoc y valida con `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo
> `node_modules`/`__pycache__` y de forma **acumulativa** (INC-05; preserva `sismico/`
> y `puente_analitico/`). Las herramientas de fichero (Read/Write/Edit) son la fuente de
> verdad de la carpeta del proyecto (el shell puede ver copias truncadas de ficheros
> preexistentes). Resultado de **predimensionado**, a revisar y firmar por técnico
> competente; marca `[confirmar AN]` los NDP (EC2 §5.10: coeficientes de pérdidas,
> límites de tensión del acero activo, μ/k de rozamiento — Anejo Nacional España).

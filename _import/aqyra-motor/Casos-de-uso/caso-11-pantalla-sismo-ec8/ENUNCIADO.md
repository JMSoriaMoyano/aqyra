# Caso 11 — Pantalla de cortante + sísmico EC8 (modal / fuerzas laterales)

> **Primer peldaño de la segunda tanda. Abre la familia sísmica.** Antes de empezar,
> lee `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`,
> `CHANGELOG-plugin.md` y la `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0,
> Dirección 1). Trabaja con el agente `ingeniero-estructurista`.
> Plugin de partida: **motor-calculo-estructural v0.12.0** (primera tanda cerrada:
> IFC ortodoxo en todos los módulos + clasificador/enrutador multi-elemento, INC-03).

## 1. Contexto y objetivo

Se entrega un **IFC ortodoxo** con el **sistema de estabilización lateral** de un
edificio de 5 plantas: una **pantalla de hormigón armado** (C30/37) que trabaja a
cortante en su plano, empotrada en la base, con la **masa sísmica de cada planta** y
los **parámetros del espectro EC8** en Pset.

Es el caso que **abre la familia sísmica**: por primera vez el motor aborda un **tipo
de análisis nuevo** (dinámico/espectral), no sólo una verificación nueva. Doble
objetivo:

- **Calcular** la pantalla bajo sismo EC8 (análisis modal espectral y/o método de
  fuerzas laterales equivalentes) y verificarla (cortante, elementos de borde, N-M,
  deriva).
- **Crear** el **módulo sísmico** y la **biblioteca EC8** (espectro de respuesta,
  análisis modal, combinación modal), que reutilizarán los casos siguientes (núcleos,
  contención sísmica Mononobe-Okabe, etc.).

## 2. Descripción del modelo (lo que contiene el IFC)

Todo según `validacion-IFC.txt`. SI; Z vertical, gravedad −Z. Pantalla en el plano XZ.

- **Pantalla** `IfcStructuralSurfaceMember` vertical C30/37, **Lw=4,0 m, tw=0,30 m,
  H=15,0 m** (5 plantas × 3,0 m), empotrada en base. Inercia en el plano
  I=tw·Lw³/12=1,60 m⁴; área A=1,20 m². Marcador `Pset_Estructurando_Pantalla`
  (Lw, tw, H, n_plantas, h_planta, ClaseDuctilidad=DCM).
- **Masas sísmicas por planta** como `IfcStructuralPointAction` (ForceZ=−W_planta) en
  los nodos de planta (z=3,6,9,12,15), grupo `Sismo_masas`: **W=1200 kN** plantas 1–4
  y **900 kN** cubierta (W = G + ψ₂·Q tributario). ΣW=5700 kN → m=581 t. El motor
  deriva la masa m=W/g.
- **Base empotrada** `IfcBoundaryNodeCondition` (6 GDL) en `PISO_0_base`.
- **Parámetros EC8** en `Pset_Estructurando_Sismo`: ag=0,20 g; suelo **C**; espectro
  **tipo 1** (S=1,15, TB=0,20, TC=0,60, TD=2,0); clase importancia II (γI=1,0);
  **q=3,0** (DCM, sistema de muros); amortiguamiento 5%; λ=0,85. Sin entidad de
  análisis estándar → Pset (igual que ks/Rd, conectores, terreno de casos 5/6/7/9).
  Marcar **[confirmar AN]** (NCSE-02 / EC8 NDP España).

## 3. Brecha conocida (lo que hay que CREAR)

El plugin v0.12.0 **no tiene módulo sísmico ni biblioteca EC8**. Corrección
**estructural pero acotada** (nuevo grupo, sin tocar los casos 1–10):

1. **Nuevo módulo `sismico/` (o `pantallas/`)**: parser de la pantalla + masas + Pset
   sísmico; construcción del **voladizo equivalente** (stick) con masas concentradas
   por planta (flexión + cortante de la sección de pared, área de cortante de muro).
2. **Nueva biblioteca EC8 (EN 1998-1)**:
   - **Espectro de respuesta de cálculo** `Sd(T)` desde los parámetros del Pset (las
     cuatro ramas, factor q, λ).
   - **Análisis modal** (PyNite tiene análisis modal): periodos T_i, modos, **masas
     modales efectivas**; **combinación modal SRSS/CQC**.
   - **Método de fuerzas laterales equivalentes** (§4.3.3.2) como **contraste**.
   - **Combinación sísmica** (EC0 §6.4.3.4): E + ΣG + Σψ₂·Q.
3. **Verificación de la pantalla**: **cortante del alma** + armadura (EC2 §6.2 / EC8),
   **elementos de borde confinados** (EC8 §5.4.3.4), **interacción N-M en la base**,
   y **deriva entre plantas** (limitación de daño, §4.4.3.2).

Anotar en `CHANGELOG-plugin.md` y subir el plugin a **0.13.0** (minor: módulo sísmico
+ biblioteca EC8). El **núcleo** (varias pantallas acopladas) queda como extensión de
la misma familia (caso posterior).

## 4. Criterios de aceptación

1. **Espectro y análisis**: `Sd(T)` correcto (meseta ag·S·2,5/q = 0,192 g para
   TB≤T≤TC); periodo fundamental razonable (**T1 ≈ 0,4–0,6 s**, en la meseta);
   masa modal efectiva del 1er modo ≳ 60–70 %.
2. **Equilibrio**: el **cortante basal** Fb = Σ de las fuerzas de planta F_i (~0 %);
   orden de magnitud **Fb ≈ 900–950 kN** (mano: 929 kN), momento de vuelco en base
   **≈ 9.900 kN·m**. Contraste **modal espectral vs fuerzas laterales**.
3. **Verificación de la pantalla (aprov. ≤ 1)**: cortante del alma con armadura;
   **elementos de borde** (EC8 §5.4.3.4); **N-M en la base** con armadura vertical;
   **deriva entre plantas** ≤ límite de limitación de daño (p. ej. 0,5–0,75 %·h según
   elementos no estructurales, §4.4.3.2).
4. **Salidas**: modos, **fuerzas por planta**, leyes de **cortante y momento en
   altura**, **deriva**, diagrama **N-M**; memoria de cálculo sísmico. Picos como
   envolvente. Resultado de **predimensionado**.

## 5. Entregables del hilo

- Módulo `sismico/` (o `pantallas/`) + biblioteca EC8, plugin reempaquetado
  **v0.13.0** y `CHANGELOG-plugin.md` actualizado.
- En `caso-11-pantalla-sismo-ec8/`: `modelo_neutro.json`, `verificacion_sismo.json`,
  memoria(s) Word y diagramas (espectro, modos, fuerzas/cortante/momento en altura,
  deriva, N-M).
- `REPOSITORIO-aprendizaje.md`: lección del caso 11 (análisis dinámico/espectral EC8;
  pantalla a cortante) y fila de métricas. **Apertura de la segunda tanda.**

## 6. Cómo ejecutar (orientación)

```bash
# 1) (ya hecho) generar el IFC del caso:  python3 generate_caso11_ifc.py
# 2) tras crear el modulo sismico:
cd <plugin>/scripts && python3 sismico/run_all_sismo.py <proj> <ruta>/caso-11.ifc
```

> Recuerda: el **espectro EC8** y la **combinación modal** son biblioteca nueva;
> valida con el **método de fuerzas laterales** y el chequeo de mano (Fb≈929 kN). El
> análisis modal de PyNite puede requerir definir masas concentradas en los nodos de
> planta. No uses el pico singular como valor de diseño. Escribe el código por heredoc
> y valida con `ast.parse` (INC-04). Empaqueta el `.plugin` excluyendo
> `node_modules`/`__pycache__` (INC-05). Las herramientas de fichero (Read/Write/Edit)
> son la fuente de verdad de la carpeta del proyecto (el shell puede ver copias
> truncadas de ficheros preexistentes). Resultado de **predimensionado**, a revisar y
> firmar por técnico competente; marca `[confirmar AN]` los NDP (NCSE-02 / EC8 España).

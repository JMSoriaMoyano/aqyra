# Texto de inicio del Caso 8 — para pegar en un hilo nuevo

> Copia y pega el bloque siguiente al iniciar el hilo del Caso 8 en el proyecto
> **Estructurando**. Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **Caso 8** del programa de aprendizaje. Lee primero `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y `CHANGELOG-plugin.md`; luego `Casos-de-uso/caso-08-losa-cimentacion/ENUNCIADO.md` y trabaja sobre `caso-08.ifc` con el agente `ingeniero-estructurista`.

**Punto de partida:** plugin **motor-calculo-estructural v0.9.0** (en el caso 7 quedó resuelta la lectura ortodoxa de los muros —alzado/espesor/material de la `IfcStructuralSurfaceMember` y carga de cabeza de `IfcStructuralPointAction`—, la esbeltez EC2 por columna modelo `M_Ed=M0+M2` y la estabilidad EC7 DA-2\*). El parser genérico `scripts/laminas/ifc_to_model_3d.py` **ya lee** la losa como superficie (canto, material, esquinas), los 6 pilares como barras verticales (`tipo=pilar`, sección `IfcRectangleProfileDef`) y las cargas de cabeza están disponibles como `IfcStructuralPointAction` (igual que el caso 5) —verificado sobre `caso-08.ifc` (ver `validacion-IFC.txt`)—. Pero `scripts/cimentaciones/solver_raft.py` **todavía lee** la losa, los pilares y sus cargas de `Pset_Estructurando_Losa` / `_Pilar_*`.

**El modelo (sintético, realista):** un IFC ortodoxo con **una losa de cimentación (raft) C30/37, BX × LY = 6,0 × 4,0 m, canto 0,60 m** (`IfcStructuralSurfaceMember` horizontal) sobre la que descargan **6 pilares 0,40 × 0,40** (malla 3 × 2, x = {1,3,5}, y = {1,3}; `IfcStructuralCurveMember` verticales con `IfcRectangleProfileDef`), apoyada en un **lecho elástico de Winkler** (`ks = 40 MN/m³`, en los 4 nodos de esquina por `IfcBoundaryNodeCondition`, `TranslationalStiffnessZ = ks·(BX/2)·(LY/2)`; `R_d = 300 kPa`). **Cargas de cabeza** por `IfcStructuralPointAction`: esquina `N_G`=550 / `N_Q`=180 kN; central `N_G`=850 / `N_Q`=300 kN → **asiento diferencial**. R_d/ks y la geometría se mantienen como Pset (respaldo), igual que el caso 5/6/7.

**Trabajo del hilo:**

1. Añade a `cimentaciones/solver_raft.py` una **vía ortodoxa** (`parse_ortodoxo()` + `parse_auto()`, igual que `solver_zapata.py` del caso 5) que: (a) lea la **losa** (BX, LY, canto = `Thickness`, material) de la `IfcStructuralSurfaceMember`; (b) identifique los **pilares** (barras verticales) con su lado y pie (centro de carga); (c) baje la **carga de cabeza** (N_G, N_Q) de cada pilar de los `IfcStructuralPointAction`; (d) reconstruya el **lecho elástico ks** de la rigidez de los `IfcBoundaryNodeCondition` y tome **R_d** del `Pset_Estructurando_Suelo`; manteniendo el **Pset como respaldo**. Corrección **acotada**, sin romper los casos 2–7.

2. Resuelve la losa: placa Winkler multipilar → equilibrio (Σ reacciones = cabezas + p.p.), **terreno EC7** (presión media ≤ R_d, **asiento diferencial** centro–borde, picos como envolvente), **EC2** (flexión por bandas en las dos direcciones, **punzonamiento** de cada pilar, cortante, **fisuración con el φ dispuesto**, armadura principal en la **capa exterior**); aprovechamientos ≤ 1.

3. Valida contra los criterios del enunciado.

4. Registra: lección del caso 8 (raft ortodoxo multipilar; asiento diferencial; placa Winkler) y fila de métricas en `REPOSITORIO-aprendizaje.md`, corrección en `CHANGELOG-plugin.md`, sube el plugin a **0.9.1** (patch) o **0.10.0** (minor: lectura ortodoxa del raft) según el alcance, y reempaqueta el `.plugin` (excluyendo `node_modules`/`__pycache__`).

5. Prepara el caso 9: `caso-09-cimentacion-profunda/` con `ENUNCIADO.md`, generador del IFC ortodoxo (pilote + encepado + pantalla anclada; `pilotes` + `bielas-tirantes` + `muros-contencion`) y `validacion-IFC.txt`.

**Notas de método (casos 1–7):** escribe el código del plugin por heredoc en el sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); empaqueta el `.plugin` con el módulo `zipfile` de Python construyéndolo en `/tmp` como `.zip` con un nombre nuevo y copiándolo después con extensión `.plugin`; instala `ifcopenshell`/`PyNiteFEA`/`numpy`/`matplotlib` (pip `--break-system-packages`) y `docx` localmente (no global) para la memoria; **clasifica el sistema estructural antes de enrutar** (aquí una losa de cimentación multipilar → módulo `cimentaciones` raft, no zapata ni muro); cuidado con los módulos homónimos entre paquetes (`solver_muro`, `verificacion_muro`…) al cruzar imports; no uses el pico singular de presión/momento como esfuerzo de diseño; el cálculo con malla fina es lento en el sandbox (ejecuta solver / verificación / mapas por separado si el orquestador supera 45 s); resultado de **predimensionado**, a revisar y firmar por técnico competente, con los NDP marcados `[confirmar AN]`.

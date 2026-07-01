# Texto de inicio del Caso 7 — para pegar en un hilo nuevo

> Copia y pega el bloque siguiente al iniciar el hilo del Caso 7 en el proyecto
> **Estructurando**. Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **Caso 7** del programa de aprendizaje. Lee primero `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md` y `CHANGELOG-plugin.md`; luego `Casos-de-uso/caso-07-muros/ENUNCIADO.md` y trabaja sobre `caso-07.ifc` con el agente `ingeniero-estructurista`.

**Punto de partida:** plugin **motor-calculo-estructural v0.8.0** (en el caso 6 quedó resuelta la lectura ortodoxa de la viga mixta y se añadió IPE 360 al catálogo). El parser genérico `scripts/laminas/ifc_to_model_3d.py` **ya lee** los dos muros como superficies (canto, material, esquinas) de `IfcStructuralSurfaceMember`/`IfcFaceSurface` y tiene disponible la carga de cabeza como `IfcStructuralPointAction` (igual que el pilar del caso 5) —verificado sobre `caso-07.ifc` (ver `validacion-IFC.txt`)—. Pero `scripts/muros-contencion/solver_muro.py` y el muro de carga de `laminas` **todavía leen** alzado, espesor, material y cargas de `Pset_Estructurando_Muro` / `_MuroCarga` / `_Carga_Muro_q` (no de las entidades estándar).

**El modelo (sintético, realista):** un IFC ortodoxo con **dos elementos** que el agente debe **clasificar y enrutar** a módulos distintos (pauta multi-elemento de los casos 2–5):

1. **Muro de carga** → `laminas` (esbeltez EC2). Muro **C25/30, H = 3,0 m, t = 0,20 m**, faja de 1,0 m, arriostrado; `IfcStructuralSurfaceMember` vertical. **Carga vertical excéntrica de cabeza** por `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce`: `Ncab_G` = 250 kN/m, `Ncab_Q` = 120 kN/m, **e = 25 mm** → `MomentY = N·e` (6,25 y 3,0 kN·m). Apoyos: base empotrada `[T,T,T]`, coronación arriostrada `[T,T,F]`.
2. **Muro de contención en ménsula (T-invertida)** → `muros-contencion` (EC7 DA-2\*). Alzado **C30/37, Hm = 5,0 m, t = 0,40 m** (`IfcStructuralSurfaceMember` vertical); zapata canto 0,50 m, puntera 1,0 m, talón 2,0 m, **B = 3,40 m**, Df = 0,80 m. Terreno: relleno γ = 19 kN/m³, φ = 30°, c = 0, β = 0, δ = 20°, pasivo φ = 30° (fracción 0,5), base φ = 30° sin adherencia, **R_d = 300 kPa**, sin freático; **sobrecarga q = 10 kPa**. Geometría en T y parámetros del terreno se mantienen como Pset (`_Muro`, `_Terreno`, `_Carga_Muro_q`) porque **no hay entidad de análisis estándar** para ellos (igual que el R_d/k_s del caso 5 y los conectores/chapa del caso 6).

**Trabajo del hilo:**

1. Añade a `laminas` (muro de carga) y a `muros-contencion` una **vía ortodoxa** que: (a) tome **alzado, espesor (= `Thickness`) y material** de la `IfcStructuralSurfaceMember` vertical; (b) **clasifique** muro de carga vs muro de contención ménsula (por geometría y/o por la presencia de `Pset_Estructurando_Terreno`); (c) para el **muro de carga**, lea la **carga de cabeza** (N + M = N·e) de los `IfcStructuralPointAction`; (d) para el **muro de contención**, mantenga la **geometría T y el terreno** en Pset; manteniendo el **Pset como respaldo** (igual que casos 1–6). Corrección **acotada**, sin romper los IFC con Psets ni los casos 2–6.

2. Resuelve ambos muros:
   - **Muro de carga (EC2 esbeltez):** λ vs λ_lim; si λ > λ_lim, efectos de 2º orden (columna modelo / rigidez nominal, `M_Ed = M0 + M2`); comprobación de la sección (N-M) y armado vertical.
   - **Muro de contención (EC7 DA-2\*):** **vuelco** (EQU), **deslizamiento** (GEO, con pasivo parcial) y **hundimiento** (GEO, σ por área eficaz B′ de Meyerhof ≤ R_d), todos ≥ 1,0; sin despegue excesivo (e ≤ B/6 / núcleo central); **armado EC2** de alzado (ménsula, M en la base), puntera y talón, con fisuración con el φ realmente dispuesto y armadura principal en la **capa exterior** (lección casos 3–6). Diagramas: empujes, esfuerzos del alzado, presiones de contacto y N-M del muro de carga.

3. Valida contra los criterios del enunciado: modelo neutro (C25/30 y C30/37, 2 superficies verticales t = 0,20 y 0,40, carga de cabeza G/Q del muro de carga); coeficientes de seguridad ≥ 1,0; aprovechamientos ≤ 1.

4. Registra: lección del caso 7 (muros ortodoxos; esbeltez EC2; estabilidad EC7 DA-2\*) y fila de métricas en `REPOSITORIO-aprendizaje.md`, corrección en `CHANGELOG-plugin.md`, sube el plugin a **0.8.1** (patch) o **0.9.0** (minor: lectura ortodoxa de muros) según el alcance, y reempaqueta el `.plugin` (excluyendo `node_modules`/`__pycache__`).

5. Prepara el caso 8: `caso-08-losa-cimentacion/` con `ENUNCIADO.md`, generador del IFC ortodoxo (losa de cimentación / raft multipilar sobre lecho elástico, módulo `cimentaciones`) y `validacion-IFC.txt`.

**Notas de método (casos 1–6):** escribe el código del plugin por heredoc en el sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); empaqueta el `.plugin` con el módulo `zipfile` de Python construyéndolo en `/tmp` como `.zip` con un nombre nuevo y copiándolo después con extensión `.plugin`; instala `ifcopenshell`/`PyNiteFEA`/`numpy`/`matplotlib` (pip `--break-system-packages`) y `docx` localmente (no global) para la memoria; **clasifica el sistema estructural antes de enrutar** (aquí dos elementos: muro de carga a esbeltez EC2 y muro de contención a estabilidad EC7, no losa ni viga); recuerda que `add_member_dist_load(x1,x2)` de PyNite usa coordenadas **locales** al elemento; no uses el pico singular como esfuerzo de diseño; resultado de **predimensionado**, a revisar y firmar por técnico competente, con los NDP marcados `[confirmar AN]`. El cálculo con malla fina es lento en el sandbox (ejecuta solver / verificación / mapas por separado si el orquestador supera el límite de 45 s).

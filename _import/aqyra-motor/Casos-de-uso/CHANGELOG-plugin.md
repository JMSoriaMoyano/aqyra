# CHANGELOG — motor-calculo-estructural.plugin

Registro de versiones y correcciones del plugin. Formato SemVer. Cada hilo que toque el
código del motor añade aquí una entrada y reempaqueta el `.plugin`.

## [0.23.0] — 2026-06-22
- **NÚCLEO TRANSVERSAL: grafo de red (nodos+tramos) + utilidades IFC compartidas
  (PT 4.1, Ola 4 — hueco H1; resuelve la decisión abierta nº4)** — extracción a un
  módulo de núcleo, reutilizable y **agnóstico al solver**, de la lógica que estaba
  embebida en el lado de estructuras, para que una disciplina nueva (instalaciones)
  "enchufe sin tocar el núcleo". **Cambio estructural sin cambio funcional: regresión
  byte a byte de la serie R.**
  - `scripts/nucleo/ifc_utils.py` (NUEVO): utilidades de lectura IFC que estaban
    **duplicadas** por parser → `psets`, `length_scale` (factor de unidades del
    `IfcUnitAssignment`, mm→m), `pset_value` (lector puntual; generaliza
    `_snap_tol_from_ifc`, con el Pset como parámetro) y álgebra homogénea 4×4
    (`matmul`/`apply`/`to_list4`/`ident4`).
  - `scripts/nucleo/grafo_red.py` (NUEVO): grafo de red nodos+tramos —
    `RegistroNodos` (fusión por tolerancia/snap, representante "primero añadido"),
    `proyeccion`/`punto_en_segmento`/`bbox_xy`, `cortes_por_interseccion` (troceo
    T/X con offset), `ordenar_segmento` y `filtrar_componentes_desconectadas`
    (union-find **genérico** vía predicado `es_ancla`). API de alto nivel
    `construir_grafo(segmentos, tol)` como **gancho H2/MEP** (un futuro
    `ifc_to_model_mep.py` la alimenta desde `IfcDistributionPort`/`IfcRelConnectsPorts`
    sin tocar el núcleo).
  - `scripts/nucleo/test_grafo_red.py` (NUEVO): micro-test autocontenido
    (intersección/snap/troceo T/X/union-find + `construir_grafo`); exit ≠ 0 si falla.
    `scripts/nucleo/README.md` documenta la mini-API.
  - **Refactor (adaptador fino, sin reescribir):** `puente_analitico/puente.py`
    (921→833 ln) deja de definir cuerpos propios de `_psets`/`_length_scale`/`_Nodos`/
    `_proyeccion`/`_punto_en_segmento`/`_bbox_xy`/`_PREFIJO_SI` y los **delega** al
    núcleo; `barras/ifc_to_model.py` y `laminas/ifc_to_model_3d.py` consumen
    `nucleo.psets`. El **solver y la verificación no se tocan**.
  - **Regresión verificada (doble, una independiente a ciegas):** R1–R5 reproducen el
    `modelo_neutro.json` de v0.22.1 **byte a byte**; casos 1/5/7/10 **CUMPLEN**
    (caso 10: 4/4 subsistemas). `ast.parse` de los **129** `.py` → **0 errores**;
    micro-test del núcleo OK. Reempaquetado **acumulativo** desde v0.22.1.

## [0.22.1] — 2026-06-22
- **CORRECCIÓN DE EMPAQUETADO (PT 1.6, verificación de la Ola 1) — sin cambios
  funcionales.** La auditoría de cierre de la Ola 1 detectó que el reempaquetado
  **acumulativo** de v0.22.0 **truncó 8 módulos preexistentes** que solo debían
  arrastrarse sin cambios (manifestación del *hazard* INC-04). Los módulos del caso 15
  (`sismico/*`, `run_all_edificio.py`, `clasificador.py`, `laminas/ifc_to_model_3d.py`)
  estaban intactos. Módulos truncados restaurados **íntegros desde v0.21.0** (cada uno es
  prefijo exacto del completo → truncado puro, sin pérdida de ediciones):
  `puente_analitico/puente.py` (921 ln; era 344), `cimentaciones/solver_raft.py`,
  `cimentaciones/solver_zapata.py`, `cimentaciones/verificacion_raft.py`,
  `cimentaciones/run_all_raft.py`, `cimentaciones/plots_raft.py`,
  `barras/ifc_to_model.py` (con `parse()`), `barras/perfiles_db.py`.
  - **Impacto:** v0.22.0 fallaba en **instalación limpia** (5 módulos con SyntaxError al
    importar: raft/zapata/verificacion_raft/run_all_raft/puente; 3 más truncados que
    parseaban por azar). Los **resultados de los casos no se ven afectados** (se ejecutaron
    desde copias de trabajo completas), pero el `.plugin` distribuible sí.
  - **Verificación post-empaquetado** (institucionalizar, hueco H6): re-extraer el ZIP y
    comprobar `ast.parse` de los **126** `.py` (**0 errores**), salto de línea final en
    todos, recuento de módulos y contraste de tamaños contra la versión previa. **`ast.parse`
    por sí solo NO basta** (3 de 8 truncados parseaban). Reempaquetado excluyendo
    `node_modules`/`__pycache__`. **Distribuir v0.22.1, no v0.22.0.**

## [0.22.0] — 2026-06-22
- **NÚCLEO DE PANTALLAS ACOPLADAS + integración del SÍSMICO EC8 en el orquestador
  de edificio (caso 15, PT 1.5 de la Ola 1 — CIERRA la estabilización lateral de
  edificación)** — la familia sísmica (módulo `sismico/` + biblioteca EC8 del caso
  11, pantalla aislada) se generaliza del voladizo (stick, 1 GdL/planta) al
  **núcleo**: varias pantallas en planta acopladas, **diafragma rígido con 3 GdL
  por planta (ux, uy, θz)**, rigidez a torsión, reparto de cortante por
  rigidez + excentricidad (CR vs CM) y torsión accidental, vigas de acoplamiento
  DCM, y el **caso sísmico aplicado en `run_all_edificio`**. Módulos NUEVOS en
  `sismico/`, sin tocar el caso 11 ni el resto de tipologías. Reempaquetado
  **acumulativo** partiendo del v0.21.0 instalado (preserva `sismico/` del caso 11,
  `pretensado/`, `clasificador.py`/`run_all_edificio.py` y todo `puente_analitico/`
  R1–R5) → **v0.22.0**.
  - `scripts/sismico/nucleo.py` (NUEVO, biblioteca): ensamblaje a **3 GdL/planta**
    (diafragma rígido) reutilizando `ec8.stick_lateral_stiffness` por pantalla
    (flexión Euler-Bernoulli + cortante Timoshenko) en su dirección (X/Y) y
    posición en planta (matriz de compatibilidad `T`, lever
    `r = -(yc-CMy)·ex + (xc-CMx)·ey`); **centro de rigidez CR**, **centro de masa
    CM**, **excentricidad estática e0**; **modal** (`scipy.eigh`) con masas modales
    efectivas en X/Y; **reparto de cortante** por componente directa + torsional
    (CR≠CM, resuelto en el sistema 3 GdL) + **torsión accidental ±0,05·L** (EC8
    §4.3.2, envolvente de signos); **pareja de muros acoplados** como plano-pórtico
    2D (Y-Z) con **brazos rígidos** + **dintel con flexibilidad de cortante**
    (`Ib_eff = Ib/(1+12·E·Ib/(G·Avb·ln²))`) → **condensación estática** del par a un
    elemento Y (el acoplamiento entra en la rigidez global), cortante del dintel por
    planta, **axil de acoplamiento** N(z) y **grado de acoplamiento DoC**; derivas
    globales en el borde más flexible.
  - `scripts/sismico/solver_nucleo.py` (NUEVO): parser ortodoxo del núcleo —
    reutiliza `laminas/ifc_to_model_3d` (ruta explícita), lee VARIAS
    `IfcStructuralSurfaceMember` verticales (Lw/tw/posición/dirección por la normal
    del plano + Pset de rol/acoplamiento), las masas de planta en los nodos de
    diafragma (CM) y los `Pset_Estructurando_Sismo`/`_Nucleo`. **Extiende** el modelo
    neutro con claves NUEVAS (`pantallas[]`, `dinteles`, `diafragma`) sin alterar las
    existentes (contrato C1).
  - `scripts/sismico/verificacion_nucleo.py` (NUEVO): reutiliza
    `verificacion_sismo` (cortante de alma, elementos de borde §5.4.3.4, N-M, deriva
    §4.4.3.2) por pantalla y añade la **viga de acoplamiento DCM** (EC8 §5.5.3.5:
    `ln/h<3` → armadura DIAGONAL; aplastamiento de biela; diseño por capacidad
    `γ_Rd`). El machón a barlovento entra en **tracción neta** por el acoplamiento:
    la armadura de borde se dimensiona con el axil real; el N-M con el gravitatorio.
  - `scripts/sismico/edificio_sismo.py` (NUEVO): aplica el sismo al edificio —
    **deriva masas de planta** (explícitas del IFC o `G + ψ2·Q`), monta el modelo
    lateral, **distribuye el cortante** y **verifica derivas globales**, con
    **combinación sísmica EC0 §6.4.3.4** (`Ed = E + ΣGk + Σψ2·Qk`, γ=1,0).
  - `scripts/run_all_edificio.py` (AMPLIADO retrocompatible): nueva **etapa `[E]`
    sísmica** (auto si hay `Pset_Estructurando_Sismo`, o flag `--sismo`) que ejecuta
    `edificio_sismo` en subproceso aislado y consolida `_caso_sismico_EC8` en el
    índice del edificio. El flujo gravitatorio (casos 1–10) queda intacto.
  - `scripts/sismico/run_all_nucleo.py` + `plots_nucleo.py` +
    `generate_memoria_nucleo.py` (NUEVOS): orquestador end-to-end, 6 diagramas
    (espectro, planta CR/CM, reparto de cortante, vigas de acoplamiento, deriva, N-M)
    y memoria Word con la estructura del contrato C3 (7 apartados, citas y
    `[confirmar AN]`).
- Validado con el **caso 15** (IFC ortodoxo: núcleo en U abierto C30/37, 2 machones
  de alma Lw=2,0 acoplados + 2 alas Lw=4,0, tw=0,30, 6 plantas×3,0=18 m, ΣW=4.000 kN;
  q=3,6 DCM muros acoplados, ag=0,20 g, suelo C, espectro tipo 1, λ=0,85; torre
  compacta 8×8):
  - **Espectro**: Sd(meseta)=ag·S·2,5/q=**0,1597 g** ✓.
  - **Modal 3 GdL/planta**: **T1x=0,305 s, T1y=0,390 s** (en meseta TB≤T≤TC);
    **ΣM_eff,X=ΣM_eff,Y=100 %**; **CR(3,40;4,00) vs CM(4,00;4,00) → e0x=0,60 m**.
  - **Cortante basal**: fuerzas laterales Fb_X=Fb_Y=**543 kN** (equilibrio Fb=ΣF_i
    **0,000 %**); contraste **modal SRSS** 454/368 kN. **Reparto por pantalla**:
    suma = Fb por dirección (**error 0,000 %**); sismo Y → machones directo + alas
    par torsional ±, sismo X → alas directo; torsión accidental ±0,05·L en envolvente.
  - **Muros acoplados**: **DoC=0,72** (acoplamiento fuerte), V_dintel,máx=346 kN,
    N_acopl,base=1.441 kN; dintel ln/h=2,0 → **armadura DIAGONAL** (As_d=11,8 cm²/grupo,
    α=24°, aprov. 0,22); **machón a barlovento en tracción neta −775 kN**.
  - **Verificación**: alas 0,62, machón comprimido 0,72, machón traccionado 0,33,
    dintel 0,22, **deriva 0,15** (0,225 %·h ≤ 0,75 %·h). **Veredicto CUMPLE; aprov.
    máx 0,72 (≤1)**. Picos como envolvente.
  - **Integración**: `run_all_edificio --sismo` aplica el caso sísmico (deriva masas,
    monta el modelo lateral, reparte el cortante, verifica derivas, EC0 §6.4.3.4) →
    `_caso_sismico_EC8 = CUMPLE`. **Caso 11 sin regresión** (T1=0,408 s, Fb=929 kN,
    borde 0,97). Memoria Word (6 diagramas) + `modelo_neutro.json` +
    `verificacion_nucleo.json`. Plugin **v0.22.0** (minor: núcleo + sísmico en
    orquestador). `[confirmar AN]` q (muros acoplados q0·α_u/α_1), amplificación de
    cortante DCM, γ_Rd del dintel, ν y límite de deriva, ψ2 (NCSE-02 / EC8 / EC0 NDP
    España; vigilar NCSR-22). **Predimensionado, a revisar y firmar por técnico
    competente. Cierra la estabilización lateral de edificación (Ola 1).**

## [0.21.0] — 2026-06-22
- **Puente IFC físico → analítico ENDURECIDO ante geometría "real-sucia" de un
  exportador concreto (caso R5, quinto y último peldaño de la Dirección 2 —
  CIERRE de INC-07 y de la serie R)** — el módulo `puente_analitico/` (que en
  R1 derivaba barras, en R2 superficies horizontales, en R3 superficies
  verticales + cimientos y en R4 el edificio completo, todo desde IFC físicos
  **limpios**) se endurece para limpiar un IFC físico **real-sucio**: ejes no
  centrados (offset por *cardinal point*), barras que no se cortan en el nudo
  (huecos/solapes), elementos no estructurales / no conectados, nomenclatura de
  exportador y unidades no-metro. **Sin tocar los solvers ni los orquestadores**
  (`run_all_real.py` se reutiliza SIN CAMBIOS): toda la robustez va en
  `puente.py` (+ alias en `perfiles_db.py`). **R1–R4 quedan idénticos** en IFC
  limpio (tolerancia por defecto 1 mm + sin offset + escala 1.0 → comportamiento
  exactamente igual; verificado por regresión byte a byte del modelo neutro).
  Reempaquetado **acumulativo** partiendo del v0.20.0 instalado (preserva
  `sismico/` + `pretensado/` —incl. continua/hiperestática del caso 14— +
  `clasificador.py`/`run_all_edificio.py` + todo el `puente_analitico/` de
  R1+R2+R3+R4 y añade encima la robustez de R5). Versión coordinada con la
  Dirección 1: R4 tomó 0.19.0; el caso 14 (pretensado continua) tomó 0.20.0
  durante este hilo (carrera de escritura detectada y resuelta) → R5 = **0.21.0**.
  - `scripts/puente_analitico/puente.py` (ENDURECIDO, retrocompatible):
    - **(a) Recuperación del eje analítico (offset eje físico↔analítico).**
      `_axis_recovery()` lee el **`CardinalPoint`** del `IfcMaterialProfileSetUsage`
      y, con (b,h) del perfil, calcula el offset del eje de referencia al
      **centroide** sobre los ejes locales del placement (`get_local_placement`),
      desplazando el eje físico al **baricéntrico** y guardando la **excentricidad**
      por barra (`limpieza.excentricidades`). `CardinalPoint=5`/ausente → offset
      nulo → R1–R4 intactos.
    - **(b) Grafo de nudos robusto.** Tolerancia de snap **parametrizable**
      (`Pset_Estructurando_Puente.Snap_tol_m`; por defecto `TOL=1 mm` = R1–R4):
      fusión de extremos próximos con registro de **huecos/solapes puenteados**,
      y **troceo en cruces T/X con offset** proyectando el punto de corte sobre la
      directriz del pasante (margen paramétrico relativo a la longitud, no
      absoluto). `_Nodos` registra cada fusión y su salto.
    - **(c) Filtrado de no-estructurales / no-conectados.** Solo se admiten las
      clases estructurales; el resto (`IfcRailing`/`IfcCovering`/
      `IfcBuildingElementProxy`…) se avisa y descarta. `_filtrar_desconectadas()`
      (union-find) elimina las componentes sin nudo apoyado (barras sueltas).
      **Ambos solo se activan en IFC real-sucio** (`snap_tol > TOL`), de modo que
      los subsistemas legítimamente separados de R4 no se filtran.
    - **(d) Alias de perfiles** (`perfiles_db._norm_name`): Euronorm de exportador
      `HE 200 B`/`HE200B` → `HEB 200`; `props_from_profile_def` devuelve el nombre
      **normalizado** de catálogo (para que el clasificador reconozca el perfil en I).
    - **(e) Factor de unidades** (`_length_scale`): respeta el `IfcUnitAssignment`
      (MILLIMETRE → escala 1e-3 en coordenadas, longitudes y dimensiones de sección;
      unidades de conversión soportadas). METRE → 1.0 → R1–R4 intactos.
    - El modelo neutro lleva ahora `limpieza` (escala, snap_tol, nudos fusionados,
      huecos puenteados, cruces troceados, elementos filtrados, excentricidades).
  - `scripts/puente_analitico/generate_memoria_real_r5.py` (NUEVO): memoria Word
    (python-docx) con la sección de **robustez del puente** (offsets eje
    físico↔analítico, grafo de nudos con tolerancia, filtrado, alias, unidades),
    la métrica de recuperación y la reproducción del caso limpio.
- Validación (caso R5, geometría = caso 1 / R1; IFC físico IFC4 en **milímetro**):
  del IFC real-sucio (2 `IfcColumn` "HE 200 B" + 1 `IfcBeam` "IPE330" con
  `CardinalPoint` 1/3/8, solape de 40 mm en pilares, hueco de 30 mm en el dintel,
  + `IfcRailing` + `IfcBuildingElementProxy` + `IfcBeam` suelto), el parser crudo
  leería **8 nudos / 4 barras** (mm, sin recuperar, con la barra suelta). Tras la
  **limpieza** el puente entrega **4 nudos / 3 barras** = el modelo limpio R1:
  escala 1e-3 aplicada, **excentricidades recuperadas** C1/C2 **0,141 m** (CP 1/3),
  B1 **0,165 m** (CP 8), **2 huecos/solapes puenteados** (0,05 m), **3 elementos
  filtrados** (railing + proxy + viga suelta), troceo T/X validado en micro-test
  (pasante 0–6 m + montante con 50 mm de offset → 2 segmentos + montante enganchado
  en el nudo proyectado). Enrutado a `barras` (EC3) → **reacción 93,60 kN/apoyo
  (EXACTA)**, horizontales ±12,01 kN balanceadas, **HEB 200 31,8 %**, **IPE 330
  44,8 %** (las diferencias frente a 32,0 / 44,6 % son la idealización del solape
  de 40 mm en cabeza —altura recuperada 4,04 m—, aceptada y documentada como en
  R1–R4; la reacción es exacta porque el equilibrio vertical no depende de la
  altura), validación cruzada PyNite vs anaStruct **CONFORME**, equilibrio ~0 %.
  **CUMPLE. Reproduce el caso limpio a pesar de la suciedad.** Regresión: R1
  (32,0/44,6 %) y R4 (modelo neutro idéntico) sin cambio. Memoria Word +
  `modelo_neutro.json` (con `limpieza`) + `clasificacion.json` + `verificacion.json`
  + diagramas + `validacion-IFC.txt`. **Cierre de INC-07 y de la serie R /
  Dirección 2.** Predimensionado, a revisar y firmar por técnico competente; NDP
  marcados `[confirmar AN]` (tolerancia de snap 60 mm, criterio de offset por
  cardinal point).

## [0.20.0] — 2026-06-22
- **Viga pretensada HIPERESTÁTICA (continua, 2 vanos) — momentos secundarios,
  línea de presiones/concordancia, redistribución y ELU con el momento secundario
  (caso 14, cuarto peldaño de la 2ª tanda — lleva el PRETENSADO a estructuras
  hiperestáticas)** — la tipología de pretensado (EC2 §5.10, caso 12 isostática 1D
  + caso 13 losa postesada 2D) se generaliza a la **viga continua**: por primera
  vez el motor calcula los **momentos hiperestáticos (secundarios) de pretensado**
  M_sec = M_p,tot − M₁, la **línea de presiones** e_p = M_p,tot/P, la
  **concordancia**, la **redistribución §5.5** y el **ELU con el momento secundario
  como acción (γ_P = 1,0, §5.10.8)**. Módulo NUEVO en `pretensado/`, sin tocar los
  casos 1–13 ni R1–R4. Reempaquetado **acumulativo** partiendo del v0.19.0
  instalado (preserva `sismico/`, `pretensado/` casos 12+13 y todo el
  `puente_analitico/` R1–R4). Versión coordinada: R4 tomó 0.19.0 → caso 14 = **0.20.0**.
  - `scripts/pretensado/ec2_continua.py` (NUEVO, biblioteca): trazado parabólico
    **por vano** e(x) (parábola con drape sobre la cuerda de excentricidades de
    apoyo, e'' = −8a/L² → **carga equivalente uniforme** w_p = 8·P·a/L²); **FEM de
    viga continua** Euler-Bernoulli (2 GDL/nodo, malla fina) para los esfuerzos de
    las cargas externas y de las cargas equivalentes → **M_p,tot(x)**; **M₁(x) =
    −P·e(x)** (primario, estructura liberada); **M_sec = M_p,tot − M₁** (secundario,
    lineal entre apoyos y nulo en los extremos); **método de las fuerzas** (1
    incógnita hiperestática = reacción del apoyo central) como contraste del FEM;
    **línea de presiones** e_p = M_p,tot/P = e + M_sec/P.
  - `scripts/pretensado/verificacion_continua.py` (NUEVO): **tensiones por fibra con
    M_sec** (transferencia con M_sec escalado a P0, cuasipermanente, rara) en las
    secciones críticas (apoyo central hogging / centro de vano sagging); **ELU de
    flexión por fibras** genérico sagging/hogging con el **secundario como acción
    γ_P = 1,0** (M_Ed = γ_G·M_g + γ_Q·M_q + 1,0·M_sec, sin doble cómputo del
    primario, que va en la resistencia); **redistribución §5.5** (δ_min = 0,44 +
    1,25·x_u/d, fck ≤ 50).
  - `scripts/pretensado/solver_pretensado_continua.py` (NUEVO): parser ortodoxo de
    la viga continua (sección `IfcRectangleProfileDef` vía `IfcMaterialProfileSet`
    C40/50, 3 apoyos `IfcStructuralPointConnection`+`IfcBoundaryNodeCondition`, 2
    `IfcStructuralCurveMember` → 2 vanos, cargas g2/q ortodoxas, trazado por vano
    del `Pset_Estructurando_Pretensado`). g0 = A·25 lo añade el solver.
  - `scripts/pretensado/run_all_pretensado_continua.py` (NUEVO): orquestador
    end-to-end (IFC → FEM externas+pretensado → M₁/M_p,tot/M_sec FEM vs método de
    las fuerzas → línea de presiones/concordancia → tensiones por fibra con M_sec →
    ELU con secundario en apoyo y vano → redistribución → flecha → JSON). Patrón de
    sobrecarga alterna por vano para el sagging máximo. `plots_pretensado_continua.py`
    (8 diagramas) y `generate_memoria_pretensado_continua.py` (memoria Word).
- Validado con el **caso 14** (viga C40/50 b=0,50×h=1,30, 2 vanos de L=20 m,
  3 apoyos; 14×Y1860S7 Ap=2.100 mm², trazado parabólico e_vano=+0,30 / e_apoyo
  central=−0,30, drape a=0,45; g2=5,0, q=12,0 kN/m, ψ₂=0,3):
  - **Balance**: w_p = 8·P·a/L² = **21,09 kN/m** equilibra la permanente g0+g2 =
    21,25 (residual **−0,74 %**). σp0/fpk = **0,720**, σp,∞/fpk = **0,600**
    (pérdidas diferidas **16,7 %**). *(Se refinaron las excentricidades del enunciado
    de ±0,50 a ±0,30 para que el balance equilibre la permanente; con ±0,50 el drape
    sería 0,75 y el pretensado sobre-equilibraría.)*
  - **Esfuerzos externos** (FEM = chequeo de mano exacto): apoyo central ELU
    **−2.334 kN·m**, vano ELU **+1.313** (ambos vanos cargados); cuasiperm apoyo
    −1.242, rara −1.662.
  - **Momentos de pretensado (LO NUEVO)**: M₁ apoyo +703, M_p,tot apoyo +1.055,
    **M_sec apoyo central = +351,5 kN·m**; **M_sec lineal (R² = 1,000000) y nula en
    los extremos** (0,00/0,00); **FEM vs método de las fuerzas Δ = 0,000 %**;
    identidad M_p,tot = M₁ + M_sec (error 5,8·10⁻¹¹). **Línea de presiones**: e_p
    apoyo = +0,15 m → tendón **NO concordante** (desviación M_sec/P = 0,15 m).
  - **Tensiones por fibra con M_sec**: apoyo transferencia todo comprimido (−7,54/
    −1,11), rara top **+0,71 < fctm = 3,5** (tracción controlada); vano todo
    comprimido en todos los estados.
  - **ELU con secundario (γ_P = 1,0)**: apoyo central M_Ed = −2.334 + 1,0·(+352) =
    **−1.983 kN·m** (el secundario **ALIVIA** el hogging), M_Rd = 2.509 (fibras,
    hogging, tendón activo a f_pd) → **u = 0,79**, x/d = 0,296; centro de vano
    M_Ed = 1.614 (patrón alterno + M_sec), M_Rd = 2.537 → **u = 0,64**, x/d = 0,293.
  - **Redistribución §5.5**: x/d = 0,296 → δ_min = 0,81 (hasta 19 % de reducción del
    hogging), opcional (u < 1, no aplicada). **Flecha** residual 1,02 mm ≪ L/250 =
    80 mm (u = 0,01). **Veredicto: CUMPLE; aprov. máx 0,79 (≤ 1); picos como
    envolvente.** Memoria Word (9 diagramas embebidos) + `modelo_neutro.json` +
    `verificacion_pretensado_continua.json`. Plugin **v0.20.0** (minor: viga
    pretensada hiperestática + momentos secundarios + línea de presiones/
    concordancia + redistribución + ELU con momento secundario). `[confirmar AN]`
    coeficientes de pérdidas, límites del acero activo, μ/k, δ (EC2 §5.10/§5.5 NDP
    España). **Predimensionado, a revisar y firmar por técnico competente.**

## [0.19.0] — 2026-06-22
- **Puente IFC físico → analítico de EDIFICIO COMPLETO multi-elemento (caso R4,
  cuarto peldaño de la Dirección 2 — el "caso 10 real")** — el módulo
  `puente_analitico/` (que en R1 derivaba barras, en R2 superficies horizontales,
  en R3 superficies verticales + cimientos) ahora deriva **TODOS los tipos a la vez**
  de un **único IFC físico por plantas** y un **clasificador/enrutador
  multi-elemento** enruta CADA elemento del modelo neutro a su módulo. Cierra la
  tubería **físico → analítico → cálculo** de extremo a extremo: es la versión
  física del caso 10 (que partía de un IFC ortodoxo). **Sin tocar `puente.py` ni
  los solvers** (se reutilizan `barras`, `mixtas/solver_mixta`, `laminas/solver_muro`
  y `cimentaciones/solver_zapata` construyendo los dicts `model` desde el modelo
  neutro + Psets, patrón R2/R3). Reempaquetado **acumulativo** partiendo del v0.18.0
  instalado (preserva `sismico/` + `pretensado/` + `clasificador.py`/
  `run_all_edificio.py` + todo el `puente_analitico/` de R1+R2+R3 y añade encima los
  ficheros de R4). Versión coordinada: R3 tomó 0.18.0; ningún caso de la Dirección 1
  había tomado 0.19.0 → R4 = **0.19.0**.
  - `scripts/puente_analitico/run_all_real_edificio.py` (NUEVO): orquestador
    end-to-end del edificio físico. `clasificar_neutro_edificio(model, ifc)` itera
    TODAS las barras y superficies del modelo neutro DERIVADO por el puente y enruta
    cada elemento por **geometría + sección + material + lecho/carga de cabeza +
    asociaciones**: barra de acero I (pórtico) → `barras` EC3; viga de acero I
    **asociada a losa** (de `vigas_asociadas` del puente) → `mixtas` EC4; superficie
    vertical de hormigón → `laminas/solver_muro` EC2 §5.8.8; superficie horizontal de
    hormigón con lecho (`Pset_Estructurando_Suelo` / `IfcFooting`) → `cimentaciones/
    solver_zapata` EC7+EC2; pilar de hormigón **sobre zapata** (pie común) → cadena
    pilar→cimiento. Constructores `build_model_portico/_mixta/_muro/_zapata` arman los
    dicts `model` desde neutro + Psets; la zapata incluye el **predimensionado** (si
    σ_ef por área eficaz > R_d, amplía la zapata cuadrada centrada en el pilar, como el
    caso 10). Cada subsistema se ejecuta en **subproceso aislado** (re-invoca el script
    con `--solo`) para evitar el choque de módulos homónimos `solver_*`/`combinaciones`/
    `plots_*`/`verificacion_*` entre paquetes. Consolida `resumen_edificio.json`.
  - `scripts/puente_analitico/generate_memoria_real_edificio.py` (NUEVO): memoria Word
    (python-docx) integrada — derivación de TODO el edificio desde un IFC físico, grafo
    de nudos multi-planta, clasificación/enrutado multi-elemento, los 4 subsistemas y el
    índice del edificio, con diagramas embebidos.
- Validación (caso R4, geometría = caso 10): del **único IFC físico** (3 `IfcColumn` +
  2 `IfcBeam` + 1 `IfcSlab` + 1 `IfcWall` + 1 `IfcFooting`, sin entidades de análisis)
  el puente deriva **8 nudos + 5 barras + 3 superficies**, con losa↔viga `{B2→Mixta_Losa}`
  y pilar↔zapata `{C3→Zapata_Aislada}`. Los **4 subsistemas resueltos por los módulos
  existentes**: **Pórtico** HEB 240 N-M **22,9 %** / IPE 360 **30,5 %** (reacción **93,60
  kN/apoyo**, horizontales balanceadas, validación cruzada PyNite vs anaStruct CONFORME);
  **Mixta** IPE 400 + losa C25/30 b_eff 2,10, **M_Ed=333 kN·m**, **η=0,66**, M_Rd=522 (u
  **64 %**), flecha 53 % *(la rutina EC4 vigente sitúa el PNA en el ala superior —verificado
  a mano— dando M_Rd=522; M_Ed y η coinciden EXACTO con el caso 10; la diferencia de M_Rd
  frente al 450 histórico es un refinamiento del motor, no del puente)*; **Muro** C30/37
  λ=52 esbelto, M_Ed=M0Ed+M2≈30 kN·m/m, **N-M 45 %**, **φ10/200 c/cara**, equilibrio
  vertical 0,000 %; **Cimentación** zapata **ampliada 2,50→2,55** (predim.), **σ_ef
  245/250 kPa (98 %)**, e=0,116 < B/6=0,425 (sin despegue), punz 14 %, cortante 52 %,
  fisuración φ12 w_k=0,278 mm (93 %), equilibrio del lecho 0,000 %. **Los 4 subsistemas
  CUMPLEN; aprovechamientos ≤ 1; picos como envolvente.** Reproduce el caso 10 desde un
  IFC FÍSICO. Memoria Word integrada + `modelo_neutro.json`/`clasificacion.json`/
  `resumen_edificio.json`/`verificacion_*.json` + diagramas. Predimensionado, a revisar y
  firmar por técnico competente.

## [0.18.0] — 2026-06-22
- **Puente IFC físico → analítico de superficies VERTICALES + cimientos (caso R3,
  tercer peldaño de la Dirección 2 — lleva el puente a muros y zapatas físicos)** —
  `puente_analitico/` (que en R1 derivaba barras y en R2 superficies horizontales,
  losas `IfcSlab`) se amplía a **superficies verticales** (`IfcWall`, plano medio) y
  a **cimientos** (`IfcFooting`, footprint + canto). Ampliación **acotada y
  retrocompatible**: `IfcSlab` sigue saliendo horizontal y, sin walls/footings, el
  comportamiento R1/R2 es idéntico. **Sin tocar los solvers** de muro/zapata (se
  reutilizan llamando `solver_muro.solve`+`verificacion_muro` y
  `solver_zapata.solve`+`verificacion_zapata.verificar` con dicts `model`
  construidos desde el modelo neutro + Psets, igual que R2). Reempaquetado
  **acumulativo** partiendo del v0.17.0 instalado.
  - `scripts/puente_analitico/puente.py` (AMPLIADO): `_superficie(element, clase,
    espesor_layer)` **clasifica la superficie por la NORMAL del plano medio**: para
    un `IfcWall` extruido en +Z cuya huella es «alargada y fina» (un lado ≤ 2,5·
    espesor del `IfcMaterialLayerSet`) genera un **plano medio VERTICAL** (4 esquinas
    de base a cabeza, centradas en el lado fino → longitud L_w × altura H), no una
    losa horizontal degenerada a media altura; `IfcSlab`/`IfcFooting` siguen
    horizontales (footprint + canto). Cada superficie del modelo neutro lleva ahora
    `orientacion` ("vertical"/"horizontal"), `normal`, `altura`, `largo`. **Cadena
    muro↔cimiento** (`zapata_asociada`/`muros_asociados`) por proximidad en planta
    (centro del muro dentro de la huella) + cota (pie del muro ≈ cara superior de la
    zapata), análoga a pilar↔zapata del caso 10. Carga de cabeza del muro
    (`N_G`/`N_Q` + excentricidad e → M=N·e) leída del `Pset_Estructurando_CargaHipotesis`
    y estructurada en la superficie. Guarda contra modelo sin nudos (R3 solo tiene
    superficies).
  - `scripts/puente_analitico/run_all_real_muro_zapata.py` (NUEVO): orquestador
    end-to-end IFC físico → puente → `clasificar_neutro` (muro vertical hormigón →
    láminas/solver_muro; superficie horizontal hormigón con lecho → cimentaciones/
    solver_zapata; cadena muro→cimiento) → construye los dicts `model` de muro y
    zapata desde neutro+Psets → `solver_muro.solve()`+`verificacion_muro.verificar()`
    y `solver_zapata.solve()`+`verificacion_zapata.verificar()` → equilibrios →
    diagramas (reutiliza `plots_muro.generar`/`diagrama_NM` y `plots_zapata.generar`).
    Aísla los **módulos homónimos** entre paquetes cargándolos por **ruta explícita
    con salvaguarda de `sys.path`** (lección caso 7/11). **NO** usa
    `parse_ortodoxo`/`run_muro_carga`/`run_all_zapata` (releen entidades de análisis
    que el IFC físico no tiene).
  - `scripts/puente_analitico/generate_memoria_real_muro_zapata.py` (NUEVO): memoria
    Word (python-docx) con clasificación por orientación, plano medio del muro +
    huella/canto de la zapata + espesor del `IfcMaterialLayerSet`, cadena
    muro→cimiento, resultados de muro (caso 7) y zapata (caso 5), equilibrios y
    diagramas embebidos.
- Validación (caso R3, geometría = casos 7 y 5): **muro** C25/30 H=3,0 t=0,20 faja
  1,0 m, carga de cabeza G=250/Q=120 kN/m e=25 mm → λ=52 > λ_lim ⇒ ESBELTO, M_Ed =
  M0Ed+M2 ≈ 31,3 kN·m/m, φ10/200 c/cara, N-M ≈ 47 %, equilibrio vertical ELU ~0,000 %;
  **zapata** C30/37 2,5×2,5 canto 0,60 sobre lecho k_s=40 MN/m³ R_d=250 kPa, bajada
  N_G=700/N_Q=250 kN + M_G=80 kN·m → EC7 σ_ef ≤ R_d (sin despegue, e<B/6), EC2
  flexión/punzonamiento/fisuración, equilibrio del lecho ~0 %. Reproduce los casos 7
  y 5. **Aprovechamientos ≤ 1.** Predimensionado, a revisar y firmar por técnico
  competente.

## [0.17.0] — 2026-06-21
- **Losa plana POSTESADA 2D + punzonamiento con efecto favorable del pretensado
  (caso 13, tercer peldaño de la 2ª tanda — lleva el PRETENSADO a 2D)** — el
  pretensado (EC2 §5.10, caso 12, 1D) se generaliza a una losa plana sobre
  pilares (placa MITC4 + punzonamiento, caso 3) mediante el **balance de cargas
  2D** y el **punzonamiento con pretensado §6.4.4**. Corrección **acotada**: un
  orquestador nuevo + dos bibliotecas nuevas en `pretensado/` y una **ampliación
  retrocompatible** de `laminas/ec2_punz_fis.punzonamiento` (parámetros opcionales
  con default que reproduce el caso 3). **Sin tocar los casos 1–12** en su
  comportamiento. Reempaquetado **acumulativo** partiendo del v0.16.0 instalado.
  - `scripts/pretensado/run_all_losa_postesada.py` (NUEVO): orquestador end-to-end
    (IFC ortodoxo losa+9 pilares → modelo neutro con `Pset_Estructurando_Pretensado`
    de la SUPERFICIE → balance 2D → placa MITC4 con caso P → pérdidas → verificación
    → JSON + diagramas). Reutiliza `laminas/solver_flat.parse_ortodoxo`.
  - `scripts/pretensado/solver_losa_postesada.py` (NUEVO): placa MITC4 sobre apoyos
    puntuales con el **caso P del pretensado** (presión equivalente hacia arriba
    w_p) + casos G0 (peso propio, NO viene del IFC), G (g2) y Q; combinaciones
    ELU/ELS con P (favorable, γ_P≈1.0) y combo de transferencia (g0+P0). Equilibrio
    ELU sobre la **carga neta** (externa − balance).
  - `scripts/pretensado/balance_2d.py` (NUEVO, biblioteca): w_p por dirección
    (8·P·a/L²), banded(X)+distribuido(Y), σcp biaxial, **V_p** (componente vertical
    de los tendones que cruzan u1, por equilibrio del área de control) y tensiones
    por fibra de franja.
  - `scripts/pretensado/verificacion_losa_postesada.py` (NUEVO): tensiones por fibra
    **por franja** (transferencia/cuasiperm/rara, momentos NETOS tomados del FEM,
    continuidad real, percentil de envolvente), **contraste cargas-equivalentes vs
    fuerza+excentricidad** por franja (identidad M_net=M_ext−P·e, Δ≈0),
    punzonamiento §6.4.4 **con/sin** efecto favorable, ELU de flexión por fibras
    (activa banded/distribuida + pasiva) por franja, fisuración §7.3, flecha con
    pretensado.
  - `scripts/laminas/ec2_punz_fis.py` (AMPLIADO retrocompatible):
    `punzonamiento(..., sigma_cp=0.0, V_p=0.0, k1=0.1)` → **v_Rd,c += k₁·σcp**
    (§6.4.4) y **V_Ed,red = V_Ed − V_p**. Con los defaults (σcp=0, V_p=0) reproduce
    EXACTAMENTE el caso 3 (sin pretensado).
  - `scripts/pretensado/plots_losa_postesada.py` + `generate_memoria_losa_postesada.py`
    (NUEVOS): planta de tendones banded/distribuido, cargas equivalentes 2D, mapas
    Mx/My, tensión por fibra y franja, perímetro de control con los tendones que lo
    cruzan, ELU por franja, flecha; memoria Word con diagramas embebidos.
- Validación (caso 13, C40/50 t=0,25 m, 3×3 pilares 0,45², vanos 8,0 m):
  **balance** w_px=w_py=4,505 → w_p=9,01 kN/m² ≈ permanente 9,0 (residual ≈0,11 %);
  **P/m=212 kN/m**; **σcp=0,848 MPa**; **σp,∞=0,600·fpk**, σp0=0,720·fpk (pérdidas
  diferidas ≈16,7 %); **V_Ed,punz interior≈1.258 kN**; el efecto favorable del
  pretensado **RELAJA** el aprovechamiento de punzonamiento (k₁·σcp en v_Rd,c +
  descuento de V_p); contraste cargas-equiv vs fuerza+exc **Δ≈0,000 MPa** por
  franja. **Tensiones por fibra** dentro de límites (transferencia inf +2,26 < fctm
  3,5; cuasiperm todo comprimido; rara inf +1,64 < fctm). **ELU flexión**: campo
  u=0,68 (As mín φ12/200); apoyo hogging u=0,99 con armadura pasiva superior
  **dimensionada** As=9,50 cm²/m (≈φ16/200) sobre pilares. **Punzonamiento** bare
  slab (con pretensado) u≈2,1–2,3 > 1 → la losa de 0,25 m a 8,0 m **requiere ábaco/
  capitel/armadura de punzonamiento** (dimensionado: h_ábaco≈0,47 m / capitel ≈2,18 m
  / Asw·sr≈110 cm²/m); el pretensado **relaja ≈13 %** (interior 2,61→2,27). **Flecha**
  total 5,2 mm ≪ L/250=32 mm (u=0,16; cuasiperm 1,6 mm por contraflecha de balance).
  **Fisuración** σ_inf,rara 1,64 < fctm (u=0,47). **Veredicto: CUMPLE con solución de
  punzonamiento; aprov. estructural máx 0,99 (≤1)**; equilibrio ELU neto 0,000 %.
  Malla MITC4 1,0 m (coincide con las 9 cabezas; 0,5 m queda como refinamiento).
  `[confirmar AN]` k₁=0,10, μ/k, penetración de cuña, límites del acero activo
  (EC2 §5.10/§6.4.4 NDP España). **Predimensionado, a revisar y firmar por técnico
  competente.**

## [0.16.0] — 2026-06-21
- **Puente IFC FÍSICO → analítico ampliado a SUPERFICIES (caso R2, segundo
  peldaño de la Dirección 2)** — el módulo `puente_analitico/` (que en R1 leía
  solo elementos lineales) ahora deriva también la **losa física** (`IfcSlab`)
  desde la geometría y enruta el modelo neutro al forjado losa-sobre-vigas
  existente SIN tocar el motor. *(Coordinación de versiones: el caso 12
  —pretensado— tomó 0.15.0; este caso toma 0.16.0.)*
  - `scripts/puente_analitico/puente.py` (AMPLIADO): por cada `IfcSlab` (y, en
    R3, `IfcWall`/`IfcFooting`) extrae la **superficie media** = footprint del
    `IfcExtrudedAreaSolid` (esquinas del `IfcRectangleProfileDef`/
    `IfcArbitraryClosedProfileDef`) llevado a MUNDO con el placement compuesto
    (`get_local_placement` + `get_axis2placement` de la `Position` del sólido) y
    la **cota media** del barrido; el **espesor** = Σ `LayerThickness` de
    `IfcMaterialLayerSetUsage`→`IfcMaterialLayerSet` (geometría `Depth` de
    respaldo); el **material** de `IfcRelAssociatesMaterial`→`IfcMaterial`, con
    **fck** de `CompressiveStrength` y **fctm** derivado de EC2 (3.1) si no
    viene. **Conectividad superficie↔barras**: la losa se asocia a las **vigas
    que la soportan** (eje de viga dentro/bajo el contorno en planta, como el
    clasificador del caso 10) → `vigas_asociadas`. Salida = **mismo modelo neutro
    estándar** (claves `superficies[]` de `laminas/ifc_to_model_3d`:
    `esquinas_coords`, `espesor`, `material`, `cargas`). **Cargas de hipótesis**:
    `Pset_Estructurando_CargaHipotesis` de SUPERFICIE (G/Q kN/m²) → `surf.cargas`
    (la de LÍNEA de R1 se conserva). **R1 intacto** (sin slabs → `superficies=[]`).
  - `scripts/puente_analitico/run_all_real_forjado.py` (NUEVO): orquestador del
    forjado físico (IFC físico con superficies → puente → modelo neutro →
    **clasificar/enrutar** (1 superficie horizontal de hormigón + barras
    horizontales de acero I → `forjado_losa_sobre_vigas`) → `laminas/run_forjado`
    (losa EC2 unidireccional + reparto por ancho tributario + vigas EC3) →
    equilibrio). Reutiliza `laminas/run_forjado` y `barras` SIN CAMBIOS.
  - `scripts/puente_analitico/plots_real_forjado.py` (NUEVO): 3 diagramas con
    nombres de barra genéricos del puente (sin tocar el plotter del caso 2).
  - `scripts/puente_analitico/generate_memoria_real_forjado.py` (NUEVO): memoria
    Word (python-docx) del caso R2.
- Validado con el **caso R2** (IFC físico IFC4: 1 `IfcSlab` C30/37 t=120 mm
  6,0×4,0 + 2 `IfcBeam` IPE 400 S275, geometría = caso 2; sin entidades de
  análisis ni cargas):
  - **Puente**: se derivan **1 superficie** (losa C30/37, t=0,120 m del
    `IfcMaterialLayerSet`, 6,0×4,0, z_med=−0,06) + **2 barras** (vigas IPE 400,
    L=6,0 m), losa asociada a B1/B2, 4 nudos de extremo biarticulados.
  - **Reproduce el caso 2**: losa φ10/125, **m_Ed=21,15 kN·m/m** (w_k=0,18 mm,
    flecha 39 %); reparto trib 2,0 m → G=9,0/Q=6,0 kN/m; **vigas IPE 400 26,5 %**;
    **reacción 63,45 kN/extremo**; **equilibrio 0,000 %** (253,8=253,8 kN);
    validación cruzada viga 0,042 % y strip de losa 0,000 % (MITC4 OK). **CUMPLE**.
  - Memoria Word + `modelo_neutro.json`/`verificacion.json`/`clasificacion.json`
    + 3 diagramas. Plugin **v0.16.0** (minor: `puente_analitico/` a superficies).
- **Nota de coordinación (hilos en paralelo, resuelta):** durante este hilo el
  hilo del caso 12 reempaquetó el `.plugin` instalado a **0.15.0 con
  `pretensado/`** (carrera de escritura sobre la carpeta compartida). Para no
  perder ninguno de los dos trabajos, el reempaquetado final de R2 se hizo
  **acumulativo partiendo del `.plugin` v0.15.0 instalado** (que ya traía
  `pretensado/` **válido** + `sismico/` + `puente_analitico/` de R1) y **añadiendo
  encima** los ficheros de R2 (`puente.py` ampliado a superficies +
  `run_all_real_forjado.py` + `plots_real_forjado.py` +
  `generate_memoria_real_forjado.py`). Resultado: **`.plugin` v0.16.0 instalado =
  casos 1–11 + `sismico/` (EC8) + `pretensado/` (EC2 §5.10, caso 12) +
  `puente_analitico/` con R1 (barras) y R2 (superficies)** — 133 entradas, sin
  `node_modules`/`__pycache__`, verificado end-to-end (R2 reproduce el caso 2
  desde el paquete instalado). El `pretensado/` válido se tomó del propio `.plugin`
  0.15.0 (las copias de `caso-12-viga-postesada/_codigo/` están truncadas, INC-04).

## [0.15.0] — 2026-06-21
- **Viga postesada isostática (caso 12, APERTURA de la tipología de PRETENSADO)** —
  primer módulo que incorpora la **acción de pretensado** (P) y la biblioteca
  **EC2 §5.10**. Módulo NUEVO, sin tocar los casos 1–11. Reempaquetado
  **acumulativo** (preserva `sismico/` y `puente_analitico/` y añade `pretensado/`).
  - `scripts/pretensado/solver_pretensado.py` (NUEVO): parser ortodoxo de la viga
    (sección `IfcRectangleProfileDef` vía `IfcMaterialProfileSet`, material C40/50,
    apoyos `IfcStructuralPointConnection`+`IfcBoundaryNodeCondition` → idealización
    isostática biapoyada, cargas g2/q por `IfcStructuralCurveAction`+
    `IfcStructuralLoadGroup`) + lectura del **`Pset_Estructurando_Pretensado`**
    (P0/σp0, Ap, fpk, trazado parabólico/e, μ/k, cuña, relajación). Carga
    `laminas/ifc_to_model_3d` por **ruta explícita con salvaguarda de `sys.path`**
    (módulos homónimos) con respaldo robusto a lectura directa del IFC. Peso propio
    g0 = A·γc con γc=25 kN/m³ (convención EC2/EHE).
  - `scripts/pretensado/ec2_pretensado.py` (NUEVO, biblioteca EC2 §5.10): pretensado
    como **cargas equivalentes** (load balancing w_p=8·P·e/L² + axil + momentos de
    anclaje) y como **fuerza+excentricidad**; trazado parabólico (e(x), θ(x));
    **pérdidas instantáneas** (rozamiento μ·(θ+k·x) ec. 5.45, penetración de cuña
    con longitud de influencia, acortamiento elástico) y **diferidas** (ec. 5.46
    combinada retracción+fluencia+relajación, relajación ec. 3.29 clase 2);
    combinaciones de momentos (rara/frecuente/cuasipermanente/ELU).
  - `scripts/pretensado/verificacion_pretensado.py` (NUEVO): **tensiones por fibra**
    en transferencia (≤0,6·fck(t)) y servicio (cuasiperm ≤0,45·fck, rara ≤0,6·fck +
    tracción <fctm), **ELU de flexión por FIBRAS** con armadura activa+pasiva (bloque
    η·fcd/λ·x, equilibrio de axil → x, M_Rd), **fisuración §7.3** y **cortante con
    pretensado** (V_Rd,c con σcp ec. 6.2a/6.2b).
  - `scripts/pretensado/run_all_pretensado.py` (NUEVO): orquestador end-to-end +
    **validación cruzada** cargas equivalentes vs fuerza+excentricidad (mismo estado
    tensional). `plots_pretensado.py` (trazado, cargas equiv., M/V, tensiones por
    fibra transferencia/servicio, ELU, pérdidas) y `generate_memoria_pretensado.py`
    (memoria Word python-docx con diagramas embebidos).
- Validado con el **caso 12** (viga C40/50, b=0,50×h=1,30, L=20 m; 1 tendón
  13×Y1860S7 Ap=1950 mm², trazado parabólico e=0,50 m; g2=5,0, q=12,0 kN/m, ψ₂=0,3):
  - **Load balancing**: w_p=21,25 kN/m equilibra la permanente (21,25 kN/m),
    residual 0,0 %. **P_m,∞=2125 kN (σp,∞=0,586·fpk)**, P0=2535 kN (σp0=0,699·fpk).
  - **Momentos**: M_g0=812,5, M_perm=1062,5, M_q=600, M_qp=1242,5, M_rara=1662,5;
    **M_Ed(ELU)=2334,4 kN·m**.
  - **Tensiones por fibra** (coinciden con el chequeo de mano): transferencia
    sup −0,67 / inf −7,13 MPa (todo comprimido); cuasiperm sup −4,55 / inf −1,99
    (sin descompresión); rara sup −7,53 / **inf +0,99 MPa** (<fctm=3,5).
  - **Cross-check** cargas equivalentes vs fuerza+excentricidad: idéntico
    (Δ=0,0 MPa). **ELU** M_Rd=2908 ≥ M_Ed=2334 (x/d=0,23). Aprov máx 0,91
    (cortante). **CUMPLE.** Plugin **v0.15.0** (minor: módulo `pretensado/` +
    biblioteca EC2 §5.10). **Apertura de la tipología de pretensado.**

## [0.14.0] — 2026-06-21
- **Puente IFC FÍSICO (BIM real) → modelo analítico (caso R1, APERTURA de la
  Dirección 2)** — primer módulo que parte de un **IFC físico** (elementos
  constructivos con geometría de barrido, sin entidades de análisis ni cargas),
  no de un IFC ortodoxo del dominio de análisis. Módulo NUEVO, sin tocar los
  casos 1–10. *(Versión coordinada con la Dirección 1: el caso 11 reserva
  0.13.0 para el módulo sísmico EC8; este caso toma 0.14.0.)*
  - `scripts/puente_analitico/puente.py` (NUEVO): convierte un IFC físico en el
    **mismo modelo neutro estándar** que ya consume el motor:
    - **Extracción geométrica** por `IfcColumn`/`IfcBeam`/`IfcMember`: el **eje**
      = directriz del barrido (origen = traslación del `ObjectPlacement`
      compuesto resuelto a mundo con `ifcopenshell.util.placement.get_local_placement`;
      dirección = eje local Z del placement; longitud = `Depth` del
      `IfcExtrudedAreaSolid`, con respaldo `ExtrudedDirection`·`Depth` proyectada
      al mundo); el **perfil** de `IfcMaterialProfileSetUsage` →
      `IfcMaterialProfileSet` → `IfcMaterialProfile` → `IfcIShapeProfileDef`
      (reutiliza `perfiles_db`, prioridad a catálogo; geometría del `SweptArea`
      de respaldo); el **material** del profile set + `IfcMaterialProperties`.
    - **Conectividad / grafo de nudos**: fusión de extremos coincidentes por
      **tolerancia** (1 mm) y troceo de una barra cuando el extremo de otra cae en
      su interior (general; en R1 los ejes son limpios y se cortan en los extremos
      → 4 nudos). Los **offsets/excentricidades** físico↔analítico se endurecen
      en R5.
    - **Apoyos**: inferidos de `Pset_Estructurando_ApoyoBase` (cota base,
      biarticulado → `[T,T,T,F,F,T]`) o, en su defecto, de la cota mínima.
      **Cargas**: el IFC físico no las trae → hipótesis de proyecto de
      `Pset_Estructurando_CargaHipotesis` (G/Q kN/m, dirección −Z → N/m con
      signo). Se documentan en el modelo neutro (`hipotesis`).
  - `scripts/puente_analitico/run_all_real.py` (NUEVO): orquestador de la
    Dirección 2 (IFC físico → puente → modelo neutro → **clasificar/enrutar** con
    los mismos criterios del enrutador (material S* + sección en I + orientación)
    → módulo `barras` (EC3) → solver PyNite → validación cruzada anaStruct →
    verificación EC3 → diagramas). Reutiliza el módulo `barras` SIN CAMBIOS.
  - `scripts/puente_analitico/generate_memoria_real.js` (NUEVO): memoria Word del
    caso R1, con la sección del **puente físico→analítico** (ejes derivados,
    grafo de nudos), la tabla de **hipótesis** de apoyo/carga (no venían en el
    IFC), el enrutado, el equilibrio (93,60 kN/apoyo) y la reproducción del caso 1.
- Validado con el **caso R1** (IFC físico IFC4: 2 `IfcColumn` HEB 200 + 1
  `IfcBeam` IPE 330, S275, geometría = caso 1):
  - **Puente**: del IFC físico se derivan **3 barras** (2 pilares verticales de
    acero I + 1 dintel horizontal de acero I) y **4 nudos** por intersección de
    ejes, con perfiles HEB 200/IPE 330, material S275 y longitudes 4,0/6,0 m
    correctos. El parser de análisis (`laminas/ifc_to_model_3d`) lee 0 elementos
    del mismo IFC (no hay entidades de análisis): el puente cubre exactamente esa
    brecha.
  - **Enrutado**: sistema = pórtico plano de acero → `barras` (EC3), igual que el
    caso 1.
  - **Reproduce el caso 1**: equilibrio **93,60 kN/apoyo** (Σ=187,2 kN, error
    ~0 %; horizontales ±12,19 kN balanceadas); **pilares HEB 200 32,0 %**;
    **dintel IPE 330 44,6 %**; autodiagnóstico OK; validación cruzada PyNite vs
    anaStruct **CONFORME**. Aprovechamientos ≤ 1. **CUMPLE**.
  - Memoria Word + `modelo_neutro.json`/`verificacion.json`/`clasificacion.json`
    + diagramas. Plugin **v0.14.0** (minor: módulo `puente_analitico/`). **Apertura
    de la Dirección 2.**

## [0.13.0] — 2026-06-21
- **APERTURA DE LA FAMILIA SÍSMICA: nuevo módulo `sismico/` + biblioteca EC8
  (EN 1998-1) (caso 11, Dirección 1, segunda tanda)** — por primera vez el motor
  aborda un **tipo de análisis nuevo** (dinámico/espectral), no sólo una
  verificación. Corrección **estructural pero acotada** (grupo nuevo, sin tocar
  los casos 1–10). *(Versión coordinada con la Dirección 2: el caso 11 toma
  0.13.0; el caso R1 — módulo `puente_analitico/` — toma 0.14.0. El `.plugin`
  instalado es **acumulativo** y contiene ambos módulos.)* Nuevo
  `scripts/sismico/`:
  - `solver_sismo.py` (NUEVO): parser ortodoxo de la pantalla de cortante.
    Reutiliza `laminas/ifc_to_model_3d` (cargado por **ruta explícita con
    salvaguarda de `sys.path`**, módulos homónimos) para el modelo neutro; lee las
    **5 masas de planta** de `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce`
    (ForceZ −Z → W_i) mapeadas a su nodo de planta, y los **parámetros EC8** del
    `Pset_Estructurando_Sismo`. Construye el **voladizo equivalente** (stick de 6
    nodos) con la sección de pared (E, I=tw·Lw³/12=1,60 m⁴, A_v de cortante) y
    masas concentradas por planta. Datos sin entidad de análisis estándar (q, S,
    TB/TC/TD, λ, ductilidad) del Pset, igual que ks/Rd/conectores/terreno de los
    casos 5/6/7/9.
  - `ec8.py` (NUEVO, biblioteca reutilizable): **espectro de cálculo `Sd(T)`** con
    las CUATRO ramas (EN 1998-1 §3.2.2.5; q, λ, límite inferior β·ag, β=0,2
    `[confirmar AN]`); **rigidez lateral** del stick con flexión Euler-Bernoulli +
    **flexibilidad de cortante (Timoshenko)** —relevante en muro corto,
    φ=12EI/(GA_vL²)=5,12—; **análisis modal** por `scipy.linalg.eigh` (T_i, modos,
    factores de participación y **masas modales efectivas**); **combinación modal
    SRSS**; **método de fuerzas laterales equivalentes** (§4.3.3.2) como contraste;
    **combinación sísmica** (EC0 §6.4.3.4). Leyes de cortante/momento en altura,
    **derivas** (d_r=q·d_e, §4.3.4) y N-M en base.
  - `verificacion_sismo.py` (NUEVO): **cortante del alma** (EC2 §6.2.3 biela 45° +
    amplificación DCM ε=1,5 `[confirmar AN]`, V_Rd,max y armado ρ_h ≥ 0,2 %);
    **elementos de borde confinados** (EC8 §5.4.3.4.2: l_c, compresión ≤ N_Rd,c,
    **agrandado en predim.** si la compresión supera la capacidad del hormigón
    confinado, ρ_min 0,5 %); **interacción N-M en la base** (fibras, armadura de
    borde + alma); **deriva entre plantas** (limitación de daño §4.4.3.2, ν=0,5,
    límite 0,75 %·h `[confirmar AN]`). Aprov. ≤ 1, picos como envolvente.
  - `run_all_sismo.py` (NUEVO): orquestador end-to-end (IFC → stick → espectro →
    modal + fuerzas laterales → esfuerzos → verificación → JSON + diagramas).
  - `plots_sismo.py` (NUEVO): 7 diagramas (espectro Sd(T), modos, fuerzas por
    planta, cortante y momento en altura, deriva, diagrama N-M).
  - `generate_memoria_sismo.py` (NUEVO): memoria de cálculo sísmico en `.docx`
    (python-docx) con los diagramas embebidos.
  - El **núcleo** (varias pantallas acopladas) queda como extensión de la misma
    familia para un caso posterior.
- Validado con el **caso 11** (IFC ortodoxo: pantalla C30/37 Lw=4,0 tw=0,30
  H=15,0, 5 masas de planta + Pset EC8; ag=0,20 g, suelo C, espectro tipo 1,
  q=3,0 DCM, λ=0,85):
  - **Espectro**: Sd(meseta)=ag·S·2,5/q=**0,1917 g** (=1,880 m/s²) ✓.
  - **Modal** (`scipy.eigh`): **T1=0,408 s** (en MESETA, TB=0,20≤T1≤TC=0,60),
    **M_eff,1=68,9 %** (≥60–70 %), ΣM_eff=100 % ✓.
  - **Cortante basal**: por **fuerzas laterales** Fb=Sd·M·λ=**928,6 kN** (rango
    900–950, mano 929) ✓; **modal SRSS** Fb=785 kN (diferencia 15,5 %, mismo
    orden, explicada por λ=0,85 y M_eff,1=68,9 % → gobierna la envolvente de
    fuerzas laterales); **equilibrio Fb=ΣF_i error 0,000 %**; **M de vuelco en
    base=9.877 kN·m**, altura eficaz 10,64 m; N base=ΣW=5.700 kN.
  - **Verificación** (aprov.): **cortante alma 0,31** (V_Ed,dis=1.393 <
    V_Rd,max=4.562 kN; Asw/s=11,1 cm²/m 2 caras); **elemento de borde 0,97**
    (l_c agrandado 0,60→**1,20 m**=0,30·Lw, F_compr=5.937 ≤ N_Rd,c=6.120 kN;
    As=18 cm²/borde por ρ_min); **N-M base 0,86** (N=5.700, M=9.877; M_Rd=11.515
    kN·m); **deriva 0,23** (d_r·ν=5,1 mm ≤ 0,75 %·h=22,5 mm; desplaz. cubierta
    38,4 mm=H/391). **Veredicto CUMPLE; aprov. máx 0,97 (≤1)**.
  - Memoria de cálculo sísmico (`.docx`) + 7 diagramas + `modelo_neutro.json` y
    `verificacion_sismo.json`. Plugin **v0.13.0** (minor: módulo sísmico +
    biblioteca EC8). **Apertura de la segunda tanda.**

## [0.12.0] — 2026-06-21
- **Edificio integrado: clasificador/enrutador MULTI-ELEMENTO + orquestador
  integrado (caso 10, CIERRE de INC-03)** — por primera vez el motor itera TODO
  un IFC ortodoxo con varios sistemas y clasifica/enruta CADA elemento (no
  `by_type[0]`), generalizando la clasificación por geometría+Pset de los casos
  7 y 9 a un grafo completo de 4 sistemas en un mismo `IfcStructuralAnalysisModel`:
  - `scripts/clasificador.py` (NUEVO): construye el modelo neutro genérico
    (`laminas/ifc_to_model_3d`), itera barras y superficies y devuelve por
    elemento `(clase, módulo, run_all, datos)` por **geometría** (vertical/
    horizontal, barra/superficie) + **sección** (I-shape acero / rectangular
    hormigón) + **material** (S*/C*) + **lecho/carga de cabeza**. Resuelve las
    **asociaciones** viga↔losa (mixta, por proximidad en planta) y pilar↔zapata
    (por pie común) SIN Pset (marcador como confirmación). `extraer_subifc()`
    escribe un **sub-IFC node-minimal por subsistema** (sus miembros, nodos
    referenciados y acciones), de modo que cada `run_all*` se ejecuta sobre su
    PORCIÓN reproduciendo las condiciones de sistema único de los casos 1/5/6/7 y
    evitando los `by_type[0]` internos de cada parser (p. ej. el
    `IfcStructuralSurfaceMember[0]` de `solver_zapata`, que en multi-superficie
    cogía la losa mixta en vez de la zapata).
  - `scripts/run_all_edificio.py` (NUEVO): orquestador integrado. Clasifica,
    extrae sub-IFC y lanza el `run_all*` de cada subsistema en **subproceso
    aislado** (evita el choque de módulos homónimos `solver_*`/`combinaciones`/
    `plots_*`/`verificacion_*`/`run_all*` entre paquetes) y **consolida** un
    índice del edificio (`resumen_edificio.json`). Opciones `--solo` (un
    subsistema) y `--no-run` (solo enrutado) para el límite de 45 s del sandbox.
  - `scripts/cimentaciones/run_zapata_predim.py` (NUEVO): predimensionado de la
    zapata — pre-chequeo ANALÍTICO del hundimiento por área eficaz con el lado de
    modelo y, si supera R_d, AMPLÍA la zapata cuadrada (centrada en el pilar) al
    mínimo lado que cumple, con un ÚNICO solve FE de confirmación (la malla fina
    es lenta en el sandbox).
  - **Correcciones acotadas, backward-compatible (sin regresión en casos 1–9):**
    - `scripts/barras/ifc_to_model.py`: respaldo por **coordenadas** en la
      resolución de extremos de barra (`IfcEdge`) cuando el IFC usa vértices
      distintos para la arista y para el `IfcStructuralPointConnection` (caso 10);
      el caso 1 (vértices compartidos) resuelve por id como antes. *Verificado:
      caso 1 HEB 200 32,0 % / IPE 330 44,6 % sin cambio.*
    - `scripts/mixtas/solver_mixta.py` (`parse_ortodoxo`): lectura del Pset de
      **conectores/chapa con DOS convenios de nombres** (caso 6: `d_m/hsc_m/
      sep_long_m`, `ht_m/hp_m/hc_m/nervios/nr/apeado`; caso 10: `Diametro_m/
      Altura_m/nr_por_nervio/Apeado`, `Canto_m/CantoChapa_hp_m/CantoHorm_hc_m/
      Orientacion`). Si falta la separación longitudinal, con chapa perpendicular
      y nr conector/nervio se deriva del paso de nervio (0,207 m hp58/hc62
      `[confirmar ficha de chapa]`). *Verificado: caso 6 M 244/432 η=0,66 flecha
      61 % sin cambio.*
    - `scripts/cimentaciones/solver_zapata.py` (`parse_ortodoxo`): el momento de
      cabeza se lee como **componente gobernante** `max(|MomentX|,|MomentY|)`
      (caso 5 lo guarda en Mx, caso 10 en My; zapata cuadrada → el eje es
      indiferente para la excentricidad). Compatible: con solo Mx≠0 devuelve Mx
      (caso 5 idéntico, comprobado a nivel de parser).
- Validado con el **caso 10** (IFC ortodoxo multi-elemento, 5 barras + 3
  superficies + 4 sistemas en un mismo modelo), clasificando y enrutando los **6
  elementos resolubles** e iterando TODO el IFC:
  - **A) Pórtico de acero** (`barras`, EC3): pilares **HEB 240** N-M **22,9 %**,
    dintel **IPE 360** flexión/flecha **30,5 %**; validación cruzada PyNite vs
    anaStruct OK; equilibrio exacto. **CUMPLE**.
  - **B) Viga mixta** (`mixtas`, EC4): **IPE 400** + losa C25/30 t=0,12, L=8,0 m,
    sep=3,0 m, chapa perpendicular sin apear: b_eff=2,10 m; **M_Ed=333/M_Rd=450
    kN·m (74 %)** con **conexión parcial η=0,66**; cortante 25 %; fase
    construcción 32 %; flecha 64 %. **CUMPLE**.
  - **C) Muro de carga** (`laminas`, EC2): C30/37 H=3,0 t=0,20, carga de cabeza
    N_G=250/N_Q=120 e=25 mm: **λ=52 > λ_lim=30 → esbelto**; columna modelo
    **M_Ed = M0Ed 16,4 + M2 13,9 = 30,2 kN·m/m**, M_Rd=68,1 (φ10/200 c/cara),
    **N-M 44 %**; compresión §12.6.5.2 17 %; equilibrio 0,000 %. **CUMPLE**.
  - **D) Cimentación** (`cimentaciones`, EC2+EC7): pilar 0,40 + zapata sobre lecho
    ks=40 MN/m³, R_d=250 kPa, N_G=700/N_Q=250 + M=80/40 kN·m. La zapata de modelo
    **2,5×2,5** da hundimiento área eficaz **σ_ef 255 kPa (102 %)** → en
    predimensionado se **adopta 2,6×2,6** (centrada): **σ_ef 236/250 kPa (94 %)**,
    e=0,116 < B/6=0,433 (sin despegue), punzonamiento 17 %, cortante 51 %,
    fisuración w_k=0,28 mm (93 %), asiento 4,9 mm; equilibrio del lecho 0,00 %.
    **CUMPLE**.
  - **EDIFICIO: los 4 subsistemas CUMPLEN; aprovechamientos ≤ 1; picos como
    envolvente.** Memoria de cálculo integrada (Word) con clasificación/enrutado,
    los 4 subsistemas y el índice del edificio + diagramas. Plugin **v0.12.0**
    (minor: clasificador/enrutador multi-elemento + orquestador integrado).
    Cierre de **INC-03** y de la **primera tanda** del programa.

## [0.11.0] — 2026-06-21
- **Cimentación profunda ortodoxa: pilote + encepado + pantalla anclada (caso 9,
  INC-03)** — vía **ortodoxa** (`parse_ortodoxo()` + `parse_auto()`, prioritaria;
  Pset como respaldo, sin regresión) añadida a los **tres módulos** encadenados,
  con **clasificación/enrutado** de cada elemento del mismo IFC (antesala del
  caso 10). Las tres barras son `tipo=pilar` por geometría; se separan por el
  Pset presente (igual que el caso 7 separó muro de carga vs contención):
  - `scripts/barras/perfiles_db.py`: nuevo `from_circle_geometry(D)` y rama
    **`IfcCircleProfileDef`** en `props_from_profile_def` (A=π·D²/4, Iy=Iz=π·D⁴/64,
    Wpl=D³/6, J=2·I, Avz=0,9·A); antes devolvía `None` para el círculo. Mantiene
    la prioridad a catálogo; I-shape/rectangle intactos (IPE 330 A=62,61 cm²,
    rectángulo 0,40 A=0,16 — verificado sin regresión).
  - `scripts/pilotes/solver_pilote.py`: `parse_ortodoxo()` clasifica el **pilote**
    como la barra vertical con `Pset_Estructurando_Pilote`, lee **D** de
    `IfcCircleProfileDef` (Radius·2), la **carga de cabeza** (N_G, N_Q, H) de los
    `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce` mapeados al nodo de
    cabeza (z máx) por `IfcRelConnectsStructuralActivity` y caso del
    `IfcStructuralLoadGroup` (ForceZ −Z → axil de compresión; ForceX → H), y la
    **geotecnia** kh/qs/qb del Pset (sin entidad de análisis estándar).
    `parse_auto()` da prioridad a la vía ortodoxa; `run_all_pilote.py` la usa.
  - `scripts/bielas-tirantes/run_all_encepado.py`: `parse_ortodoxo()` clasifica el
    **encepado** como la `IfcStructuralSurfaceMember` con
    `Pset_Estructurando_Encepado`, toma el **canto = `Thickness`** y la
    **separación entre pilotes** de la distancia entre los dos
    `IfcStructuralPointConnection` de cabeza (con BC `TranslationalStiffnessZ`,
    z≈0); la **carga del pilar** del `IfcStructuralPointAction` sobre el nodo de
    pilar (z≈0 sin BC, distinto de las cabezas); ancho/lado pilar/Ø pilote
    (geometría de región D) del Pset. `parse_auto()` con respaldo Pset.
  - `scripts/muros-contencion/solver_pantalla.py`: `parse_ortodoxo()` clasifica la
    **pantalla** como la barra vertical con `Pset_Estructurando_Pantalla`, lee el
    **espesor** de `IfcRectangleProfileDef` (XDim) y el material de la asociación;
    terreno (γ/φ/q/R_d), ancla (z, incl, sep, bulbo) y excavación/empotramiento
    (sin entidad de análisis estándar) se mantienen en Pset. `parse_auto()` con
    respaldo Pset; `run_all_pantalla.py` la usa.
- Validado con el **caso 9** (IFC ortodoxo, todo C30/37; 2 pilotes + encepado +
  pantalla en un mismo modelo, clasificados y enrutados a tres módulos):
  - **Pilote** Ø0,60 L=12 m (vía ortodoxa, D del `IfcCircleProfileDef`):
    EC7 axil **N_Ed=1.215 = Rc,d 1.876 kN (65 %)** (fuste 1.357 + punta 707 car.,
    γ_s=γ_b=1,10); lateral viga sobre muelles kh=15 MN/m³ con **H=90 kN ELU**,
    M_Ed=88 kN·m, flecha cabeza 4,3 mm (43 %), equilibrio **0,000 %**; EC2 sección
    circular As,min 0,5 %·Ac=14,1 cm² (u_N 19 % / u_M 20 %). **CUMPLE**.
  - **Encepado** 2 pilotes (región D, EC2 §6.5): **N_Ed=2.430 kN**; celosía
    θ=39,7°, **T=1.464 kN / C=1.902 kN** (vs estática cerrada err **0,00 %**);
    tirante As_req 33,7 cm²; **biela 42 %, nudo CCC 68 %, nudo CCT 29 %**.
    **CUMPLE**.
  - **Pantalla anclada** e=0,60 H_exc=7,0 d=4,5 (L=11,5): Ka=0,333 / Kp=3,00
    (Rankine φ=30°); equilibrio horizontal ELU **0,00 %** (Ea,car=457 kN/m);
    M_máx=251 kN·m/m (z=5,0), **F_ancla=403 kN** (envolvente apoyo libre/muelles),
    bulbo L=6,41 m, FoS_pasivo empotramiento 1,78; fuste φ flexión M_Ed=251 →
    As=11,2 cm²/m (≥As,min 7,95). **CUMPLE**.
  - Picos como envolvente; aprovechamientos ≤ 1. Memorias Word + diagramas por
    elemento. Plugin **v0.11.0** (minor: lectura ortodoxa de pilote/encepado/
    pantalla + `IfcCircleProfileDef`).

## [0.10.0] — 2026-06-21
- **Losa de cimentación (raft) multipilar ortodoxa (caso 8, INC-03)** — vía
  **ortodoxa** añadida a `scripts/cimentaciones/solver_raft.py` (prioritaria;
  Pset como respaldo, sin regresión), generalizando la cadena pilar→cimiento del
  caso 5 de una zapata (1 pilar) a una losa con varios pilares:
  - `parse_ortodoxo()` + `parse_auto()`: lee la **losa** (BX, LY, canto =
    `Thickness`, material) de la `IfcStructuralSurfaceMember` horizontal (vía
    `ifc_to_model_3d`); identifica los **pilares** (barras verticales,
    `tipo="pilar"`) con su **lado** (`IfcRectangleProfileDef`) y su **pie**
    (centro de carga); **mapea la carga de cabeza de cada pilar** por el nodo de
    cabeza (`IfcRelConnectsStructuralActivity` → `Pxx_cabeza`), con
    `ForceZ` (gravedad −Z) de `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce`
    y caso del `IfcStructuralLoadGroup`; **reconstruye k_s** de la rigidez de los
    `IfcBoundaryNodeCondition` de esquina (k_s = k_esquina/((BX/2)·(LY/2))) y toma
    **R_d** de `Pset_Estructurando_Suelo`. Pset `_Losa`/`_Pilar_*` de respaldo.
  - `solve()`: añade el **peso propio de la losa** (caso G por área tributaria) →
    equilibrio = cabezas + p.p.; origen de malla parametrizado (x0,y0); filtro de
    combinaciones (ELU/ELU_G/ELS_car/ELS_cp) para la malla fina; guarda **cortante
    de placa** (Qx,Qy) por quad además de Mx,My. `run_all_raft.py` usa `parse_auto`.
  - `scripts/cimentaciones/verificacion_raft.py` reescrito:
    **EC7** capacidad con **presión media característica ≤ R_d** (pico bajo
    pilares/esquinas como **envolvente**, no de diseño; mismo criterio que casos
    3-5); sin despegue; **asiento diferencial** centro–borde y distorsión angular.
    **EC2**: flexión por bandas (sagging/hogging x,y) con **armadura realmente
    dispuesta** (helper `disponer()` que elige Ø/separación para cumplir ULS **y**
    w_k≤0,3 mm), armadura **principal en la capa exterior**; **cortante** de una
    dirección (V_Rd,c sin armadura); **punzonamiento** por pilar con **reducción
    por reacción del terreno** (EN 1992-1-1 §6.4.4(2), propia de cimentaciones) y
    utilización sin alivio informativa; **fisuración (7.3)** con el φ dispuesto.
  - `scripts/cimentaciones/plots_raft.py`: añadidos **planta** (pilares con N G/Q,
    muelles de esquina) y **mapa de asientos**; mapas de presión (caract.) y Mx/My.
  - `scripts/cimentaciones/generate_memoria_raft.js`: memoria del caso 8
    (lectura ortodoxa, equilibrio con p.p., EC7 media/envolvente + asiento
    diferencial, EC2 flexión/cortante/punzonamiento con alivio/fisuración).
- Validado con el **caso 8** (losa C30/37 6,0×4,0 t=0,60 m, k_s=40 MN/m³,
  6 pilares 0,40 malla 3×2; esquina N_G=550/N_Q=180, central N_G=850/N_Q=300 kN):
  vía **ortodoxa**, k_s reconstruido = 40 MN/m³; equilibrio ELU **7.722 kN**
  (cabezas 7.245 + p.p. 477) = Σ reacciones del lecho, error **0,00 %**; EC7
  **p_med=231 ≤ R_d=300 kPa (77 %)**, pico env. 247 / ELU 342 (informativo), sin
  despegue, **asiento dif. centro–borde 0,40 mm (1/5045)**; EC2 flexión inferior X
  **φ16/150 capa exterior** (M=231 kN·m/m), cortante x 73 %/y 36 %,
  **punzonamiento con alivio del terreno no crítico** (sin alivio 237 %),
  fisuración **w_k=0,293 ≤ 0,30 mm (98 %)**. Veredicto **CUMPLE**. End-to-end
  15,7 s en sandbox.

## [0.9.0] — 2026-06-21
- **Muros ortodoxos: muro de carga (esbeltez EC2) + muro de contención ménsula
  (EC7 DA-2*) (caso 7, INC-03)** — vía **ortodoxa** añadida a los dos módulos de
  muro (prioritaria; Pset como respaldo, sin regresión):
  - `scripts/laminas/solver_muro.py`: `parse_ortodoxo()` + `parse_auto()`. Toma
    **alzado (H), espesor (= `Thickness`) y material** de la
    `IfcStructuralSurfaceMember` vertical (vía `ifc_to_model_3d`), **clasifica
    muro de carga vs contención** por la AUSENCIA de `Pset_Estructurando_Terreno`,
    y lee la **carga de cabeza** (N + M = N·e) de los `IfcStructuralPointAction`
    + `IfcStructuralLoadSingleForce` (ForceZ + MomentY), con caso del
    `IfcStructuralLoadGroup`. La carga vertical de cabeza se aplica como
    compresión (FZ negativa). Pset `_MuroCarga` como respaldo.
  - `scripts/laminas/ec2_muro.py`: **método de la columna modelo / curvatura
    nominal (EN 1992-1-1 §5.8.8)** — `comprobar_pandeo_columna()` clasifica la
    esbeltez (λ vs λ_lim, §5.8.3.1), y si es esbelto calcula los efectos de 2º
    orden `M_Ed = M0Ed + M2` (M2 = N·e2, e2 = Kr·Kφ·(1/r0)·lo²/π²) y comprueba la
    sección con `M_Rd_simetrica()` (interacción **N-M** con armadura vertical
    simétrica, bloque rectangular). Se mantiene el método simplificado
    §12.6.5.2 como contraste.
  - `scripts/laminas/verificacion_muro.py`: rama ortodoxa (si hay carga de
    cabeza) que arma la **esbeltez por columna modelo** con la armadura vertical
    mínima dispuesta (§9.6). `plots_muro.diagrama_NM()`: **diagrama de
    interacción N-M** con el punto de diseño (M0Ed y M_Ed). `run_muro_carga.py`
    (nuevo alias) y `run_all_muro.py` usan `parse_auto`.
  - `scripts/muros-contencion/solver_muro.py`: `parse_ortodoxo()` + `parse_auto()`.
    Lee el **alzado** (Hm de las esquinas, t_alz = `Thickness`, material) de la
    superficie vertical y **clasifica el muro de contención** por la presencia de
    `Pset_Estructurando_Terreno`; la **geometría en T** de la zapata y los
    **parámetros del terreno** se mantienen en Pset (sin entidad de análisis
    estándar, igual que R_d/k_s del caso 5 y conectores/chapa del caso 6).
    `parse()` se hizo **robusto a IFC multi-superficie** (selecciona el miembro
    con `Pset_Estructurando_Muro`/`_Terreno`, no `by_type[0]`). El módulo
    `ifc_to_model_3d` se carga por ruta explícita con salvaguarda de `sys.path`
    (evita ensombrecer los módulos homónimos del paquete).
  - `scripts/muros-contencion/verificacion_muro.py`: **fisuración (EC2 §7.3.4)
    con el φ realmente dispuesto** y selección de diámetro/separación
    (`armar_fisuracion`) para w_k ≤ 0,3 mm, con la **armadura principal en la capa
    exterior** (trasdós del alzado, cara inferior de puntera y superior de talón).
  - Memorias Word ampliadas: la del muro de carga añade la sección **§5.8.8
    (M0+M2, N-M)** y el diagrama N-M; la del muro de contención muestra el **φ
    dispuesto y w_k** por elemento.
- Validado con el **caso 7** (IFC ortodoxo, 2 superficies verticales):
  - **Muro de carga** C25/30 H=3,0 t=0,20 m, faja 1,0 m, arriostrado; carga de
    cabeza G=250 / Q=120 kN/m, e=25 mm: equilibrio ELU **537,4 kN/m** error
    **0,000 %**; **λ=52 > λ_lim=27 → ESBELTO**; M_Ed = M0Ed 17,0 + M2 14,3 =
    **31,3 kN·m/m**; armadura φ10/200 c/cara → M_Rd=67,3, **N-M aprov. 47 %**;
    compresión §12.6.5.2 aprov. 21 %. **CUMPLE**.
  - **Muro de contención** C30/37 Hm=5,0 t=0,40 m, zapata B=3,40 (puntera 1,0 +
    talón 2,0), Df=0,80 m; relleno γ=19 φ=30° q=10 kPa, R_d=300 kPa: Ka=0,333;
    Eh=114,4 kN/m; **vuelco u=0,50 (FS=2,62)**, **deslizamiento u=0,97 (FS=1,67,
    pasivo parcial)**, **hundimiento u=0,55** (q_Ed=165 ≤ R_d=300 kPa, e=0,398 <
    B/6=0,567, sin despegue); alzado **φ16/100 trasdós** (M=241 kN·m/m, w_k=0,263),
    puntera **φ16/225** (w_k=0,277), talón **φ20/200** (w_k=0,296); validación
    empuje 0,21 %. **CUMPLE**.

## [0.8.0] — 2026-06-21
- **Viga mixta ortodoxa + IPE 360 en catálogo (caso 6, INC-03 / INC-06)** —
  `scripts/mixtas/solver_mixta.py` ampliado con vía **ortodoxa** (prioritaria;
  Pset como respaldo, sin regresión):
  - `parse_ortodoxo()` reconstruye la viga mixta desde el modelo neutro estándar
    (`laminas/ifc_to_model_3d`): **perfil de acero** de
    `IfcMaterialProfileSet`→`IfcIShapeProfileDef` (dims exactas h,b,tw,tf de la
    geometría; A/Iy/Wply/Avz de `perfiles_db` con **prioridad a catálogo**,
    geometría de respaldo); **losa** del `IfcStructuralSurfaceMember` (canto =
    Thickness, material por `IfcRelAssociatesMaterial`, ancho tributario = luz
    **transversal** al eje de la viga de la superficie); **cargas por fase** de
    los `IfcStructuralLoadGroup`+`IfcStructuralSurfaceAction`, **clasificadas por
    el nombre del grupo** (`*_construccion`/`*_mixta`) y por acción permanente
    (G*) o variable (Q*) → `{G_losa, Qc, G2, Q}`; **conectores y chapa nervada**
    se mantienen en `Pset_Estructurando_Conectores`/`_Losa` (sin entidad de
    análisis estándar, igual que R_d/k_s del caso 5). `parse_auto()` da prioridad
    a la vía ortodoxa y cae a `parse()` (Pset) si falta información estándar.
  - `run_all_mixta.py` usa `parse_auto`. `verificacion_mixta.b_eff()` cap del
    ancho parcial `bei = min(Le/8, (sep−b0)/2)` → `b_eff ≤ L/4+b0` y `≤ sep`.
  - `scripts/barras/perfiles_db.py`: **IPE 360 añadido al catálogo** (A=72,73 cm²,
    Iy=16270 cm⁴, Wpl,y=1019 cm³, Avz=35,14 cm², clase 1) → recupera el ~4 % de los
    acuerdos que la geometría de placas subestimaba (INC-06; geometría daba
    A≈69,95 cm²).
- Validado con el **caso 6** (IPE 360 S275 + losa colaborante C25/30 t=0,12 m,
  L=8,0 m, sep=3,0 m, chapa perpendicular, sin apear): vía **ortodoxa**, sección
  de **catálogo** (A=72,73 cm²); esfuerzos biapoyados exactos (fase mixta
  q=30,46 kN/m → M=q·L²/8=**243,6 kN·m**, V=q·L/2=**121,8 kN**; construcción
  q=14,26 → M=114,0, V=57,0; error 0,000 %); **b_eff=2,10 m**; **M_pl,Rd=510,8**,
  **M_a,Rd=280,2**, **conexión parcial η=0,66 ≥ η_min=0,40** → **M_Rd=431,6 kN·m**
  (M_Ed 56 %); PNA en ala superior; cortante 22 %; **fase construcción** 41 %;
  **flecha** total 19,5 ≤ 32,0 mm (L/250, 61 %) y activa 4,2 ≤ 22,9 mm (L/350,
  18 %). Veredicto **CUMPLE**.

## [0.7.0] — 2026-06-21
- **Cadena pilar→cimiento ortodoxa + lecho elástico de borde (caso 5, INC-03)** —
  `scripts/cimentaciones/solver_zapata.py` ampliado con vía **ortodoxa**
  (prioritaria; Pset como respaldo, sin regresión):
  - `parse_ortodoxo()` reconstruye la zapata desde el modelo neutro estándar
    (`ifc_to_model_3d`): **geometría** de la zapata (B, L, canto, material) de la
    superficie `IfcStructuralSurfaceMember`/`IfcFaceSurface`; **cadena
    pilar→cimiento** identificando el pilar (barra vertical, `tipo="pilar"`), su
    lado desde la sección rectangular (`IfcRectangleProfileDef` vía `perfiles_db`)
    y el pie del pilar = centro de carga; **carga de cabeza** (N + M_x) leída de
    `IfcStructuralPointAction`+`IfcStructuralLoadSingleForce` con caso desde
    `IfcStructuralLoadGroup`; **lecho elástico Winkler** reconstruido de la rigidez
    de los `IfcBoundaryNodeCondition` (`TranslationalStiffnessZ`): k_s = k_nodo /
    área tributaria; **R_d** del dato geotécnico `Pset_Estructurando_Suelo`.
    `parse_auto()` da prioridad a la vía ortodoxa y cae al `parse()` Pset.
  - **Bajada de carga**: `solve()` añade el **peso propio de la zapata** (caso G,
    repartido por área tributaria) → el axil que llega al terreno = N de cabeza +
    p.p.; el equilibrio (Σ reacciones del lecho = axil total) cierra con error
    nulo. Filtro de combinaciones (ELU/ELS_car/ELS_cp) para acelerar la malla fina.
    El campo nodal guarda `trib` y `w` (asiento).
  - `scripts/cimentaciones/verificacion_zapata.py` reescrito:
    **EC7 hundimiento por área eficaz** (EN 1997-1 Anejo D): σ_ef = N_d/(B'·L')
    con B'=B−2e ≤ R_d como aprovechamiento gobernante; e < B/6 (sin despegue);
    σ_max de borde y pico FE reportados como **envolvente** (no valor de diseño,
    igual criterio que los picos singulares de los casos 3-4). **EC2 con presión
    NETA** del pilar (la presión del peso propio uniforme cuenta en EC7 pero **no
    flecta** la zapata): flexión en la cara del pilar tomando el **voladizo más
    cargado**, armadura principal en la **capa exterior** (dirección gobernante);
    punzonamiento (6.4) con el axil del pilar; cortante a d; **fisuración (7.3)
    con el φ dispuesto**; asiento (ELS). Autodiagnóstico **MITC4** (Timoshenko).
  - `scripts/cimentaciones/plots_zapata.py`: añadido **mapa de asiento** (ELS).
  - `scripts/cimentaciones/generate_memoria_zapata.js`: memoria del caso 5
    (cadena pilar→cimiento, bajada de carga, EC7 área eficaz, EC2 con fisuración
    y asiento, MITC4).
- Validado con el **caso 5** (pilar C30/37 0,40×0,40 + zapata 2,5×2,5 t=0,60 m
  sobre lecho k_s=40 MN/m³): vía **ortodoxa**, k_s reconstruido = 40 MN/m³;
  equilibrio ELU **1.444 kN = cabeza 1.320 + p.p. 124 = Σ reacciones** (error
  ~0 %); EC7 hundimiento **σ_ef=246 ≤ R_d=250 kPa (98 %)**, e=0,075 < B/6=0,417 m
  (sin despegue, picos de borde 273 / FE 271 kPa como envolvente); EC2 flexión
  cara pilar M_y=132,7 → φ12/125 (capa exterior), punzonamiento 11 %, cortante
  56 %, fisuración φ12 **w_k=0,272 ≤ 0,30 mm (91 %)**, asiento 4,9 mm; MITC4 OK.
  Veredicto **CUMPLE**.

## [0.6.0] — 2026-06-21
- **Superficie inclinada ortodoxa + apoyos de borde (caso 4, INC-03)** —
  `scripts/laminas/solver_incl.py` reescrito con vía **ortodoxa** (prioritaria;
  Pset como respaldo, sin regresión):
  - `_parse_ortodoxo()` reconstruye el faldón desde el modelo neutro estándar
    (`ifc_to_model_3d`): deduce **L_v** (longitud del borde de alero, horizontal),
    **L_u** (borde lateral sobre la pendiente) y **θ = asin(Δz/L_u)** de las
    esquinas inclinadas (`IfcFaceSurface`/`IfcPolyLoop`); material y cargas G/Q
    del camino estándar; **la carga G ya incluye el peso propio** (`incluye_pp`,
    no se duplica A·ρ·g).
  - **Apoyos lineales de alero y cumbrera** leídos de los
    `IfcStructuralPointConnection`+`IfcBoundaryNodeCondition`: los nodos se
    **clasifican por geometría** (alero z≈0 → `[T,T,T]`; cumbrera z≈z_máx →
    `[F,T,T]`) y se aplican los GDL reales; **bordes laterales LIBRES** (faldón
    1-vía que salva L_u entre alero y cumbrera). La vía Pset conserva el apoyo
    legacy en los 4 bordes.
  - **Esfuerzos de membrana completos** `n_x, n_y, n_xy` en el plano local del
    faldón (antes solo n_x, n_y); reacciones por borde (alero/cumbrera).
  - `scripts/laminas/verificacion_incl.py`: la **dirección gobernante** (mayor
    momento de vano = dirección de L_u) se coloca en la **capa exterior** (canto
    útil mayor); **fisuración con el φ realmente dispuesto** y selección de
    separación hasta w_k≤0,3 (igual que caso 3); membrana con n_xy y coherencia
    con el empuje tangencial q·senθ.
  - `scripts/laminas/generate_memoria_incl.js`: memoria del caso 4 (apoyo en
    alero/cumbrera, reacciones por borde, tabla de membrana con n_xy y empuje
    tangencial).
- Validado con el **caso 4** (faldón C30/37 t=0,20 m, 8,0×6,0 m, θ=30°): modelo
  neutro 1 superficie inclinada (esquinas z={0;3,0}) + 4 nodos alero/cumbrera;
  equilibrio ELU **460,8 kN = Σ reacciones (alero 230,7 + cumbrera 230,1)**,
  error 0,000 %; flexión vano **My=38,1 ≈ q_n·L_u²/8=37,4 kN·m/m** (φ10/125,
  µ=0,067), flecha 24 %, w_k=0,231 mm; **membrana** comp/trac ±67 kN/m,
  n_xy=7,1 kN/m → uRd=1,7 %; autodiagnóstico MITC4 OK (invariancia 0,78 %).

## [0.5.0] — 2026-06-21
- **Sección rectangular de pilar (IfcRectangleProfileDef)** — caso 3, INC-03:
  - `scripts/barras/perfiles_db.py`: nuevo `from_rectangle_geometry(b, h)` (A=b·h,
    Iy=b·h³/12, Iz=h·b³/12, W el/pl, J de St. Venant, Avz=5/6·A) y ampliación de
    `props_from_profile_def` para resolver `IfcRectangleProfileDef` (XDim, YDim).
    Se mantiene la **prioridad a catálogo** y la geometría como respaldo.
  - `scripts/laminas/ifc_to_model_3d.py`: el modelo neutro guarda ahora las
    propiedades de la sección rectangular del pilar (b, h, A, I) e **infiere
    `tipo="pilar"`** por geometría (barra vertical: Δz≠0, Δxy=0) cuando no hay Pset.
- **Apoyos puntuales: losa plana apoyada en una retícula de pilares (INC-03, paso 2)**:
  - `scripts/laminas/solver_flat.py`: nueva vía **ortodoxa** `parse_ortodoxo()` que
    construye los pilares desde el modelo neutro (barras verticales) — cabeza = nodo
    de mayor z, lado desde la sección rectangular, **posición clasificada
    geométricamente** (interior/edge/corner por la retícula). Se conserva la vía
    `Pset_Estructurando_Pilar` como respaldo. `solve()` no duplica el peso propio
    cuando la carga G de superficie ya lo incluye (`incluye_pp`).
  - `scripts/laminas/run_losa_plana.py` (nuevo orquestador del caso 3): IFC ortodoxo →
    modelo neutro → placa MITC4 con apoyos puntuales → flexión EC2 por bandas, flecha,
    **fisuración con el diámetro realmente dispuesto** (ajuste de la armadura inferior
    para w_k≤0,3) → **punzonamiento EC2 6.4** con valor de cálculo por **áreas
    tributarias** y reacción elástica como envolvente de seguridad (dimensionamiento) →
    equilibrio global.
  - `scripts/laminas/generate_memoria_caso03.js` (nuevo): memoria Word del caso 3.
- Validado con el **caso 3** (losa plana C30/37 t=280 mm sobre 9 pilares 0,40×0,40 m):
  modelo neutro 18 nodos / 9 pilares con sección / 1 superficie; equilibrio ELU
  1.597,5 kN con error 0,000 %; flexión vano φ10/150–φ10/125, soporte φ12/100; flecha
  aprov. 9 %; w_k=0,234 mm; punzonamiento interior **V_Ed,trib=399 kN → aprov. 77 %
  CUMPLE**; reacción elástica 616 kN dimensionada (canto≥320 mm / Asw·s_r 22,2 cm²/m /
  capitel 576 mm). Autodiagnóstico MITC4 OK.

## [0.4.0] — 2026-06-21
- **Parser `laminas` a IFC ortodoxo** (caso 2; análogo a `barras` v0.3.1):
  - `scripts/laminas/ifc_to_model_3d.py`: lee la **superficie** desde entidades
    estándar — esquinas de la representación `IfcFaceSurface`/`IfcPolyLoop`
    (polígono de `IfcCartesianPoint`), espesor de `IfcStructuralSurfaceMember.Thickness`,
    material por `IfcRelAssociatesMaterial` → `IfcMaterial`, y cargas de superficie
    desde `IfcStructuralSurfaceAction` + `IfcStructuralLoadPlanarForce` con el caso
    desde `IfcStructuralLoadGroup` (`IfcRelAssignsToGroup`). Las **barras** toman ahora
    sección/material del `IfcMaterialProfileSet` → `IfcIShapeProfileDef` (DB de perfiles,
    reutilizando `perfiles_db.py`). Se **mantiene el camino `Pset_Estructurando_*` como
    respaldo**. Salida del modelo neutro ampliada: `esquinas_coords` por superficie.
- **Reparto losa → vigas (INC-03, primer paso multi-elemento)** y orquestador del forjado:
  - `scripts/laminas/run_forjado.py`: losa **unidireccional** EC2 (m = q·L²/8 por metro,
    armado, reparto transversal, fisuración, flecha; comprobación de placa por banda FEM
    de 1 m + autodiagnóstico MITC4) → **reparto por ancho tributario** (mitad de la
    separación entre vigas) → **vigas EC3** con el módulo `barras` (PyNite + validación
    cruzada anaStruct de una viga representativa, evitando el colapso x–z de vigas
    paralelas) → **equilibrio global** (carga de superficie ELU vs suma de reacciones).
  - `scripts/laminas/plots_forjado.py`: planta del forjado, momento/sección de losa y
    esfuerzos de viga. `scripts/laminas/generate_memoria_caso02.js`: memoria Word.
- Validado con el **caso 2** (losa C30/37 t=120 mm + 2 vigas IPE 400 S275): m_Ed = 21,15
  kN·m/m (φ10/125), reparto G=9,0 / Q=6,0 kN/m, reacción por extremo 63,5 kN, equilibrio
  global error 0,00 %, validación cruzada 0,04 %; losa y vigas **CUMPLEN**.

## [0.3.1] — 2026-06-21
- **Parser `barras` a IFC ortodoxo** (INC-01, INC-02):
  - Nuevo `scripts/barras/perfiles_db.py`: base de datos de perfiles HEB/IPE (SI) y cálculo
    de propiedades (A, Iy, Iz, J, Wel/Wpl, Avz, clase EC3) desde un `IfcIShapeProfileDef`,
    con **prioridad a catálogo** y geometría de respaldo.
  - `ifc_to_model.py`: lee la **sección** desde `IfcRelAssociatesMaterial` →
    `IfcMaterialProfileSet` → `IfcMaterialProfile` → `IfcIShapeProfileDef`; resuelve el
    **material** del profile set; lee **cargas** desde `IfcStructuralCurveAction` +
    `IfcStructuralLoadLinearForce`, con caso desde `IfcStructuralLoadGroup`
    (`IfcRelAssignsToGroup`) y barra desde `IfcRelConnectsStructuralActivity`. Se **mantiene
    el camino `Pset_Estructurando_*` como respaldo** (compatibilidad con IFC del catálogo).
- **Corrección** `cross_validate.py`: la validación cruzada anaStruct solo creaba apoyo si
  todos los GDL estaban coaccionados (empotrado); ahora distingue **base articulada**
  (traslaciones fijas + giro en plano libre → `add_support_hinged`) de empotrada. Necesario
  para pórticos biarticulados.
- Validado con el **caso 1** (pórtico HEB 200 + IPE 330, S275): equilibrio exacto (93,60
  kN/apoyo), validación cruzada < 0,1 %, EC3 CUMPLE.
- Empaquetado: se excluyen `node_modules/` y `__pycache__/` del `.plugin` (INC-05).

## [0.3.0] — 2026-06-21
- **Añadido** grupo `mixtas/` — viga mixta acero-hormigón / forjado colaborante (EC4):
  ancho eficaz, M_pl,Rd por fibras y M_Rd con grado de conexión, conexión a cortante,
  cortante, fase de construcción y flecha (n0/nL).
- Agente, skill, README y hoja de ruta (v2.2) actualizados.

## [0.2.0] — 2026-06-21
- **Añadido** grupo `muros-contencion/` — muro ménsula (EC7 estabilidad DA-2* + EC2) y
  pantalla anclada (empotramiento apoyo libre + ancla/bulbo + EC2).
- **Añadido** a `cimentaciones/` — losa de cimentación (raft) sobre lecho elástico.
- Corrección: `add_member_dist_load` con coordenadas locales (muro/pantalla).

## [0.1.0] — 2026-06-21
- Primera versión empaquetada: `barras` (EC3), `laminas` (losa/flat/incl/muro de carga,
  EC2), `cimentaciones` (zapata), `bielas-tirantes` (encepado), `pilotes`. Agente
  `ingeniero-estructurista` + skill `motor-calculo-estructural`.

---

## Primera tanda COMPLETADA (casos 1–10)
- **Caso 10 cerrado** (v0.12.0): clasificador/enrutador **multi-elemento** +
  orquestador integrado del edificio (`run_all_edificio`). Por primera vez el
  motor itera TODO un IFC, clasifica y enruta cada elemento, y consolida un índice
  del edificio. **INC-03 RESUELTO**.
- Estado del backlog tras la primera tanda: INC-01 ✅, INC-02 ✅, **INC-03 ✅**,
  INC-04/05 mitigadas (prácticas de empaquetado/edición), INC-06 ✅ para perfiles
  de catálogo.

## Pendiente (segunda tanda — casos 11+)
- Módulos aún no construidos: **pantallas a cortante + sísmico EC8**,
  **Mononobe-Okabe** (empuje sísmico en contención), **pretensado**, **análisis
  no-lineal**. Requieren ampliar el motor (no solo el parser): nuevos módulos de
  cálculo y sus verificaciones.

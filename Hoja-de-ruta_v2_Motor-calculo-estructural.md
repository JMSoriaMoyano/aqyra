# Hoja de ruta v3.0 — Motor de cálculo estructural (Estructurando)

**Estado a 21/06/2026 · plugin `motor-calculo-estructural` v0.12.0.** Núcleo estable +
catálogo de casos de uso que crece por un **programa de aprendizaje incremental**. La
**primera tanda (10 casos)** está cerrada: del elemento aislado al **edificio integrado
multi-elemento**, con lectura de **IFC ortodoxo** (entidades estándar del dominio de
análisis estructural) en todos los módulos y **clasificación/enrutado multi-elemento**
(cierre de INC-03). Esta versión fija el **estado del arte** y abre **dos direcciones**
de trabajo en paralelo.

> Leyenda de estado: ✅ implementado y validado · 🔜 siguiente · ⬜ pendiente.

---

## 1. Dónde estamos (estado del arte)

| Capacidad | Estado |
|---|---|
| IFC → modelo neutro → solver → verificación → memoria | ✅ Consolidado y validado |
| **Lectura de IFC ortodoxo** (`parse_ortodoxo()`+`parse_auto()` en todos los módulos; Pset de respaldo) | ✅ Hecho (casos 1–9) |
| **DB de perfiles** (`perfiles_db`): I-shape, rectangular y circular, prioridad a catálogo | ✅ Hecho |
| Barras 1D (pórtico acero) EC3 + validación cruzada anaStruct | ✅ Hecho |
| Láminas 2D (placa MITC4) certificadas vs Timoshenko | ✅ Hecho |
| Losa sobre vigas · losa plana + punzonamiento (comprobación **y dimensionamiento**) · cubierta inclinada + membrana | ✅ Hecho |
| Muro de carga (esbeltez EC2 columna modelo §5.8.8, N-M) | ✅ Hecho |
| Fisuración EC2 §7.3 (con φ dispuesto), flecha ELS, cuantías | ✅ Hecho |
| Muelles de suelo (Winkler) · **zapata** · **losa de cimentación/raft** (EC7 + EC2) | ✅ Hecho |
| **Bielas y tirantes** (regiones D, EC2 §6.5) — encepados | ✅ Hecho |
| **Pilote** (EC7 axil + lateral viga-muelles + EC2) | ✅ Hecho |
| **Muro de contención ménsula** y **pantalla anclada** (EC7 DA-2* + EC2 + anclajes) | ✅ Hecho |
| **Viga mixta acero-hormigón / forjado colaborante (EC4)** | ✅ Hecho |
| **Clasificador/enrutador MULTI-ELEMENTO + orquestador integrado de edificio** (itera todo el IFC, enruta cada elemento, consolida) | ✅ Hecho (caso 10, INC-03 cerrado) |
| Visualización (diagramas, mapas de color, vistas 3D) + memoria Word | ✅ Hecho |
| **Pantallas/núcleos a cortante + sísmico EC8** (fuerzas laterales / modal espectral) | 🔜 Dirección 1 |
| **Pretensado (EC2 §5.10)** — inicio de la tipología | 🔜 Dirección 1 |
| **Puente IFC físico (BIM real) → modelo analítico** (`puente_analitico`: eje/sección/material desde geometría + grafo de nudos) | ✅ Hecho (caso R1, apertura Dirección 2, v0.14.0) |
| Sismo en contención (Mononobe-Okabe), anclas múltiples, fases de excavación | ⬜ Pendiente |
| No-lineal / 2º orden global, fuego, fatiga, uniones | ⬜ Pendiente |

Conclusión: cubierto el **edificio convencional completo de hormigón y acero** (de la
cubierta a la cimentación, superficial y profunda), la **contención de tierras** (muro
ménsula y pantalla anclada) y la **integración multi-elemento** de un edificio en un mismo
IFC. La entrada hasta ahora ha sido siempre **IFC ortodoxo** (dominio de análisis,
sintético). Las dos direcciones nuevas amplían (1) **qué se calcula** y (2) **qué entra**.

---

## 2. Enfoque: núcleo estable + catálogo + programa de aprendizaje

- **Núcleo** (estable, validado, se toca poco): geometría, FE, combinaciones, biblioteca de
  verificación EC, salidas y validación.
- **Catálogo de casos** (crece sin fin): cada caso es una instancia de una *receta*
  repetible (§4) que consume el núcleo; añadir uno no rompe los anteriores.
- **Programa de aprendizaje** (mecanismo de crecimiento, consolidado en la 1ª tanda): cada
  caso se desarrolla en **un hilo** sobre un IFC del caso y deja el plugin endurecido. Tres
  documentos arrastran el conocimiento entre hilos:
  - `Casos-de-uso/PROGRAMA-aprendizaje.md` — la escalera de casos y el protocolo (DoD).
  - `Casos-de-uso/REPOSITORIO-aprendizaje.md` — lecciones, backlog de incidencias y métricas.
  - `Casos-de-uso/CHANGELOG-plugin.md` — versiones y correcciones del plugin (SemVer).
  - `criterios-despacho.md` (raíz) — criterios del despacho (materiales, AN, flechas, recubrimientos).

El **agente `ingeniero-estructurista`** clasifica el elemento/caso desde el IFC y enruta al
módulo; el catálogo crece sin reescribir el agente.

---

## 3. El núcleo reutilizable (consolidado)

1. **Lectura IFC → modelo neutro** (IfcOpenShell): vía **ortodoxa prioritaria**
   (`IfcMaterialProfileSet`/`IfcIShapeProfileDef`·`IfcRectangleProfileDef`·`IfcCircleProfileDef`,
   `IfcStructuralCurve/Surface/PointAction`, `IfcStructuralLoadGroup`, `IfcBoundaryNodeCondition`)
   con Pset propio de respaldo. `perfiles_db` con prioridad a catálogo.
2. **Clasificador/enrutador multi-elemento** (`scripts/clasificador.py`): itera TODO el IFC,
   clasifica cada barra/superficie por geometría+sección+material+lecho/carga de cabeza,
   resuelve asociaciones (viga↔losa, pilar↔zapata) y extrae un **sub-IFC por subsistema**.
3. **Orquestador integrado** (`scripts/run_all_edificio.py`): invoca el `run_all*` de cada
   subsistema en subproceso aislado (módulos homónimos) y consolida el índice del edificio.
4. **Solver FE** (PyNite): barras 1D, láminas 2D (cualquier orientación) y **muelles** (lecho
   elástico, pilote/pantalla). *(Para no-lineal/sísmico avanzado se valorará OpenSeesPy — §8.)*
5. **Acciones y combinaciones** EC0/EC1 con Anejo Nacional.
6. **Biblioteca de verificación** (lo más valioso, crece por cláusulas): EC2 (flexión,
   cortante, **punzonamiento + dimensionamiento**, fisuración, esbeltez columna modelo,
   cuantías), EC3 (secciones, pandeo), **EC4** (viga mixta: b_eff, M_Rd con grado de conexión,
   conectores, fases, flecha), **EC7** (empujes, estabilidad B′ Meyerhof, capacidad de pilote,
   empotramiento de pantalla, anclajes). *(Futuro: EC8 sísmico, EC2 §5.10 pretensado.)*
7. **Salidas**: diagramas, mapas de color, vistas 3D, **memoria Word**.
8. **Arnés de validación**: solución analítica o solver independiente por tipo (Timoshenko
   para placa, anaStruct para barras, formas cerradas de empujes), equilibrio global ~0 %.

---

## 4. La "receta" de un caso de uso (patrón repetible)

1. **Generador IFC de prueba** del caso (banco de pruebas).
2. **Parser** → modelo neutro (extiende el esquema si hace falta).
3. **Clasificar/enrutar** (multi-elemento si procede) antes de resolver.
4. **Solver**: idealización y FE específicos (apoyos, cargas, malla).
5. **Verificación**: la(s) cláusula(s) EC propias (reutiliza la biblioteca).
6. **Validación**: analítica/cruzada + equilibrio.
7. **Visualización + memoria** Word del caso, y **registro** (lección + métricas + CHANGELOG + versión).

---

## 5. La primera tanda — escalera de 10 casos (COMPLETADA)

| # | Caso | Módulos | Plugin |
|---|---|---|---|
| 1 | Pórtico de acero biarticulado | `barras` (EC3) | v0.3.1 |
| 2 | Forjado: losa sobre vigas de acero | `laminas`+`barras` | v0.4.0 |
| 3 | Losa plana sobre pilares + punzonamiento | `laminas` (flat) | v0.5.0 |
| 4 | Cubierta / forjado inclinado | `laminas` (incl) | v0.6.0 |
| 5 | Soporte + zapata aislada | `cimentaciones`+`barras` | v0.7.0 |
| 6 | Forjado colaborante / viga mixta | `mixtas` (EC4) | v0.8.0 |
| 7 | Muro de carga + muro de contención ménsula | `laminas`+`muros-contencion` | v0.9.0 |
| 8 | Losa de cimentación (raft) multipilar | `cimentaciones` (raft) | v0.10.0 |
| 9 | Cimentación profunda: pilote + encepado + pantalla | `pilotes`+`bielas-tirantes`+`muros-contencion` | v0.11.0 |
| 10 | **Edificio integrado** (pórtico+mixta+muro+cimentación) | **clasificador/enrutador + todos** | v0.12.0 |

Backlog cerrado en la tanda: **INC-01/02** (parser ortodoxo de sección y cargas), **INC-03**
(multi-elemento), **INC-06** (perfiles de catálogo); **INC-04/05** mitigadas (edición por
heredoc + `ast.parse`; empaquetado sin `node_modules`/`__pycache__`).

---

## 6. NUEVOS OBJETIVOS — dos direcciones

A partir de aquí el motor crece en **dos ejes ortogonales y complementarios**: la
**Dirección 1** amplía *qué se calcula* (nuevos tipos de elemento y de análisis); la
**Dirección 2** amplía *qué entra* (modelos IFC reales de BIM, no sólo IFC de análisis
hechos a mano). Ambas alimentan el mismo núcleo y se desarrollan con la misma receta del §4.

### Dirección 1 — Segunda tanda de casos (11–15): estabilización lateral + sísmico + inicio del pretensado

> Empieza por el sistema de estabilización lateral y el sísmico, y a continuación **inicia
> la tipología de elementos pretensados** (4 casos). Algunos casos abren biblioteca EC nueva
> (EC8, EC2 §5.10); el caso 15 enlaza hacia tableros/puentes.

- 🔜 **Caso 11 — Pantallas / núcleos a cortante + sísmico EC8 (fuerzas laterales / modal
  espectral).** Sistema de estabilización lateral. Pantalla de hormigón trabajando a cortante
  en su plano (membrana + **elementos de borde** confinados) y **núcleo** (pantallas
  acopladas). Análisis sísmico EC8 (EN 1998-1): masas sísmicas, **espectro de respuesta**,
  **método de fuerzas laterales equivalentes** y **análisis modal espectral** (PyNite tiene
  modal), combinación modal (SRSS/CQC), factor de comportamiento *q*, combinación sísmica
  (EC0 §6.4.3.4). Verificación: cortante en alma y armadura de borde (EC8 §5.4.3.4), **deriva
  entre plantas** (limitación de daño). Nuevo módulo `sismico/` (o `pantallas/`) + arranque de
  la **biblioteca EC8**. *Abre la familia sísmica.*
- 🔜 **Caso 12 — Inicio del pretensado: viga postesada isostática (EC2 §5.10).** Primer
  elemento pretensado. Trazado parabólico; pretensado como **cargas equivalentes** (load
  balancing) y como fuerza+excentricidad; **pérdidas** instantáneas (rozamiento, penetración
  de cuña, acortamiento elástico) y diferidas (retracción, fluencia, relajación) §5.10.6.
  Verificación de **tensiones en transferencia y en servicio** (límites de compresión/tracción,
  descompresión), **ELU de flexión** con armadura activa+pasiva y fisuración. Nuevo módulo
  `pretensado/` + biblioteca **EC2 §5.10**.
- ⬜ **Caso 13 — Losa postesada (post-tensioned flat slab).** Tendones en banda y
  distribuidos; **balance de cargas** 2D; **punzonamiento con efecto favorable del pretensado**
  (EC2 §6.4.4: σcp + componente vertical de los tendones); tensiones, ELU y flecha con
  pretensado. Reutiliza `laminas` (flat) + `pretensado/`.
- ⬜ **Caso 14 — Viga pretensada hiperestática (continua).** Tendón en viga de 2–3 vanos:
  **momentos hiperestáticos (secundarios) de pretensado**, línea de presiones y concordancia,
  redistribución, ELU con momentos hiperestáticos y comprobación de tensiones.
- ⬜ **Caso 15 — Tablero de vigas pretensadas prefabricadas + losa in situ.** Sección
  compuesta pretensado–HA por **fases** (pretesado en banco/transferencia, montaje, losa
  fresca sobre la viga sola, sección compuesta en uso). Combina EC2 §5.10 con el esquema de
  fases del EC4 y el ancho eficaz. **Enlaza hacia la tipología de puentes.**

### Dirección 2 — El puente IFC físico (BIM real) → modelo analítico (casos reales)

> Las 10 primeras casos partieron de **IFC ortodoxo** (dominio de análisis, hecho a mano:
> `IfcStructuralCurveMember`, `IfcStructuralSurfaceMember`, cargas y apoyos explícitos). Pero
> los entregables BIM reales son **IFC físicos**: `IfcBeam`/`IfcColumn`/`IfcMember`/`IfcWall`/
> `IfcSlab`/`IfcFooting`/`IfcPile` con **geometría** (sólidos de extrusión/barridos),
> `IfcMaterial(LayerSet/ProfileSet)` y estructura espacial (`IfcBuilding`/`Storey`), **sin
> entidades de análisis y sin cargas**. (El incidente del visor lo evidenció: el IFC de
> análisis no tiene geometría que renderizar; el IFC físico sí, pero no tiene modelo de
> análisis.) Resolver ese **puente físico → analítico** es lo que de verdad necesita un
> proyecto real.

**Nuevo módulo `puente_analitico/` (físico → modelo neutro).** Convierte un IFC físico en el
mismo modelo neutro que el motor ya consume, para que el clasificador/enrutador y los solvers
existentes apliquen sin cambios:

1. **Extracción geométrica**: ejes y perfiles de elementos lineales desde el sólido de
   barrido (`IfcExtrudedAreaSolid` → directriz + `IfcProfileDef`) — exacto para prismáticos,
   ligero; superficie media y espesor de muros/losas desde `IfcMaterialLayerSet`/geometría.
   *(Para geometría compleja, `ifcopenshell.geom`/OpenCASCADE como respaldo.)*
2. **Idealización**: eje baricéntrico de barras; clasificación viga/pilar (horizontal/vertical)
   y muro/losa (vertical/horizontal); zapatas/pilotes desde `IfcFooting`/`IfcPile`.
3. **Conectividad / nodos**: grafo de uniones por intersección de ejes con **tolerancia**,
   troceado de barras en cruces, fusión de nodos coincidentes, **tratamiento de offsets/
   excentricidades** (eje físico vs eje analítico). *(El punto difícil y de mayor valor.)*
4. **Apoyos**: inferidos de cimentaciones (zapata→apoyo/Winkler) o del nivel de arranque; o
   leídos de Pset si existe.
5. **Cargas (el IFC físico no las trae)**: peso propio de geometría×densidad del material +
   **hipótesis de carga por uso** (sobrecargas por ocupación, definidas aparte/Pset/fichero
   de cargas compañero). Se documenta como hipótesis a confirmar.
6. **Salida**: modelo neutro estándar → clasificador → solvers existentes.

**Casos reales (serie R):**

- ✅ **R1 — Pórtico físico real (v0.14.0).** IFC con `IfcColumn`+`IfcBeam` (Body, perfil de
  acero). El módulo `puente_analitico/` deriva las 3 barras y los 4 nodos por intersección de
  ejes (eje = directriz del barrido vía `get_local_placement`+`Depth`; sección/material de
  `IfcMaterialProfileSetUsage`; apoyos/cargas de hipótesis en Pset) y enruta a `barras` (EC3),
  **reproduciendo el caso 1** (93,60 kN/apoyo; HEB 200 32,0 %; IPE 330 44,6 %). *Validada la
  extracción de eje/sección/material y la generación de nodos. Offsets/excentricidades → R5
  (INC-07).*
- ⬜ **R2 — Forjado físico.** `IfcSlab` sobre `IfcBeam`/`IfcColumn`: superficie media +
  barras → `laminas`+`barras`. *Valida superficie media, espesor de `IfcMaterialLayerSet`,
  reparto.*
- ⬜ **R3 — Muro + zapata físicos.** `IfcWall` + `IfcFooting`: muro de carga + cimentación.
  *Valida clasificación de superficies físicas y la cadena muro/pilar→cimiento.*
- ✅ **R4 — Edificio físico completo (el "caso 10 real") (v0.19.0).** Varios `IfcColumn`/
  `IfcBeam`/`IfcSlab`/`IfcWall`/`IfcFooting` en estructura espacial por plantas: de un
  **único IFC físico** el puente deriva TODO el modelo analítico (barras + superficies
  horizontales/verticales + cimientos + asociaciones) y un **clasificador/enrutador
  multi-elemento** (`run_all_real_edificio.py`) enruta cada elemento a su módulo
  (barras/mixtas/láminas/cimentaciones, subproceso por subsistema). **Reproduce el caso 10
  desde un IFC físico** (pórtico 22,9/30,5 %; mixta M_Ed 333, η=0,66; muro λ=52, N-M 45 %;
  zapata σ_ef≤R_d). *Cierra la tubería físico→analítico→cálculo de extremo a extremo.
  Offsets/geometría "real-sucia" → R5 (INC-07).*
- ✅ **R5 — IFC físico "real-sucio" de un exportador concreto (v0.21.0).** `puente.py`
  endurecido (retrocompatible): recuperación del eje analítico por **`CardinalPoint`**,
  grafo de nudos con **snap parametrizable + bridging + troceo T/X con offset**, **filtrado**
  de no-estructurales y de componentes no conectadas, **alias de perfiles** (Euronorm) y
  **factor de unidades** del `IfcUnitAssignment`. Reproduce el caso 1/R1 desde un IFC
  real-sucio (93,60 kN/apoyo; HEB 200 31,8 %; IPE 330 44,8 %); R1–R4 idénticos en IFC
  limpio. **Cierra INC-07 y la serie R / Dirección 2.** (Pendiente menor: `IfcPile` físico.)

> Relación entre direcciones: la **D1** crece la **biblioteca de verificación** (EC8, §5.10);
> la **D2** crece la **lectura/idealización** (físico→analítico). Cuando converjan, un IFC
> físico real de un edificio se calculará de extremo a extremo (R4) con todos los tipos de
> elemento (incl. pantallas/pretensado).

---

## 7. Orden recomendado

1. ✅ Primera tanda (casos 1–10) — del elemento al edificio integrado multi-elemento.
2. 🔜 **D1 · Caso 11** — pantallas/núcleos a cortante + sísmico EC8. *Mayor valor: abre el sísmico.*
3. ✅ **D2 · Caso R1** — puente IFC físico→analítico en el pórtico (la base de la D2, v0.14.0). *Hecho, en paralelo a la D1.*
4. 🔜 **D1 · Caso 12** — viga postesada isostática (inicio del pretensado).
5. ⬜ D1 · Casos 13–15 (losa postesada → hiperestática → tablero prefabricado) · D2 · R2–R4.
6. ⬜ Extensiones de contención (Mononobe-Okabe, anclas múltiples) y avanzados (no-lineal/2º
   orden, fuego, fatiga, uniones).

*(D1 y D2 avanzan en paralelo; R1 puede arrancar a la vez que el caso 11.)*

---

## 8. Límites del motor lineal y cuándo escalar

- El núcleo es **elástico-lineal**: cubre esfuerzos, dimensionamiento y ELU/ELS de la inmensa
  mayoría de la edificación.
- **Sísmico EC8 (D1)**: el análisis **modal espectral** y de **fuerzas laterales** es lineal y
  cabe en el núcleo (PyNite tiene modal). El **sísmico no-lineal** (pushover, time-history)
  requeriría **OpenSeesPy**.
- **Pretensado (D1)**: como cargas equivalentes + pérdidas cabe en el núcleo lineal; la
  no-linealidad de la sección en ELU se trata por fibras (como en EC4).
- **Puente físico→analítico (D2)**: el reto es de **lectura geométrica y construcción del
  grafo de conectividad** (tolerancias, offsets), no del solver. La geometría exacta de
  barridos prismáticos es ligera; la compleja puede apoyarse en `ifcopenshell.geom`.
- **No-lineal, 2º orden global avanzado, fatiga, fuego** pueden requerir un solver más
  potente (p. ej. **OpenSeesPy**) o módulos específicos.
- Regla invariable: **todo resultado es de predimensionado y debe ser revisado y firmado por
  técnico competente.** Los NDP del Anejo Nacional se marcan **[confirmar AN]**.

---

## 9. Encaje del plugin + agente "ingeniero-estructurista"

- El **núcleo** (solver + biblioteca de verificación + salidas + clasificador/orquestador)
  vive en el plugin como código versionado.
- Cada **caso** es un módulo del catálogo (`scripts/<grupo>/`) que sigue la receta del §4.
- El **agente** (1) **clasifica** desde el IFC, (2) **enruta**, (3) **orquesta** la receta
  (incl. multi-elemento), (4) **acumula criterios** del despacho en memoria.
- Estado del paquete: **`motor-calculo-estructural.plugin` v0.14.0**, con `barras/`,
  `laminas/`, `cimentaciones/` (zapata+raft), `muros-contencion/` (ménsula+pantalla),
  `mixtas/` (EC4), `bielas-tirantes/`, `pilotes/`, el **`clasificador.py`**,
  **`run_all_edificio.py`** y el nuevo **`puente_analitico/`** (físico→analítico, Dirección 2),
  más el agente, la skill y `referencias/`.
- **Próximos módulos**: `sismico/`(+`pantallas/`), `pretensado/` (Dirección 1); y, en la
  Dirección 2, ampliar `puente_analitico/` a `IfcSlab`/`IfcWall`/`IfcFooting`/`IfcPile`
  (R2–R4) y endurecer offsets/geometría real-sucia (R5, INC-07).

---

## 10. Resumen

De "fases" a **"núcleo estable + catálogo de casos"** crecido por un **programa de
aprendizaje**. La **primera tanda (10 casos)** cierra el edificio convencional de hormigón y
acero —de la cubierta a la cimentación, superficial y profunda—, la contención de tierras y
la **integración multi-elemento** (un edificio en un IFC, clasificado y enrutado elemento a
elemento). A partir de aquí, **dos direcciones**: **(1)** ampliar el cálculo —pantallas/
núcleos a cortante + **sísmico EC8** y el **inicio del pretensado** (casos 11–15)— y **(2)**
resolver el **puente IFC físico (BIM real) → modelo analítico** con casos reales (serie R),
para pasar de IFC de análisis hechos a mano a modelos de proyecto reales. Ambas sobre el mismo
plugin que el agente orquesta.

---

## Registro de versiones de la hoja de ruta

- **v3.0 (21/06/2026):** estado del arte tras cerrar la **primera tanda (10 casos)** y el
  plugin **v0.12.0** (clasificador/enrutador multi-elemento + orquestador integrado; lectura
  de IFC ortodoxo en todos los módulos; INC-03 cerrado). Se fijan **dos direcciones**:
  (1) segunda tanda de casos 11–15 (pantallas/núcleos a cortante + sísmico EC8; inicio del
  pretensado) y (2) puente **IFC físico → modelo analítico** con casos reales (serie R) y el
  módulo `puente_analitico/`.
- **v2.2 (21/06/2026):** añadida la viga mixta acero-hormigón / forjado colaborante (EC4);
  plugin v0.3.0 con el grupo `mixtas/`.
- **v2.1 (21/06/2026):** estado integrado tras empaquetar el plugin v0.2.0 — añadidos
  losa de cimentación (raft), muro de contención en ménsula y pantalla anclada; muelles de
  suelo y EC7 consolidados en el núcleo.
- **v2.0:** reorientación de "fases" a **"núcleo estable + catálogo de casos"**.

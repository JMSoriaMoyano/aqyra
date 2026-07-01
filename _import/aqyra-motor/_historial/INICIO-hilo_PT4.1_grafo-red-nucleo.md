# Texto de inicio — PT 4.1 (Ola 4): extraer el grafo de red + utilidades IFC al núcleo (H1)

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 4.1 de la Ola 4**: **extraer al núcleo el grafo de red
(nodos+tramos) y las utilidades IFC compartidas** que hoy viven embebidas en el lado de estructuras,
para que una disciplina nueva (instalaciones) "enchufe sin tocar el núcleo". Es el **hueco H1** de la
verificación de la Ola 1 y el **arranque de la Ola 4**. Resuelve además la **decisión abierta nº4** de
la hoja de ruta ("¿dónde vive el motor hidráulico de red?"). Trabaja con el agente
`ingeniero-estructurista` (es quien conoce el código a refactorizar) y **no rompas estructuras**.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` (v2.3) — §4 (núcleo y contratos C1, CN-1, CN-2 y CN-3; "capacidad
   transversal emergente: motor hidráulico de red"), §6 (olas; este hilo es Ola 4) y la decisión
   abierta nº4.
2. `Nucleo-transversal/Verificacion-Ola1.md` — huecos **H1** (este PT), H2 (IFC MEP) y H3 (bases de
   demanda); y el dry-run de "enchufe" de `instalaciones` (§5).
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §2 (esquema y convenciones), §3 (modelos
   hermanos), §4 (dominio MEP: `IfcSystem`/`IfcFlowSegment/Fitting/Terminal`/`IfcDistributionPort`,
   modelo neutro de red `nodos`+`tramos`+`terminales`+`fuentes`) y §6 (checklist C1).
4. `criterios-despacho.md`, `Casos-de-uso/REPOSITORIO-aprendizaje.md` (lección R5/INC-07 del grafo de
   nudos; INC-09 empaquetado) y `Casos-de-uso/CHANGELOG-plugin.md`.
5. **Código de partida en el plugin v0.22.1** (`motor-calculo-estructural-v0.22.1.plugin`): el grafo
   topológico está en `scripts/puente_analitico/puente.py` (R5: construcción de nudos por
   intersección con **tolerancia/snap** parametrizable, bridging de huecos/solapes, **troceo en T/X**,
   filtrado de no-estructurales por union-find, **factor de unidades** del `IfcUnitAssignment`); las
   utilidades de lectura IFC (`_psets`, resolución de material/sección, `factor de unidades`) están
   **duplicadas** en los parsers (`barras/ifc_to_model.py`, `laminas/ifc_to_model_3d.py`, etc.).

**Objetivo y alcance (qué hay que hacer):**

1. **Definir la frontera de lo reutilizable** (lo común a estructuras e instalaciones), separándolo
   del solver (que es específico de cada disciplina y **NO se toca**):
   - **(a) Utilidades IFC del núcleo:** `_psets`, **factor de unidades** (`IfcUnitAssignment`,
     mm→m), y los *helpers* de lectura genéricos. Hoy duplicados → centralizar.
   - **(b) Grafo topológico nodos+tramos:** construcción por **intersección/puertos** con
     tolerancia, **snap**, bridging y **troceo en T/X**, y la limpieza por **componentes
     conexas** (union-find). Hoy dentro de `puente.py`.
   - **Fuera del núcleo (se queda en cada disciplina):** el solver (FEM estructural vs.
     hidráulico/eléctrico/térmico) y la verificación normativa.
2. **Decidir dónde vive** (decisión abierta nº4) y dejarlo documentado. *Recomendación de partida:*
   un **módulo/skill transversal** reutilizable (p. ej. en `iso19650-openbim` o como módulo de
   núcleo compartido) que exponga (a) y (b) con una **API estable**; el grafo debe ser
   **agnóstico al solver** (devuelve `nodos`+`tramos`/`barras` + topología; quien calcula es la
   disciplina).
3. **Refactorizar `puente_analitico` para consumir el núcleo** manteniendo
   **retrocompatibilidad total**: los casos **R1–R5** deben reproducir su `modelo_neutro.json`
   **byte a byte** (regresión) y los casos 1/5/7/10 seguir cumpliendo. Patrón: extraer sin cambiar
   comportamiento (adaptador fino si hace falta), no reescribir.
4. **Dejar el "gancho" para H2 (no construir MEP aquí):** la API del grafo debe poder alimentar un
   futuro `ifc_to_model_mep.py` (nodos+tramos por `IfcDistributionPort`/`IfcRelConnectsPorts`),
   pero **este PT no implementa el dominio MEP** (eso es H2) ni el solver hidráulico.

**Entregable:**
- El **módulo/skill del núcleo** con (a) utilidades IFC y (b) grafo de red, con su **mini-API
  documentada** y un **micro-test** del grafo (intersección/snap/troceo) + una **prueba de
  regresión** de estructuras (R1–R5 idénticos; casos 1/5/7/10 CUMPLEN).
- **Actualizar C1** (documentar las utilidades del núcleo como API compartida y el origen del grafo)
  y, si procede, la decisión abierta nº4 en la hoja de ruta.
- **Registrar**: lección en `REPOSITORIO-aprendizaje.md` (+ fila/INC si aplica), entrada SemVer en
  `CHANGELOG-plugin.md`, y **subir versión + reempaquetar** el `.plugin`.
- **Puerta de calidad obligatoria** antes de dar por bueno el paquete:
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin
  --ref motor-calculo-estructural-v0.22.1.plugin` (debe dar **APTO**, exit 0).

**Notas de método:** las herramientas de fichero (Read/Write/Edit) son la **fuente de verdad** de la
carpeta conectada (el shell del sandbox puede ver copias **truncadas** de markdown — no las edites por
shell). Toolchain Python en `/tmp/pylibs` → ejecuta con `PYTHONPATH=/tmp/pylibs`; valida todo el
código con `ast.parse`; el análisis puede superar ~45 s → ejecuta por partes. El `.plugin` de la raíz
puede estar bloqueado por el host → **construye el ZIP en `/tmp` y cópialo con `cat > destino`**, con
**nombre versionado** (no sobrescribas), excluyendo `__pycache__`/`node_modules`/`*.pyc`. Empaquetado
**acumulativo** partiendo de **v0.22.1** (preserva `sismico/`, `pretensado/`, `puente_analitico/`
R1–R5, clasificador y orquestadores). Todo es **predimensionado, a revisar y firmar por técnico
competente**; NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos y el `puente.py` de v0.22.1, y proponiendo la **frontera de la API**
(qué entra al núcleo y qué se queda en la disciplina) antes de mover una sola línea.

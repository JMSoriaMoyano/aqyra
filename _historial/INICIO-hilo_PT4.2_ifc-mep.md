# Texto de inicio — PT 4.2 (Ola 4): dominio IFC MEP + modelo neutro de red (H2)

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 4.2 de la Ola 4**: **abrir el dominio IFC MEP** — un parser
físico→neutro de **red** (`ifc_to_model_mep.py`), su **generador de IFC MEP de prueba** y la
**validación de red** (continuidad/terminales), **reutilizando el núcleo transversal** ya extraído en
el PT 4.1 (`scripts/nucleo/`: `ifc_utils` + `grafo_red`) **sin tocarlo**. Es el **hueco H2** de la
verificación de la Ola 1. Trabaja con el agente `ingeniero-estructurista` (conoce el núcleo y el
patrón de parsers) y **no rompas estructuras** ni el núcleo. **Este PT NO implementa el solver de red**
(hidráulico Darcy/Manning, eléctrico, térmico): eso nace después con la disciplina `instalaciones`.
H2 es solo C1 para MEP (leer/validar/escribir IFC MEP + emitir el modelo neutro de red).

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` — §3 (mapa de plugins; `iso19650-openbim` "a ampliar a
   MEP"; convención de `description` ≤ 500), §4 (núcleo y "capacidad transversal emergente: motor
   hidráulico de red"), §6 (olas; este hilo es Ola 4) y §8 (decisiones abiertas; nº4 ya resuelta).
2. `Nucleo-transversal/Verificacion-Ola1.md` — huecos **H2** (este PT) y H3 (bases de demanda); y el
   dry-run de "enchufe" de `instalaciones` (§5, punto 1: la vía MEP).
3. `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` — §3bis (la **API del núcleo**:
   `ifc_utils.psets/length_scale/pset_value`, `grafo_red.construir_grafo`), §4 (dominio MEP:
   entidades `IfcSystem`/`IfcDistributionSystem`, `IfcFlowSegment/Fitting/Terminal/Controller/
   MovingDevice`, `IfcDistributionPort`+`IfcRelConnectsPorts`; **modelo neutro de red**
   `nodos`+`tramos`+`terminales`+`fuentes`) y §6 (checklist C1 para disciplina nueva).
4. `criterios-despacho.md`, `Casos-de-uso/REPOSITORIO-aprendizaje.md` (lecciones **PT 4.1** —grafo+
   utilidades al núcleo, frontera núcleo/disciplina, gancho H2—, R5/INC-07 del grafo de nudos, INC-09
   empaquetado) y `Casos-de-uso/CHANGELOG-plugin.md` (entrada v0.23.0).
5. **Núcleo de partida (PT 4.1, v0.23.0):** `scripts/nucleo/grafo_red.py` expone
   `construir_grafo(segmentos, tol)` (segmentos genéricos `{p0,p1,payload}` → `{nodos,tramos,
   métricas}`; troceo T/X, snap, métricas) y `filtrar_componentes_desconectadas(nodos, tramos,
   es_ancla)` (union-find genérico; **para MEP `es_ancla` = nudo fuente/acometida**);
   `scripts/nucleo/ifc_utils.py` expone `psets`, `length_scale` (factor de unidades), `pset_value` y
   álgebra 4×4. Hay micro-test (`scripts/nucleo/test_grafo_red.py`) y `scripts/nucleo/README.md`.

**Objetivo y alcance (qué hay que hacer):**

1. **Parser `ifc_to_model_mep.py` (físico→neutro de red).** Lee `IfcDistributionSystem` (tipo:
   FIRESUPPRESSION/ELECTRICAL/AIRCONDITIONING…), los `IfcDistributionElement`
   (`IfcFlowSegment` = tubo/conducto/cable bandeja, `IfcFlowFitting` = codo/te, `IfcFlowTerminal` =
   BIE/rociador/difusor/luminaria/enchufe, `IfcFlowController`, `IfcFlowMovingDevice`) y la
   conectividad por **`IfcDistributionPort` + `IfcRelConnectsPorts`** (con respaldo por geometría/
   intersección si faltan puertos). **Reutiliza el núcleo:** `ifc_utils` para Psets/unidades y
   `grafo_red.construir_grafo` para los `nodos`+`tramos` (los `IfcFlowSegment` aportan los segmentos;
   los puertos/extremos, los nudos). Emite el **modelo neutro de red** de C1 §4
   (`unidades` SI declaradas, `sistema`, `nodos`, `tramos`, `terminales`, `fuentes`), **modelo
   hermano** del estructural (mismas convenciones, claves nuevas, sin redefinir las existentes).
2. **Generador de IFC MEP de prueba** (banco, análogo a `generate_test_ifc*`): al menos una red PCI
   sencilla (fuente → tramos → 2-3 terminales BIE) para validar el parser de extremo a extremo.
3. **Validación de red** (arnés propio, análogo al de equilibrio estructural): **continuidad**
   (grafo conexo desde la fuente), **terminales conectados**, sin **componentes huérfanas**
   (reutiliza `grafo_red.filtrar_componentes_desconectadas` con `es_ancla`=fuente), unidades SI
   coherentes. Sin cálculo hidráulico.
4. **Ampliar `iso19650-openbim` a MEP** (E/S IFC): que `ifc-create`/`ifc-validate` **conozcan
   entidades MEP** (crear red de prueba; validar nomenclatura/Psets `Pset_*`/clasificación bsDD para
   MEP; escribir Psets de resultado de red cuando los haya). Si el alcance del hilo se hace grande,
   prioriza el parser + validación (1-3) y deja `ifc-create/validate` MEP como sub-entrega.
5. **Gancho a H3 (no construir bases de demanda aquí):** el modelo neutro de red debe poder recibir
   más adelante las **demandas** (caudales/potencias/ocupación) por terminal/sistema; deja la clave
   prevista pero **no** implementes el módulo de demanda (eso es H3).

**Decisión a resolver y documentar (empaquetado de MEP):** ¿dónde vive `ifc_to_model_mep.py` y la
validación de red — en **`iso19650-openbim`** (capa IFC transversal, lo natural según §3) o en el
futuro plugin **`instalaciones`**? Y, en consecuencia, **cómo accede al núcleo** `scripts/nucleo/`
(hoy incubado en `motor-calculo-estructural`): esto fuerza/acelera **promover el núcleo a módulo
compartido** (decisión nº4, ya prevista). Propón la frontera y el plugin que reempaqueta **antes de
mover una línea**. Ojo: la puerta de calidad reempaqueta el plugin que toques (probablemente
`iso19650-openbim`), no `motor-calculo-estructural`.

**Entregable:**
- `ifc_to_model_mep.py` (consume el núcleo, **no** lo modifica) + generador de IFC MEP de prueba +
  validación de red, con un **micro-test** de la red (continuidad/terminales/troceo por puertos) y un
  caso de prueba MEP que pase de extremo a extremo.
- **Actualizar C1** (§4: marcar el parser MEP como implementado; checklist §6 para la vía MEP) y, si
  procede, `Verificacion-Ola1.md` (H2 → ✅) y la hoja de ruta.
- **Registrar:** lección en `REPOSITORIO-aprendizaje.md` (+ fila/INC si aplica), entrada SemVer en el
  **CHANGELOG del plugin que toques**, y **subir versión + reempaquetar** ese `.plugin`.
- **Puerta de calidad obligatoria** antes de dar por bueno el paquete:
  `PYTHONPATH=/tmp/pylibs python3 Nucleo-transversal/verificar_empaquetado.py <nuevo>.plugin
  --ref <previo>.plugin` (APTO, exit 0). Recuerda: `description` ≤ 500 caracteres; usa
  `--allow-shrink <rutas>` solo para encogimientos **intencionados y auditados**.

**Notas de método:** las herramientas de fichero (Read/Write/Edit) son la **fuente de verdad** de la
carpeta conectada (el shell del sandbox puede ver copias **truncadas** de markdown y de `.py` recién
editados — no los edites por shell; si necesitas ejecutar un script editado, **cópialo a `/tmp` y
córrelo desde ahí**). Toolchain Python en `/tmp/pylibs` (ifcopenshell 0.8.5) → ejecuta con
`PYTHONPATH=/tmp/pylibs`; valida todo el código con `ast.parse`; el análisis puede superar ~45 s →
ejecuta por partes. El `.plugin` de la raíz puede estar bloqueado por el host → **construye el ZIP en
`/tmp` y cópialo con `cat > destino`**, con **nombre versionado** (no sobrescribas), excluyendo
`__pycache__`/`node_modules`/`*.pyc`. Empaquetado **acumulativo** desde la última versión íntegra del
plugin que toques. Todo es **predimensionado, a revisar y firmar por técnico competente**; NDP
marcados `[confirmar AN]`.

**Empieza** leyendo los documentos y el núcleo (`scripts/nucleo/`), y **proponiendo la frontera**
(qué entidades MEP mapeas, cómo construyes la red con `grafo_red.construir_grafo`, dónde vive el
parser y qué plugin se reempaqueta) **antes de mover una sola línea**.

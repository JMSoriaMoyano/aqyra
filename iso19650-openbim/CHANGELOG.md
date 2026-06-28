# CHANGELOG — iso19650-openbim.plugin

Registro de versiones del plugin. Formato SemVer. Cada hilo que toque el plugin añade
una entrada y reempaqueta el `.plugin` (puerta `Nucleo-transversal/verificar_empaquetado.py`).

## [0.10.0] — 2026-06-28
- **Evolucion de C1 "apertura de familias P1" (RFC Aqyra-Raiz, 2026-06-28).** UNA sola
  evolucion completa del contrato (no parches) que desbloquea las tres familias del
  Visor/Editor (P1·A edificacion, P1·B trazado, P1·C normativa) sin volver a tocar C1.
  Toda la capacidad entra ENTERA y GENERICA; el cebo construye por slices contra una
  superficie ya estable. **Retrocompatible/aditiva** (estructuras/MEP/lineal/puentes sin
  regresion). Lado compilador (narracion-ifc + scripts/lineal):
  1. **Huecos generalizados** — `spec_to_ifc._practicar_hueco` / `_hueco_horizontal`: via
     UNICA `IfcOpeningElement`+`IfcRelVoidsElement` aplicable a CUALQUIER anfitrion (muro
     -ya-, losa, cubierta/elemento horizontal). El muro se refactoriza a la misma via.
  2. **Catalogo de clases ABIERTO** — `elementos[].ifcClass` (alias historico `.clase`)
     autora CUALQUIER IfcClass concreta del catalogo bsDD del esquema, incl.
     `IfcTransportElement` (ascensor); clases futuras entran sin re-bump.
  3. **Doble clasificacion** — nuevo `narracion-ifc/clasificacion.py`: cada elemento
     autorado lleva `bSDD` (URI) + `Uniclass 2015` (tabla EF) por mapeo DETERMINISTA por
     ifcClass (+PredefinedType), tan determinista como la URI bsDD; fallback por grupo IFC.
     Se aplica a pilares/muros/losas/rampas/escaleras y a `elementos[]` (catalogo).
  4. **Alineaciones completas** — `alineaciones[]` -> `IfcAlignment`. La maquinaria de la
     Ola 5 `scripts/lineal/generate_test_ifc_lineal.py` se REFACTORIZA extrayendo
     `construir_alineacion(model, ctx, ...)` (planta recta/clotoide/curva + alzado
     rasantes/acuerdos + seccion/peralte + georref); el banco de pruebas `main` la reusa
     (test_lineal.py SIN regresion). El puente `narracion-ifc/alineaciones_ifc.py` traduce
     el `alto.json` y delega — NO se reimplementa geometria de alineacion. El IFC resultante
     es legible por `scripts/lineal/ifc_to_model_lineal.py`.
  5. **Esquema `alto.json` FORWARD-OPEN** — `narracion-ifc/spec.schema.json` v0.2:
     `additionalProperties=true` en todos los niveles y documentado (garantia formal de
     "sin mas parches"); documenta `huecos`, `ifcClass`, `alineaciones[]`.
- **Golden unica C1 (Llave 1)** `C1-APERTURA-01` en VERDE: un `alto.json` con huecos en
  losa+muro, un `IfcTransportElement` (ELEVATOR), una alineacion con clotoide+acuerdo
  vertical y doble clasificacion -> compila IFC IFC4X3 valido (losa vaciada, ascensor
  presente, IfcAlignment legible por el parser lineal, bsDD+Uniclass en cada elemento).
  Entregada como artefacto a Aqyra-Raiz para que JM la registre y firme en `Estructurando 2.0`.
- **Nota de versionado (para JM):** skew observado — `versions.lock` ancla 0.8.2, el paquete
  publicado es v0.9.2 (track puentes) y este `plugin.json` de dev iba a 0.7.0. Se propone
  **0.10.0** (siguiente MINOR sobre el head publicado 0.9.2; cambio ADITIVO, C1 sigue v0).
  Reconciliar el numero definitivo al anclar (Llave 2).

## [0.7.0] — 2026-06-22
- **Extension del dominio IFC MEP a ABASTECIMIENTO a presion (PT 6.3, Ola 6 · CIERRE).**
  El parser de red `scripts/mep/ifc_to_model_mep.py` reconoce los sistemas de
  abastecimiento (`IfcDistributionSystem` PredefinedType **WATERSUPPLY/DOMESTICCOLDWATER/
  POTABLEWATER**) y la **FUENTE = DEPOSITO** (`IfcTank`/`IfcFlowStorageDevice`, reconocido
  por **jerarquia `is_a()`**, no por string exacto) ademas del **grupo de bombeo**
  (`IfcFlowMovingDevice`, ya soportado). Lee la **presion/cota de lamina** de la fuente del
  Pset si esta (`fuentes[*].presion`/`cota_lamina`); si no, la inyecta la demanda (CN-3). El
  parser lee `habitantes_eq` tambien en abastecimiento (consumo EN 805). Las fuentes llevan
  `tipo: "deposito"|"equipo"|"controlador"`. El parser **sigue agnostico al sistema**
  (PCI/REBT/**saneamiento sin regresion**: `test_red_mep.py` TODO OK).
- `scripts/mep/validacion_red.py`: **sin cambios** (ya anclaba la red en `fuentes`; el
  abastecimiento ancla en la fuente, como PCI).
- `scripts/mep/generate_test_ifc_abastecimiento.py` (NUEVO): generador de IFC MEP de
  abastecimiento de prueba (deposito por cota + **anillo/malla** WATERSUPPLY).
- `scripts/mep/test_red_abastecimiento.py` (NUEVO): micro-test IFC-based (deposito como
  fuente, cota de lamina, malla, continuidad CUMPLE).
- El **calculo hidraulico** (solver Darcy-Weisbach de red, copia del de `instalaciones`)
  vive en `obras-lineales`, no aqui (frontera C1). **El nucleo NO se toca** (espejo
  md5-identico). Caso e2e en `obras-lineales` (`caso-LIN-06-abastecimiento`).

## [0.6.0] — 2026-06-22
- **Extension del dominio IFC MEP a SANEAMIENTO (PT 6.2, Ola 6).** El parser de red
  `scripts/mep/ifc_to_model_mep.py` reconoce los sistemas en **lamina libre**
  (`IfcDistributionSystem` PredefinedType **SEWAGE/STORMWATER/DRAINAGE/WASTEWATER**),
  lee las **cotas de solera** (`Pset_Estructurando_Red.CotaSolera` por nudo; pozos
  `IfcDistributionChamberElement`) y mapea el **VERTIDO/outfall** (`IfcFlowTerminal`
  PredefinedType **OUTLET** o por nombre) como **ancla** de la red, emitiendolo en una
  clave **nueva `vertidos[]`** (`tipo:"vertido"`) y marcando su nodo. Los terminales de
  saneamiento llevan `habitantes_eq` (aporte residual, EN 752). El parser **sigue siendo
  agnostico al sistema** (PCI/REBT **sin regresion**: misma salida + la clave aditiva
  `vertidos:[]`). El **calculo hidraulico** (solver de Manning de red) vive en
  `obras-lineales`, no aqui (frontera C1).
- `scripts/mep/validacion_red.py`: la red puede anclarse en **fuentes** (presion) o en
  **vertidos** (saneamiento por gravedad); continuidad/cobertura desde el vertido.
- `scripts/mep/generate_test_ifc_saneamiento.py` (NUEVO): generador de IFC MEP de
  saneamiento de prueba (colectores residuales SEWAGE -> vertido, con cotas de solera).
- Micro-test `scripts/mep/test_red_mep.py` ampliado con 2 casos de saneamiento (ancla en
  el vertido -> CUMPLE; sin fuente ni vertido -> NO CUMPLE). **El nucleo NO se toca**
  (espejo md5-identico). Caso e2e en `obras-lineales` (`caso-LIN-05-saneamiento`).

## [0.5.0] — 2026-06-22
- **Apertura del dominio georreferenciado de OBRA LINEAL (PT 5.1, Ola 5).** Extensión C1 §4bis:
  IFC 4.3 (IFC4X3) `IfcAlignment` + georreferencia, análoga a lo que el PT 4.2 hizo con el dominio
  IFC MEP. Nace `scripts/lineal/` (patrón espejo de `scripts/mep/`), que **reutiliza el núcleo**
  (`ifc_utils`) **sin tocarlo** (espejo md5-idéntico):
  - `ifc_to_model_lineal.py` (NUEVO): parser físico→**modelo neutro lineal**. Lee `IfcAlignment` →
    `IfcAlignmentHorizontal/Vertical/Cant` → `IfcAlignmentSegment.DesignParameters` (segmentos
    LINE/CIRCULARARC/CLOTHOID; CONSTANTGRADIENT/PARABOLICARC; peralte) + georref
    (`IfcMapConversion`/`IfcProjectedCRS`). Reconstruye el perfil por **PK**. Emite `alineacion`
    {planta/alzado/peralte} + `georref` + ganchos `secciones_tipo`/`firme`/`terreno` (None). **No
    calcula trazado** (referenciación lineal 1D, NO grafo de red → no usa `grafo_red`).
  - `generate_test_ifc_lineal.py` (NUEVO): banco IFC4X3 — eje recta→clotoide→curva→clotoide→recta
    (L=400 m) + 2 acuerdos verticales + peralte, georreferenciado (EPSG:25830). Unidad SI explícita.
  - `validacion_alineacion.py` (NUEVO): arnés propio — PK monótono/contiguo, **continuidad+tangencia**
    (integrando cada segmento), continuidad de cotas/pendientes, georref presente, SI; radios/clotoides
    vs 3.1-IC (informativo). `test_lineal.py`: micro-test e2e (positivo + 3 negativos).
  - `export_gis.py` (NUEVO): planta → **GeoJSON** LineString en CRS proyectado (decisión nº3: GeoJSON
    + IFC 4.3 como dos soportes complementarios; puente a hidrología/cuencas de la Ola 6).
- **`ifc-create`/`ifc-validate` ampliadas a Alignment.** `skills/ifc-validate/references/checks-lineal.py`
  (NUEVO): inventario de alineación + georref + continuidad (reutiliza `scripts/lineal`); SKILL.md de
  ambas skills documentan el dominio de obra lineal (entidades, georref, validación). Los validadores
  MEP (`checks-mep.py`) y el parser MEP **no se tocan** (sin regresión).
- **El núcleo NO se toca** (`verificar_espejo_nucleo.py`: ESPEJOS IDÉNTICOS). La lectura de
  georreferencia vive en el parser lineal (se promoverá al núcleo solo si una 2ª disciplina la pide).
  Caso e2e `Casos-de-uso/caso-LIN-01-eje-carretera` (IFC 4.3 → neutro lineal → validación **CUMPLE** →
  GeoJSON). Puertas: **APTO** (`--ref` v0.4.3) y **ESPEJOS IDÉNTICOS**. Reempaquetado acumulativo desde v0.4.3.

## [0.4.3] — 2026-06-22
- **Parser MEP lee `sistema.clase_riesgo` de un Pset del sistema (INC-12, PT 4.6).** `ifc_to_model_mep.py`:
  cuando el `IfcDistributionSystem` lleva `Pset_Estructurando_SistemaPCI.ClaseRiesgo` (o `Pset_Estructurando_Red`),
  el parser emite `sistema.clase_riesgo` (p. ej. OH1); si no, queda `None` y la inyecta el agente (respaldo).
  Así la red de rociadores es **reproducible sin inyección manual** (el dato del IFC prevalece, como con
  caudal/presión de terminal). `generate_test_ifc_rociadores.py` escribe ese Pset (ClaseRiesgo=OH1) en la red
  de prueba. **Sin regresión**: BIE (PCI-01) y ELECTRICAL (REBT) dan `clase_riesgo=None` → comportamiento
  idéntico; rociadores (PCI-02) reproduce req 58,9 / margen 241,1 kPa sin inyección. **El núcleo NO se toca**;
  `instalaciones` NO se toca (el dispatcher ya enrutaba por `clase_riesgo`). Reempaquetado acumulativo desde v0.4.2.

## [0.4.2] — 2026-06-22
- **Validador MEP sistema-aware (PT 4.5, Ola 4).** `skills/ifc-validate/references/checks-mep.py`:
  el Pset de segmento requerido depende ahora del **tipo de sistema** (cierra el TODO heredado
  "o Duct/Cable segun sistema"): `ELECTRICAL/POWER/LIGHTING -> Pset_CableSegmentTypeCommon`,
  `AIRCONDITIONING/VENTILATION/... -> Pset_DuctSegmentTypeCommon`, resto (PCI/fontaneria) ->
  `Pset_PipeSegmentTypeCommon`. Sin esto, una red ELECTRICAL (conductores con
  `Pset_CableSegmentTypeCommon`) daba NO APTO por exigir Pset de tuberia. **El parser
  (`ifc_to_model_mep.py`) NO se toca** (decision PT 4.5). Sin regresion en PCI. Casos e2e:
  `caso-REBT-01-vivienda` y `caso-REBT-02-terciario` (APTO).

## [0.4.1] — 2026-06-22
- **WRITE-BACK de Psets de resultado de red (PT 4.4, Ola 4).** Cierra el ciclo
  **IFC → cálculo → IFC** dando a la disciplina la **mecánica** de escritura IFC (la
  semántica —qué escribir— la fija `instalaciones`; frontera C1 §5, opción (a) del PT 4.4).
  - `skills/ifc-create/references/escribir_psets_resultado.py` (NUEVO): escritor **genérico**
    y agnóstico de disciplina/esquema. Lee un mapping JSON `{elementos: {Name|GlobalId:
    {Pset: {prop: val}}}}` y vuelca los Psets de resultado al IFC con `ifcopenshell.api`
    (localiza por Name y, si no, por GlobalId). CLI: `entrada.ifc mapping.json salida.ifc`.
  - `skills/ifc-validate/references/checks-mep.py`: **reconoce** `Pset_Estructurando_ResultadoRed`
    (informativo) para confirmar el write-back; el resto de la validación de red intacto.
  - `scripts/mep/generate_test_ifc_rociadores.py` (NUEVO): banco de pruebas — red **mallada**
    de rociadores (escalera de 3 lazos + 6 rociadores `ROC-n`, `FIREPROTECTION`) para ejercitar
    el solver de mallas de `instalaciones`.
  - **Núcleo espejado intacto** (`scripts/nucleo/` byte a byte con el canónico del motor); MEP
    estructural (parser/validación PT 4.2) sin cambios. Reempaquetado acumulativo desde v0.4.0.

## [0.4.0] — 2026-06-22
- **DOMINIO IFC MEP (PT 4.2, Ola 4 — hueco H2 de la verificación de la Ola 1).** Abre la
  E/S IFC del dominio de instalaciones (redes de distribución) y emite el **modelo neutro
  de red**, reutilizando el **núcleo transversal** (`ifc_utils` + `grafo_red`, PT 4.1)
  **sin tocarlo**. **No** implementa el solver de red (Darcy/Manning, eléctrico, térmico):
  eso nace después con la disciplina `instalaciones`.
  - `scripts/mep/ifc_to_model_mep.py` (NUEVO): parser físico→neutro de red.
    `IfcDistributionSystem` (PredefinedType) + `IfcFlowSegment/Fitting/Terminal/Controller/
    MovingDevice` + `IfcDistributionPort`/`IfcRelConnectsPorts` (respaldo geométrico) →
    `{unidades SI, sistema, nodos, tramos, terminales, fuentes}`. Reutiliza
    `ifc_utils.psets`/`length_scale`/`pset_value` y `grafo_red.construir_grafo`. Modelo
    **hermano** del estructural (claves nuevas, sin redefinir las existentes). Gancho **H3**:
    clave `demanda` prevista por terminal/sistema, **no** calculada.
  - `scripts/mep/generate_test_ifc_mep.py` (NUEVO): banco de pruebas — red PCI
    (`FIREPROTECTION`) fuente → 4 tramos → 3 BIE, con puertos y `IfcRelConnectsPorts`.
  - `scripts/mep/validacion_red.py` (NUEVO): arnés de validación de red — continuidad
    (conexo desde fuente), terminales conectados, sin componentes huérfanas
    (`grafo_red.filtrar_componentes_desconectadas`, `es_ancla`=fuente), unidades SI.
  - `scripts/mep/test_red_mep.py` (NUEVO): micro-test autocontenido (unión por puertos,
    troceo T/X, validación de red); exit ≠ 0 si falla. `scripts/mep/README.md` documenta la API.
  - `scripts/nucleo/` (NUEVO, **espejo** del canónico de `motor-calculo-estructural`):
    `ifc_utils.py` + `grafo_red.py` + micro-test (verbatim). Avance de la **decisión nº4**
    (promover el núcleo a módulo compartido); el canónico sigue en el motor.
  - **Skills ampliadas a MEP:** `ifc-create/SKILL.md` (entidades MEP + plantilla de red),
    `ifc-validate/SKILL.md` + `references/checks-mep.py` (NUEVO: inventario, Psets `Pset_*`,
    puertos y **continuidad de red** vía el parser+validación).
  - **Verificación:** micro-test OK; caso e2e `Casos-de-uso/caso-MEP-01-red-pci` (5 nodos /
    4 tramos / 3 BIE / 1 fuente, cobertura 100 %) → **CUMPLE**. `ast.parse` de los 11 `.py`
    (0 errores). Reempaquetado **acumulativo** desde v0.3.0.

## [0.3.0] — (baseline previo)
- Gestión de información BIM (ISO 19650 / OpenBIM): `bep-eir`, `loin-matrix`, `cde-audit`,
  `bsdd-clasificacion`, y E/S IFC del **dominio estructural** (`ifc-create`, `ifc-validate`)
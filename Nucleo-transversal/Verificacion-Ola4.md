# Verificación de cierre de la Ola 4 (PT 4.6)

**Auditoría del motor de red del ecosistema y de sus dos verticales —PCI (BIE + rociadores) y
eléctricas (REBT)— · 22/06/2026.** Análogo al PT 1.6 sobre la Ola 1: comprueba que la cadena
**IFC → modelo neutro → demanda → solver → verificación → write-back → validación** es coherente,
**sin regresiones**, con los contratos **C1 + CN-1/CN-2/CN-3** respetados, las **puertas de calidad en verde** y
el **núcleo espejado idéntico**, y deja preparado el hueco del **tercer vertical (clima/RITE)** y de
la **Ola 5**. No es desarrollo nuevo: no se construye ningún vertical. Todo resultado es de
**predimensionado/asistencia y debe ser revisado y firmado por técnico competente** (Ingeniero de
Caminos); NDP marcados `[confirmar AN]`.

> **Veredicto global: Ola 4 CERRABLE ✅ en lo verificado (núcleo de red + PCI + REBT), sin
> reempaquetar.** Los contratos C1 + CN-1/CN-2/CN-3 son coherentes con la implementación multi-vertical; el modelo
> neutro de red es **realmente agnóstico al sistema** (PCI hidráulico y REBT eléctrico lo consumen
> igual); la regresión de **micro-tests (3/3) y de los 5 casos e2e** confirma **PCI sin regresión tras
> las adiciones de REBT** y **REBT CUMPLE/APTO**; las **puertas** dan **APTO** y **ESPEJOS IDÉNTICOS**
> en los tres plugins; el núcleo es **md5-idéntico** en los tres; y **no hay defecto de empaquetado**
> (0 truncados, 0 artefactos, sin divergencia workspace↔`.plugin`). La auditoría abre **una incidencia
> menor de reproducibilidad** (INC-12: la red de rociadores PCI-02 necesitaba la inyección de
> `clase_riesgo`, un dato de proyecto del agente, que el `run_all` por sí solo no realizaba) — **ya
> RESUELTA en este mismo hilo** (`iso19650-openbim` **v0.4.3**: el parser lee `clase_riesgo` de un Pset del
> sistema; PCI-02 reproduce sin inyección; puertas APTO + ESPEJOS IDÉNTICOS; ver §6/§9) — y **registra una
> aproximación documentada** (feeder mono+tri = trifásico equilibrado, REBT, INC-13, ya `[confirmar AN]`).
> Ninguna cambia un veredicto. Único reempaquetado: **iso19650-openbim v0.4.3** (refinamiento del parser por
> INC-12; núcleo intacto, `instalaciones` y el motor sin tocar).

---

## 1. Tabla contrato por contrato (coherencia C1 + CN-1/CN-2/CN-3 multi-vertical)

| Contrato | Veredicto | Evidencia |
|---|---|---|
| **C1 — IFC / modelo neutro de red (agnóstico al sistema)** | ✅ Coherente | El parser `iso19650-openbim:scripts/mep/ifc_to_model_mep.py` emite el **mismo esquema de modelo neutro** para los dos verticales: top-keys `{unidades, sistema, nodos, tramos, terminales, fuentes, metricas}` **idénticas** en PCI-01 (`sistema.tipo=FIREPROTECTION`) y en REBT-01/02 (`sistema.tipo=ELECTRICAL`); mismo bloque `unidades` SI (`longitud m, caudal l/s, presion kPa, potencia W`); mismas claves de tramo `{ni,nj,dn,material,rugosidad,longitud,clase,elemento}`. **Lo único que cambia es `sistema.tipo`.** La **sección del conductor** (REBT) **no nace en el parser** sino en la capa de demanda de `instalaciones` (decisión PT 4.5) → el parser quedó **intacto** entre v0.4.0 y v0.4.2 (la puerta confirma 0 encogidos / 0 nuevos en el contraste v0.4.2↔v0.4.1). **Frontera C1↔CN-3↔cálculo respetada.** |
| **C1 §5bis — Write-back de Psets de resultado** | ✅ Coherente | La **mecánica** vive en `iso19650-openbim` (`ifc-create:escribir_psets_resultado.py`, escritor genérico por mapping `Name/GlobalId`); la **semántica** en `instalaciones`, con el **mismo `Pset_Estructurando_ResultadoRed`** en los dos verticales: `red/resultado_ifc.py` (hidráulico: `DN_dimensionado_mm`, `Caudal_l_s`, `Velocidad_m_s`, `Perdida_carga_kPa`, `Margen_kPa`, `Cumple`) y `electrico/resultado_ifc_electrico.py` (eléctrico: `Seccion_mm2`, `Intensidad_A`, `I_admisible_A`, `Caida_tension_pct`, `Potencia_W`, `Fases`, `Material_conductor`). Mismo Pset, propiedades por disciplina. |
| **C1 §5/§5bis — Validación sistema-aware (Pipe/Cable/Duct)** | ✅ Coherente | `ifc-validate:checks-mep.py` (v0.4.2) exige el Pset de segmento **según `sistema.tipo`**: `ELECTRICAL/POWER/LIGHTING → Pset_CableSegmentTypeCommon`, `AIRCONDITIONING/VENTILATION/AIRHANDLING/EXHAUST → Pset_DuctSegmentTypeCommon`, resto (PCI/fontanería) → `Pset_PipeSegmentTypeCommon` (def.). Verificado en PCI (exige Pipe, sin regresión) y REBT (exige Cable). **`AIRCONDITIONING→Duct` ya está cableado** (hueco RITE pre-aprovisionado). |
| **C2 — Memoria del despacho** | ✅ Coherente | `criterios-instalaciones.md` (raíz) tiene las 5 secciones (Normativa, Materiales/componentes, Coeficientes y criterios, Lecciones aprendidas, Formato de memoria), con normativa **PCI** (RIPCI/UNE-EN 671/UNE 23500/DB-SI; rociadores UNE-EN 12845) y **REBT** (ITC-BT-10/19/25/44/47) y 10 lecciones fechadas (PCI-01…REBT-02). La skill `instalaciones:criterios-memoria` lee/mantiene este archivo + la memoria por obra. Enchufa sin tocar el núcleo. |
| **C3 — Entregables / memoria** | ✅ Coherente | Cada caso e2e entrega `memoria-instalaciones.md` (+ `.docx`) con el esqueleto homogéneo (datos, normativa citada, demanda/bases, comprobaciones por elemento, registro fechado, conclusiones), unidades SI (l/s, kPa, mm, A, %) y NDP `[confirmar AN]`. Reutiliza el motor de documentos común. |
| **CN-3 — Bases de demanda (slot no estructural)** | ✅ Coherente | El "slot CN-3" se cubre con **bases de demanda propias** por vertical: PCI `pci/bases_demanda.py` (BIE por simultaneidad RIPCI/UNE; rociadores por densidad×área UNE-EN 12845, dispatcher `aplicar_demanda`) y REBT `electrico/bases_demanda_electrica.py` (vivienda ITC-BT-25 C1–C12; receptores ITC-BT-44/47; previsión ITC-BT-10). El **dato del IFC prevalece** sobre el valor por defecto. Frontera C1(lectura iso19650) ↔ CN-3(demanda) ↔ cálculo(instalaciones) mantenida en ambos verticales. |

Leyenda: ✅ coherente · ⚠️ desajuste menor / a precisar · ❌ falta.

**Conclusión C1 + CN-1/CN-2/CN-3.** El núcleo de red es agnóstico al sistema demostrablemente (el mismo parser y el
mismo grafo alimentan un solver hidráulico y uno eléctrico), y la frontera transversal↔disciplina se
respeta en los dos verticales. No se detecta ninguna divergencia de contrato.

---

## 2. Regresión integral (sin tocar código)

Banco de pruebas reconstruido en un `/tmp` **nuevo**: los tres `.plugin` extraídos íntegros con `unzip`
(fuente íntegra), los 5 casos copiados con sus IFC y JSON de referencia, toolchain en `/tmp/pylibs`
(ifcopenshell 0.8.5). El solver y la demanda de `instalaciones` son **stdlib pura**; solo el
parser/validador de `iso19650-openbim` usan ifcopenshell.

### 2.1 Micro-test (stdlib)

| Micro-test | Resultado |
|---|---|
| `instalaciones/scripts/nucleo/test_grafo_red.py` | **TODO OK** (registro de nodos por tolerancia, troceo T/X, no-regresión a tol trivial, union-find genérico, álgebra 4×4, bbox) |
| `instalaciones/scripts/red/test_solver_red.py` | **0 fallos** (fricción laminar/Swamee-Jain, tramo recto vs analítico, balance en la te, **árbol 0 lazos**, **malla 1 lazo 50/50**, **malla 2 lazos cierre ≈0**, balance nodal con signo) |
| `instalaciones/scripts/electrico/test_solver_electrico.py` | **0 fallos** (I mono/tri, ΔU por tramo vs analítico, intensidad admisible, balance de potencias, radial 0 lazos, **redimensionado** automático) |

### 2.2 Casos e2e (re-ejecutados desde `/tmp`, contrastados contra el JSON de referencia almacenado)

| Caso | Sistema | Pipeline re-ejecutado | Veredicto | Cifra clave | Contraste vs referencia |
|---|---|---|---|---|---|
| **MEP-01** | FIREPROTECTION (topología) | parser → `validacion_red` | **CUMPLE** | cobertura 100 %, 0 huérfanas (5 nodos/4 tramos/3 term.) | **IDÉNTICO** (0 mismatches) |
| **PCI-01** | PCI · BIE | parser → `run_all_pci` | **CUMPLE** | fuente disp 600 / **req 352,9 kPa** (margen 247,1); balance **0,0000 %**; v_pico 0,994 m/s | Numérico **idéntico** (info[] reformulado; el JSON almacenado es de v0.1.0, anterior al esquema de caudal con signo) |
| **PCI-02** | PCI · rociadores OH1 (malla 3 lazos) | parser → *inyección `clase_riesgo=OH1`* → `run_all_pci` | **CUMPLE** | fuente disp 300 / **req 58,9 kPa** (margen 241,1); v_pico 1,243 m/s; balance **0,0000 %**; **cierre lazo 3·10⁻⁶ kPa** | **IDÉNTICO con la orquestación completa** (resultado: 0/282 claves; verif: 0 numéricas, 1 info[] reformulada). Ver §6 (INC-12) |
| **REBT-01** | ELECTRICAL · vivienda (8 circuitos) | parser → `run_all_electrico` | **CUMPLE** | P cabecera 18 705,8 W; **ΔU máx 1,098 %** (C8-Calefacción); balance potencias **0,0000 %** | **IDÉNTICO** (0 mismatches resultado y verif.) |
| **REBT-02** | ELECTRICAL · terciario (mono+tri) | parser → `run_all_electrico` | **CUMPLE** | P cabecera 11 296,0 W; **ΔU máx 3,318 %** (TOMA-1); balance potencias **0,0000 %** | **IDÉNTICO** (0 mismatches resultado y verif.) |

**PCI sin regresión tras REBT (lo crítico de la Ola 4).** Las cifras de PCI-01 y PCI-02 coinciden con
sus referencias previas (PT 4.3/4.4) **byte a cifra**; la incorporación del vertical eléctrico (PT 4.5)
**no alteró** el solver hidráulico ni la demanda PCI. El residuo de convergencia de Hardy-Cross en
PCI-02 difiere de forma negligible (3·10⁻⁶ vs 5·10⁻⁶ kPa, ruido de iteración, ≪ tolerancia).

> **Matiz de método (no regresión).** En PCI-01 y PCI-02 los `*.json` almacenados en la carpeta del
> caso son de PT 4.3/4.4 y tienen un esquema ligeramente anterior (PCI-01 carece de las claves de
> *caudal con signo* añadidas en PT 4.4; algunos textos `info[]` del arnés se reformularon). **Todos los
> valores numéricos coinciden**; las diferencias son de **esquema/redacción**, no de cálculo. Conviene
> regenerar esos JSON de referencia para evitar falsos positivos futuros (mejora menor, no defecto).

---

## 3. Puertas de calidad sobre los 3 plugins (salida pegada)

### 3.1 `verificar_empaquetado.py` (con `--ref` a la versión previa íntegra)

> Nota de método: la puerta `verificar_empaquetado.py` del workspace llegó **mount-corrupta** por el
> shell (9201 B pero 200 líneas y `SyntaxError` en la 201). Se **reconstruyó desde la fuente íntegra**
> (herramienta `Read`, 251 líneas, `ast.parse` OK) y se ejecutó desde `/tmp`. `verificar_espejo_nucleo.py`
> se sirvió íntegra (4661 B/126 ln, parsea).

```
VERIFICACION DE EMPAQUETADO -- iso19650-openbim-v0.4.2.plugin   (--ref v0.4.1)
  plugin.json OK -- name=iso19650-openbim version=0.4.2
  description: 434/500 caracteres -- OK
  Sin artefactos (__pycache__/node_modules/*.pyc) -- OK
  Modulos .py: 13  |  errores de sintaxis: 0  |  sin salto de linea final: 0
  Contraste vs ref: 0 encogidos, 0 ausentes, 0 nuevos
VEREDICTO: APTO para distribuir

VERIFICACION DE EMPAQUETADO -- instalaciones-v0.3.0.plugin      (--ref v0.2.0)
  plugin.json OK -- name=instalaciones version=0.3.0
  description: 481/500 caracteres -- OK
  Sin artefactos (__pycache__/node_modules/*.pyc) -- OK
  Modulos .py: 15  |  errores de sintaxis: 0  |  sin salto de linea final: 0
  Contraste vs ref: 0 encogidos, 0 ausentes, 6 nuevos
    nuevos: scripts/electrico/{bases_demanda_electrica,resultado_ifc_electrico,
            run_all_electrico,solver_electrico,test_solver_electrico,verificacion_electrico}.py
VEREDICTO: APTO para distribuir
```

> El parser MEP (`ifc_to_model_mep.py`) **no se tocó** al pasar a v0.4.2 (0 encogidos / 0 nuevos): el
> único cambio fue hacer `checks-mep.py` **sistema-aware** (INC-11). Los 6 nuevos de `instalaciones` son
> el vertical eléctrico íntegro. `description` ≤ 500 en los dos (434, 481).

**Tercer plugin (canónico del núcleo), informativo —no se re-entrega en PT 4.6:**

```
VERIFICACION DE EMPAQUETADO -- motor-calculo-estructural-v0.23.0.plugin   (--ref v0.22.1)
  plugin.json OK -- name=motor-calculo-estructural version=0.23.0
  description: 460/500 caracteres -- OK
  Sin artefactos -- OK | Modulos .py: 129 | sintaxis: 0 | sin salto de linea final: 0
  Contraste vs ref: 3 encogidos, 0 ausentes, 3 nuevos (scripts/nucleo/{grafo_red,ifc_utils,test_grafo_red}.py)
  -> con --allow-shrink de los 3 ficheros del refactor H1:  VEREDICTO: APTO para distribuir
```

> Los 3 "encogidos" (`puente_analitico/puente.py` −3411 B, `barras/ifc_to_model.py` −299 B,
> `laminas/ifc_to_model_3d.py` −295 B) son el **refactor H1 auditado en PT 4.1** (código extraído a
> `scripts/nucleo/`): NO es truncado (parsean; la puerta confirma 0 errores de sintaxis sobre los 129
> módulos). Con `--allow-shrink` de esos tres ficheros → **APTO**. `description` 460/500.

### 3.2 `verificar_espejo_nucleo.py` (canónico = motor v0.23.0)

```
VERIFICACION DE IDENTIDAD DEL NUCLEO ESPEJADO
  canonico (motor-calculo-estructural-v0.23.0.plugin): 4 ficheros
     966a7588e3228928e5b7164e6de6a553  README.md
     fe5dfebb4c5adb73f90718d57978e8a4  grafo_red.py
     ad06f87d648fc0388b35d10deeb290b7  ifc_utils.py
     29dedbb4d266ab4e805a913478eeb66d  test_grafo_red.py
  espejo iso19650-openbim-v0.4.2.plugin  -> IDENTICO
  espejo instalaciones-v0.3.0.plugin     -> IDENTICO
VEREDICTO: ESPEJOS IDENTICOS
```

`description` ≤ 500 en los tres plugins: **motor 460 · iso19650 434 · instalaciones 481**.

---

## 4. Auditoría del núcleo espejado (identidad md5 en los tres plugins)

`scripts/nucleo/` (`ifc_utils.py`, `grafo_red.py`, `test_grafo_red.py`, `README.md`) es **canónico en el
motor** y se espeja byte a byte. md5 directo extraído de cada `.plugin`:

| Fichero del núcleo | md5 (idéntico en los 3) |
|---|---|
| `ifc_utils.py` | `ad06f87d648fc0388b35d10deeb290b7` |
| `grafo_red.py` | `fe5dfebb4c5adb73f90718d57978e8a4` |
| `test_grafo_red.py` | `29dedbb4d266ab4e805a913478eeb66d` |
| `README.md` | `966a7588e3228928e5b7164e6de6a553` |

**Identidad confirmada** en `motor-calculo-estructural-v0.23.0`, `iso19650-openbim-v0.4.2` e
`instalaciones-v0.3.0`. (El `__pycache__/*.pyc` que aparece al ejecutar los micro-test en el árbol de
trabajo **no está en el ZIP** —la puerta confirma "sin artefactos"— y la puerta de espejo lo ignora.)

---

## 5. Auditoría de defectos de empaquetado y workspace↔`.plugin`

- **Truncado:** `ast.parse` + salto de línea final sobre **todos** los `.py` de los tres ZIP → **0
  errores de sintaxis, 0 sin salto de línea final** (13 + 15 + 129 módulos).
- **Artefactos:** recuento directo en los tres ZIP → **0** `__pycache__`/`node_modules`/`*.pyc`.
- **`description` ≤ 500:** los tres cumplen (460/434/481).
- **workspace ↔ `.plugin`:** se contrastaron por md5 los `.py` y `CHANGELOG.md` del workspace contra el
  `.plugin`. Los aparentes diff de `.py` (`solver_red.py`, `bases_demanda.py`, `verificacion_red.py`,
  `test_solver_red.py`, `checks-mep.py`) son el **hazard de mount**: el shell sirve copias **truncadas**
  del workspace (p. ej. `solver_red.py` 15 209 B con `SyntaxError` vs 22 810 B en el `.plugin`); 4 de 5
  **fallan `ast.parse`** —firma de corrupción de lectura, no de un workspace stale (un stale válido
  parsearía)—. Contrastado con la herramienta `Read` (fuente de verdad): el `solver_red.py` del workspace
  tiene **522 líneas y termina exactamente igual** que el del `.plugin` (`sys.exit(main(...))`). **No hay
  divergencia real.**
- **Lección PT 4.5 (`.md` no sincronizado) — NO recurre:** los `CHANGELOG.md` del workspace están **al
  día** (`instalaciones` encabeza `v0.3.0`; `iso19650-openbim` encabeza `[0.4.2]`) y el `checks-mep.py`
  del workspace tiene las **mismas 8 referencias** `Cable/Duct` que el `.plugin` (la lógica sistema-aware
  sí está en el workspace).

**Conclusión:** no se destapa ningún defecto de empaquetado. El único reempaquetado del hilo es
**iso19650-openbim v0.4.3** (refinamiento del parser por INC-12, §6), no por un defecto de empaquetado.

---

## 6. Hallazgo de la auditoría: reproducibilidad de la red de rociadores (INC-12, P3 — RESUELTO en este hilo)

Al re-ejecutar **PCI-02** con las dos llamadas CLI documentadas (`ifc_to_model_mep.py` →
`run_all_pci.py`), el resultado **divergía** de la referencia (req 205,7 vs 58,9 kPa; cabecera 3,2 vs
6,0 l/s). **Causa raíz:** PCI-02 es una red de **rociadores OH1**; el dispatcher `aplicar_demanda` enruta
a `aplicar_rociadores` **solo si `sistema.clase_riesgo` está presente**, y en caso contrario **cae a la
lógica de BIE** (1,6 l/s, 2 simultáneas). El IFC de prueba **no lleva** la clase de riesgo (grep `OH1`
sobre `rociadores-malla.ifc` → 0), y el README del caso lo dice explícitamente: *"Se inyecta
`sistema.clase_riesgo = "OH1"`"*. Es decir, **la clase de riesgo es un dato de proyecto que aporta el
agente** entre el parser y la demanda; `run_all_pci.py` por sí solo no la inyecta.

**Comprobado:** inyectando `clase_riesgo=OH1` (el paso de orquestación documentado), PCI-02 reproduce la
referencia **exacto** (req 58,913 / margen 241,087 / v_pico 1,243; resultado 0 mismatches sobre 282
claves). **Por tanto no es una regresión de código**, sino una **dependencia de orquestación** no
reproducible con las dos llamadas CLI aisladas.

**Acción propuesta (no bloqueante):** una de — (a) que el parser lea `clase_riesgo` de un Pset del
`IfcDistributionSystem` (`Pset_Estructurando_SistemaPCI.ClaseRiesgo`) cuando exista, manteniendo la
inyección del agente como respaldo; (b) un flag `--clase-riesgo OH1` en `run_all_pci.py`; o (c)
documentarlo como paso de orquestación fijo del agente (es lo coherente con el patrón "el agente
clasifica/orquesta"). Recomendado **(a)+(c)**: el dato lo manda el agente, pero si el modelador lo dejó
en el IFC, que el parser lo respete (como ya hace con caudal/presión de terminal).

> **✅ RESUELTO en este mismo hilo (`iso19650-openbim` v0.4.3, opción a+c).** El parser
> `ifc_to_model_mep.py` lee `sistema.clase_riesgo` de `Pset_Estructurando_SistemaPCI.ClaseRiesgo` (o
> `Pset_Estructurando_Red`) cuando existe; si no, queda `None` y la inyecta el agente (respaldo). El generador
> `generate_test_ifc_rociadores.py` escribe ese Pset (`ClaseRiesgo=OH1`). Verificado: el IFC se autodescribe,
> el parser emite `clase_riesgo=OH1` y **PCI-02 reproduce la referencia SIN inyección manual** con
> `run_all_pci.py` directo (req 58,913 / margen 241,087; resultado 0 mismatches/282 claves); el write-back IFC
> re-parseado valida **CUMPLE** (continuidad 100 %, `clase_riesgo` round-trip OH1). **Sin regresión**: BIE
> (PCI-01) y ELECTRICAL (REBT) dan `clase_riesgo=None` → idéntico. **Núcleo e `instalaciones` intactos**.
> Puertas: empaquetado v0.4.3 vs v0.4.2 **APTO** (13 .py, 0 truncados, desc 434/500) y **ESPEJOS IDÉNTICOS**.
> Caso PCI-02 regenerado coherente (IFC con Pset + neutro + demanda + resultado + verif + mapping + write-back).

---

## 7. Checklist consolidado "listo para el tercer vertical (clima / RITE)"

Igual que el PT 1.6 dejó el checklist "listo para nueva disciplina", se evalúa qué **reutiliza** RITE del
núcleo ya verificado y qué es **realmente nuevo**.

**Lo que RITE reutiliza del núcleo (ya verificado, sin tocar) — [x]**

- [x] **Grafo de red** (`grafo_red.construir_grafo`, nodos+tramos por puertos/intersección): los
  conductos de aire son una red de distribución más (md5 idéntico en los 3 plugins).
- [x] **Lectura IFC MEP** (`ifc_to_model_mep.py`): el parser es **agnóstico al sistema** y ya emite
  `sistema.tipo` tal cual; un `IfcDistributionSystem` `AIRCONDITIONING/VENTILATION` produce el mismo
  modelo neutro de red.
- [x] **Write-back** (`Pset_Estructurando_ResultadoRed`, escritor genérico): reutilizable con
  propiedades de aire (caudal m³/h, pérdida Pa, sección/diámetro de conducto).
- [x] **Validación sistema-aware**: `AIRCONDITIONING/VENTILATION/AIRHANDLING/EXHAUST → Pset_DuctSegmentTypeCommon`
  **ya está cableado** en `checks-mep.py` (no hay que tocar el validador para el caso base de clima).
- [x] **Patrón demanda = slot CN-3** (dispatcher tipo `aplicar_demanda`), **memoria/criterios** (CN-1/CN-2) y
  **patrón de subagente** (`proyectista-*`) replicables.
- [x] **Propagación por árbol** del solver (`red/solver_red._arbol_desde_fuente`) reutilizable para
  conductos en árbol; **Hardy-Cross** disponible si la red de retorno/anillo es mallada.

**Lo realmente nuevo de RITE (a construir en el vertical) — [ ]**

- [ ] **Solver de conductos de aire**: pérdida de carga en conducto (rozamiento + singulares), equilibrado
  de caudales de impulsión/retorno, posible cálculo por el método de **pérdida de carga constante** o
  **recuperación estática**; unidades de aire (m³/h, Pa).
- [ ] **Cargas térmicas / demanda RITE**: cargas de calefacción/refrigeración, caudales de ventilación
  por ocupación (RITE IT 1.1.4.2, IDA/ODA), renovaciones — el "slot CN-3" del clima (DB-HE / RITE).
- [ ] **Tipos de terminal de aire** (difusor, rejilla, UTA) y la extensión de `unidades` (caudal de aire,
  presión Pa, potencia térmica kW) en el modelo neutro.
- [ ] **Subagente `proyectista-climatizacion`** + enrutado `AIRCONDITIONING → RITE` en el agente
  `ingeniero-de-instalaciones` (el agente ya enruta FIREPROTECTION→PCI y ELECTRICAL→REBT).

**Definición de "hecho" de la Ola 4 (verificada):** (a) el modelo neutro de red es agnóstico al sistema
✅; (b) dos verticales (PCI, REBT) cierran de extremo a extremo IFC→…→IFC ✅; (c) núcleo espejado idéntico
✅; (d) puertas en verde ✅; (e) el hueco de clima está **pre-aprovisionado** (parser agnóstico + validador
`AIRCONDITIONING→Duct` + patrón de demanda/subagente) ✅.

**Listo para la Ola 5 (obras lineales I):** independiente de la Ola 4; estrena **IFC 4.3 Alignment + GIS**
(decisión abierta nº3 sobre formato GIS pendiente). El **motor hidráulico de red** queda disponible para
la Ola 6 (drenaje/obras hidráulicas, Manning).

---

## 8. Decisiones a resolver y documentar

### 8.1 ¿Se cierra la Ola 4 con RITE antes de la Ola 5, o RITE pasa a un PT posterior?

**Propuesta: cerrar la Ola 4 "en lo verificado" (núcleo de red + PCI + REBT) AHORA, y llevar RITE a una
sub-ola 4.x (PT 4.7), antes o en paralelo a la Ola 5.** Justificación:

- Los **dos verticales construidos están completos y verificados** de extremo a extremo; el estado
  alcanzado es un hito sólido que conviene **bancar** (cerrar) sin esperar a clima.
- **RITE no es una tarea de verificación sino un vertical nuevo** con física genuinamente nueva (solver de
  conductos, cargas térmicas, demanda RITE/DB-HE). Mantenerlo dentro de "Ola 4 abierta" mezcla
  *consolidación* con *desarrollo*.
- El **riesgo de incorporar RITE más tarde es bajo**: el hueco está pre-aprovisionado (parser agnóstico,
  validador `AIRCONDITIONING→Duct`, patrón demanda/subagente), así que entra como **sub-ola 4.x** sin
  bloquear la Ola 5 (que es independiente: Alignment/GIS).
- Operativamente: marcar **Ola 4 ✅ cerrada (PCI + REBT)** y crear **PT 4.7 "clima/RITE" (sub-ola 4.x)** en
  el backlog, ejecutable cuando convenga sin frenar el arranque de obras lineales.

### 8.2 Estado de las capacidades transversales: "dos solvers sobre el mismo grafo"

**Confirmado.** `red/solver_red.py` (Darcy-Weisbach; árbol + Hardy-Cross en malla) y
`electrico/solver_electrico.py` (propagación por árbol, **importando** `red/solver_red._arbol_desde_fuente`;
sin Hardy-Cross porque la BT de interior es radial) operan **sobre el mismo `grafo_red`** del núcleo. La
abstracción a **anunciar al núcleo** es: **"grafo de red (topología) + N solvers (física por disciplina)"**.
La Ola 6 (obras hidráulicas) añadirá el **tercer solver** —Manning, lámina libre— sobre el mismo grafo, y
el clima (4.x) el de conductos de aire. El núcleo da topología y E/S; **no calcula**.

---

## 9. Backlog / incidencias actualizado

| ID | Prioridad | Estado | Resumen | Resuelta/Detectada en |
|---|---|---|---|---|
| **INC-10** | P2 | ✅ | Espejo del núcleo + puerta de integridad (md5). **Re-confirmado**: ESPEJOS IDÉNTICOS en los 3 plugins. | PT 4.2 → resuelto PT 4.3; re-verificado **PT 4.6** |
| **INC-11** | P2 | ✅ | Validador MEP sistema-aware (Pipe/Cable/Duct). **Re-confirmado**: PCI exige Pipe (sin regresión), REBT exige Cable, `AIRCONDITIONING→Duct` cableado. | PT 4.5 → re-verificado **PT 4.6** |
| **INC-12** | P3 | ✅ (resuelto en este hilo) | **Reproducibilidad de la red de rociadores PCI.** `run_all_pci.py` por sí solo caía a demanda BIE si faltaba `sistema.clase_riesgo` (dato de proyecto que inyectaba el agente). **RESUELTO (iso19650-openbim v0.4.3, opción a+c):** el parser lee `clase_riesgo` de `Pset_Estructurando_SistemaPCI` del sistema (respaldo = inyección del agente); el generador lo escribe. PCI-02 reproduce **sin inyección** (req 58,9/margen 241,1; 0 mismatches/282 claves; write-back round-trip OH1). Sin regresión (BIE/REBT → None); núcleo e `instalaciones` intactos; puertas APTO + ESPEJOS IDÉNTICOS. | **PT 4.6** |
| **INC-13** | P3 | 🟡 (registrada) | **Aproximación "feeder mono+tri = trifásico equilibrado"** (REBT): un feeder que alimenta cargas mono y tri se resuelve como trifásico (U=400) y la ΔU acumulada mezcla 400/230 V, expresada en % sobre la tensión del terminal. Ya marcada `[confirmar AN]`; mantener como aproximación de predimensionado a revisar por técnico. | PT 4.5 → registrada **PT 4.6** |
| **INC-09** | P1 | ✅ | Puerta de empaquetado. **Re-confirmada operativa** (cazó la corrupción de mount de su propia copia del workspace; reconstruida desde fuente y ejecutada). | PT 1.6 |
| **INC-04 / mount** | P3 | 🟡 | **Hazard de mount confirmado de nuevo**: el shell sirvió truncadas las puertas y varios `.py` del workspace (no los `.plugin`, que extraen íntegros). Patrón aplicado: `.plugin` por `unzip` + ficheros sueltos por `Read`→reconstrucción en `/tmp`. | recurrente |

**Mejora menor (no INC):** el caso **PCI-02 ya se regeneró** al esquema actual con la cadena v0.4.3 (IFC con
Pset + neutro + demanda + resultado + verif + mapping + write-back IFC). Queda **PCI-01** por regenerar
(caudal con signo / textos del arnés) para que el contraste futuro sea estrictamente byte a byte.

---

## 10. Conclusión

La **Ola 4 puede cerrarse en lo verificado (✅): núcleo de red + PCI (BIE + rociadores) + REBT.** El modelo
neutro de red es **agnóstico al sistema** (mismo esquema y unidades para PCI hidráulico y REBT eléctrico,
solo cambia `sistema.tipo`); la cadena **IFC→neutro→demanda→solver→verificación→write-back→validación** es
coherente con los contratos C1 + CN-1/CN-2/CN-3 en los dos verticales; la **regresión** (micro-tests 3/3 y 5 casos e2e)
confirma **PCI sin regresión tras REBT** y **REBT CUMPLE/APTO**; las **puertas** dan **APTO** (iso19650
v0.4.2 vs v0.4.1; instalaciones v0.3.0 vs v0.2.0) y **ESPEJOS IDÉNTICOS** (núcleo md5-idéntico en los tres
plugins); y **no hay defecto de empaquetado** (0 truncados, 0 artefactos, sin divergencia real
workspace↔`.plugin`; la lección `.md` de PT 4.5 no recurre).

La auditoría abrió **INC-12** (reproducibilidad de rociadores: la clase de riesgo era un dato de orquestación
del agente, no una regresión) y la **resolvió en el mismo hilo** (`iso19650-openbim` **v0.4.3**: el parser lee
`clase_riesgo` de un Pset del sistema → PCI-02 reproduce sin inyección; puertas APTO + ESPEJOS IDÉNTICOS;
núcleo e `instalaciones` intactos). Registra además **INC-13** (aproximación feeder mono+tri, ya `[confirmar
AN]`). Ninguna cambia un veredicto.

**Recomendaciones:** (1) marcar **Ola 4 ✅ cerrada (PCI + REBT)**; (2) llevar **RITE a una sub-ola 4.x
(PT 4.7)**, con el hueco ya pre-aprovisionado; (3) anunciar al núcleo la abstracción **"grafo de red +
N solvers"** (hidráulico, eléctrico; Manning en Ola 6, conductos en 4.x); (4) **distribuir
`iso19650-openbim` v0.4.3** (único reempaquetado, por INC-12; el motor v0.23.0 e `instalaciones` v0.3.0
siguen siendo los vigentes). INC-13 queda como NDP a confirmar por el técnico.

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de Caminos). NDP
`[confirmar AN]`.*

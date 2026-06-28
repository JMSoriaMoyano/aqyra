# Memoria de instalaciones — PCI · Red de rociadores automáticos (malla)

**Caso PCI-02 · Disciplina Instalaciones · Subagente `proyectista-pci` · PT 4.4 (Ola 4).**
Predimensionado/asistencia. **Todo cálculo y resultado debe ser revisado y firmado por técnico
competente (Ingeniero de Caminos).** Los valores NDP no verificados se marcan `[confirmar AN]`.

---

## 1. Objeto y normativa

Dimensionado hidráulico de predimensionado de una **red mallada de rociadores automáticos** de
protección contra incendios y comprobación de caudales y presiones en el rociador hidráulicamente
más desfavorable y en el grupo de presión.

- **UNE-EN 12845** — Sistemas fijos de lucha contra incendios. Rociadores automáticos: diseño,
  instalación y mantenimiento. Base de demanda por **densidad de descarga × área de operación**.
- **RIPCI** (RD 513/2017) — Reglamento de instalaciones de protección contra incendios.
- **UNE 23500** — Abastecimiento de agua contra incendios (grupo de presión / fuente).
- **DB-SI** del CTE (SI4) — Dotación de instalaciones de protección contra incendios.

Frontera del ecosistema (contratos del núcleo): la **lectura/escritura IFC** es de
`iso19650-openbim` (dominio MEP, C1); la **demanda** (CN-3) y el **cálculo hidráulico** son de
`instalaciones`, sobre el **modelo neutro de red**. El núcleo aporta la **topología**
(nodos+tramos); el solver **calcula**.

## 2. Descripción de la red

Red mallada en disposición de **escalera** (dos colectores conectados por montantes) con seis
rociadores colgando por ramales. Tomada de un **IFC MEP** (`rociadores-malla.ifc`,
`IfcDistributionSystem` PredefinedType=FIREPROTECTION) y traducida al modelo neutro de red por el
parser MEP de `iso19650-openbim`.

| Parámetro | Valor |
|---|---|
| Nodos | 14 |
| Tramos | 16 |
| **Lazos independientes** (m − n + 1) | **3 (red mallada)** |
| Rociadores (terminales) | 6 (ROC-1 … ROC-6) |
| Fuente | Grupo de presión PCI (nodo N1) |
| Colectores / montantes / ramales | DN100 / DN80 / DN32 |
| Material | Acero galvanizado, rugosidad absoluta 0,045 mm `[confirmar AN]` |
| Fluido | Agua 20 °C (ρ=998 kg/m³, ν=1,01·10⁻⁶ m²/s) `[confirmar AN]` |

## 3. Bases de demanda (UNE-EN 12845) — clase de riesgo OH1

Demanda por **densidad de descarga × área de operación** para **Riesgo Ordinario 1 (OH1)**
`[confirmar AN]`:

| Magnitud | Valor | Origen |
|---|---|---|
| Densidad de descarga | 5,0 mm/min | UNE-EN 12845, OH `[confirmar AN]` |
| Área de operación (sistema húmedo) | 72 m² | UNE-EN 12845, OH húmedo `[confirmar AN]` |
| Cobertura por rociador | 12 m² | `[confirmar AN]` |
| **Nº de rociadores del área más desfavorable** | **6** = ⌈72/12⌉ | — |
| Caudal mínimo por rociador | 1,00 l/s = 5,0·12/60 | densidad × cobertura |
| Factor K del rociador | 80 (l/min·bar⁻⁰·⁵) | rociador estándar 15 mm `[confirmar AN]` |
| **Presión dinámica mínima en boquilla** | **56,25 kPa** = (60/80)²·100 | Q = K·√p |
| **Caudal de diseño total** | **6,0 l/s** = 5,0·72/60 | densidad × área de operación |
| Duración / autonomía | 60 min | UNE-EN 12845, OH `[confirmar AN]` |

El dato de proyecto (IFC) de caudal/presión por terminal, si existe, **prevalece** sobre el valor
normativo por defecto (`fuente_dato`). En este caso los rociadores toman el valor normativo OH1.

## 4. Método de cálculo

- **Pérdida de carga:** Darcy-Weisbach, factor de fricción por **Swamee-Jain** (aproximación
  explícita de Colebrook-White) `[confirmar criterio]`. Mayoración por accesorios +20 % sobre la
  fricción `[confirmar AN]`. Velocidad máxima admisible 6,0 m/s `[confirmar AN]`.
- **Reparto de caudales en red mallada:** **Hardy-Cross** (corrección por lazo, exponente n=2),
  sobre la base de **ciclos fundamentales** (cuerdas del árbol generador desde la fuente). Se
  impone simultáneamente: **continuidad de caudales en los nudos** y **pérdida de carga nula
  alrededor de cada lazo** (2.ª ley de Kirchhoff hidráulica). La fricción se reevalúa por
  iteración. El árbol (sin lazos) es el caso particular de 0 correcciones.
- **Propagación de presiones** desde el grupo de presión, con cota geométrica.
- **Simultaneidad:** los **6** rociadores del área de operación más desfavorable (los más remotos).

## 5. Resultados y comprobaciones

**Convergencia del reparto de mallas (Hardy-Cross):** 3 lazos, **9 iteraciones**, residuo máximo de
cierre por lazo **5·10⁻⁶ kPa** (≈ 0). Cierre por lazo: [−5·10⁻⁶, −2·10⁻⁶, −1·10⁻⁶] kPa.

**Balance de caudales (arnés de verificación):** residuo de continuidad nodal **0,0000 %**
(caudal con signo: en cada nudo de unión entra = sale; cada rociador recibe su demanda; el grupo
inyecta el caudal total de 6,0 l/s).

**Tramos gobernantes (mayor caudal):**

| Tramo | DN (mm) | Caudal (l/s) | Velocidad (m/s) | Δp (kPa) |
|---|---|---|---|---|
| M-T1 (colector cabecera) | 100 | 3,990 | 0,508 | 0,277 |
| M-T2 | 100 | 2,250 | 0,286 | 0,098 |
| M-B1 | 100 | 2,010 | 0,256 | 0,080 |
| R-1 (montante) | 80 | 2,010 | 0,400 | 0,237 |
| D-ROC-1 (ramal rociador) | 32 | 1,000 | **1,243** | 2,262 |

**Velocidad pico:** 1,243 m/s en los ramales DN32 ≤ 6,0 m/s `[confirmar AN]` → **cumple**.

**Comprobación en rociadores (los 6 simultáneos):** presión disponible ≈ 297 kPa en todos, frente a
los **56,25 kPa** requeridos → margen ≈ 241 kPa. **Todos CUMPLEN.**

**Grupo de presión (fuente):** presión disponible **300 kPa** `[confirmar AN]` ≥ presión requerida
**58,9 kPa** (rociador gobernante ROC-3/ROC-6) → **margen 241 kPa**. Caudal de diseño 6,0 l/s frente
a 12 l/s de capacidad declarada del grupo.

> El **punto de funcionamiento** (curva demanda vs abastecimiento) queda holgadamente del lado
> seguro: el grupo entrega 300 kPa muy por encima de los 58,9 kPa que exige la red en el caudal de
> diseño de 6,0 l/s. La curva real del grupo (UNE 23500) debe verificarse en proyecto `[confirmar AN]`.

## 6. Escritura de resultados al IFC (write-back)

Cerrando el ciclo **IFC → cálculo → IFC**, los resultados se han escrito de vuelta al modelo como
**Psets de resultado** (`Pset_Estructurando_ResultadoRed`) sobre 22 elementos (16 tramos + 6
rociadores): por tramo DN dimensionado, caudal, velocidad, pérdida de carga y sentido del flujo;
por rociador caudal, presión disponible, presión mínima, margen y veredicto. El IFC enriquecido
(`rociadores-malla-resultado.ifc`) se ha **validado** con `iso19650-openbim:ifc-validate`:
continuidad de red **CUMPLE** (cobertura 100 %, 0 componentes huérfanas) y reconocimiento de los
Psets de resultado.

La **mecánica** de escritura IFC vive en `iso19650-openbim` (capa transversal); la **semántica**
(qué propiedades) la fija `instalaciones`. La orquestación la realiza el agente de disciplina.

## 7. Conclusión

La red mallada de rociadores **OH1** cumple en predimensionado: reparto hiperestático resuelto por
Hardy-Cross con cierre de lazos y balance de caudales ≈ 0, velocidades admisibles, y presión
suficiente en los seis rociadores del área de operación y en el grupo de presión. **Resultado:
CUMPLE.** Predimensionado a revisar y firmar por técnico competente.

---

### Registro de comprobaciones (2026-06-22)

| Sistema | Solver | Parámetros | Resultado | Veredicto |
|---|---|---|---|---|
| Rociadores OH1 (malla, 3 lazos) | Darcy-Weisbach + Hardy-Cross | densidad 5,0 mm/min × 72 m²; n=6; K=80; p_min 56,25 kPa | fuente 300/58,9 kPa (margen 241); v_pico 1,243 m/s; balance 0,0 %; cierre lazo 5·10⁻⁶ kPa | **CUMPLE** |

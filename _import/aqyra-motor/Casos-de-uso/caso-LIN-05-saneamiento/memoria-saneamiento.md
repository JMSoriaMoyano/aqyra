# Memoria de cálculo — red de saneamiento (colectores en lámina libre)

**Caso caso-LIN-05-saneamiento · PT 6.2 (Ola 6) · obras-lineales v0.3.0 · EN 752.**
Predimensionado/asistencia. **Debe revisarla y firmarla un técnico competente
(Ingeniero de Caminos).** Los parámetros no normalizados se marcan `[confirmar AN]`.

## 1. Objeto y normativa

Predimensionamiento hidráulico de una **red separativa de aguas residuales** (colectores
por gravedad) hasta su **vertido**, comprobando por tramo el grado de llenado, la
velocidad (autolimpieza y no erosión), la pendiente y el diámetro mínimo, conforme a la
práctica de la **EN 752** (sistemas de desagüe y alcantarillado). El cálculo hidráulico
es de **lámina libre por la fórmula de Manning** sobre el **grafo de red**.

## 2. Datos de partida

Modelo geométrico y de red tomado del **IFC MEP de saneamiento** (`IfcDistributionSystem`
PredefinedType SEWAGE), traducido al **modelo neutro de red** por el parser de
`iso19650-openbim` v0.6.0. Las **cotas de solera** (invert) de los nudos son dato del IFC
(`Pset_Estructurando_Red.CotaSolera`) y **prevalecen**; si faltaran, se tomaría la cota
del nudo como solera `[confirmar AN]`.

| Nudo | Solera (m) | Función |
|---|---|---|
| P1, P2 | 100,50 | acometida de sector |
| P4 | 100,20 | acometida de sector |
| P3 | 100,00 | pozo de registro (unión) |
| V | 99,50 | **vertido (ancla de la red)** |

Colectores de hormigón (n de Manning = 0,013 `[confirmar AN]`): COL-1 y COL-2 Ø315
(P1→P3, P2→P3), COL-3 Ø400 (P3→V), COL-4 Ø315 (P4→V).

## 3. Bases de demanda (aguas residuales, EN 752)

Caudal de cálculo por acometida = dotación × habitantes-equivalentes × coeficiente de
retorno × coeficiente de punta (+ infiltración). Valores adoptados `[confirmar AN]`:
dotación **200 l/hab·día**, retorno **0,80**, coeficiente de punta **2,5**, infiltración
**0**. Resulta 0,00463 l/s por habitante-equivalente.

| Acometida | hab-eq | Q medio (l/s) | Q punta (l/s) |
|---|---|---|---|
| ACO-1 (P1) | 2600 | 4,81 | 12,04 |
| ACO-2 (P2) | 2600 | 4,81 | 12,04 |
| ACO-3 (P4) | 1700 | 3,15 | 7,87 |
| **Caudal total vertido** | | | **31,94** |

## 4. Método de cálculo

El **solver de Manning de red** (`obras-lineales:scripts/red/solver_lamina_libre.py`)
opera sobre el grafo del núcleo (`scripts/nucleo/`, espejado byte a byte del motor):

1. **Orientación del flujo:** la red se ordena como **árbol desde el vertido** (outfall =
   ancla), reutilizando la construcción de árbol por BFS del motor de red de la Ola 4.
2. **Reparto de caudales:** por **continuidad aguas arriba** — el caudal de cada colector
   es la suma de los aportes del subárbol que drena hacia él.
3. **Hidráulica por tramo:** **calado normal** en sección parcialmente llena resolviendo
   `Q = (1/n)·A·R^(2/3)·J^(1/2)` por bisección (geometría circular reutilizada de
   `drenaje/odt.py`), con **J = pendiente de solera** en el sentido del flujo.
4. **Mallas (cableado):** el árbol es el caso de 0 lazos; si hubiera colectores en malla,
   se activa un Hardy-Cross de lámina libre (cierre por pérdida de fricción de Manning)
   `[confirmar AN]`. En este caso la red es un árbol (0 lazos).

Comprobaciones por tramo `[confirmar AN]`: grado de llenado ≤ 0,75; velocidad en
[0,6; 5,0] m/s; pendiente > 0; DN ≥ 300 mm.

## 5. Resultados

| Colector | DN (mm) | Q (l/s) | J (m/m) | calado (m) | llenado | v (m/s) |
|---|---|---|---|---|---|---|
| COL-1 | 315 | 12,04 | 0,0071 | 0,077 | 24,4 % | 0,82 |
| COL-2 | 315 | 12,04 | 0,0071 | 0,077 | 24,4 % | 0,82 |
| COL-3 | 400 | 24,07 | 0,0100 | 0,092 | 23,0 % | 1,11 |
| COL-4 | 315 | 7,87 | 0,0130 | 0,053 | 17,0 % | 0,90 |

**Verificación de continuidad:** balance nodal con signo (caudal hacia el vertido),
residuo máximo **0,0 %**. COL-3 = COL-1 + COL-2 = 24,07 l/s; el vertido recoge el total
(31,94 l/s).

## 6. Conclusión

**CUMPLE.** Todos los colectores trabajan en lámina libre con grado de llenado holgado
(≤ 24,4 % < 0,75), velocidades en banda de autolimpieza sin erosión (0,82–1,11 m/s) y
desagüe por gravedad (J > 0). Los resultados se han escrito de vuelta al IFC
(`Pset_Estructurando_ResultadoRed`) y el modelo enriquecido re-validó **CUMPLE**.

> **Salvedades / NDP a confirmar (Anejo Nacional / criterio del despacho):** dotación y
> coeficiente de punta de aguas residuales; n de Manning por material; grado de llenado
> máximo de proyecto; velocidades de autolimpieza y de no erosión; diámetro mínimo de
> colector; origen de las cotas de solera cuando no constan en el IFC. El
> **abastecimiento a presión** (EN 805) se documenta aparte (PT 6.3).

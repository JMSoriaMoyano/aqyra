# Inicio de hilo — P1·B Visor/Editor · familia de TRAZADO (geometría por alineaciones)

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo abre la **TERCERA familia geométrica** del visor: la **geometría por
ALINEACIONES** (obras lineales / infraestructura), distinta del catálogo de elementos de edificación
(ya completo) y de la auditoría normativa (transversal). Empieza por la **circulación del parking** y
escala a **trazado de carretera y urbanización**.

## ✅ ALCANCE CERRADO (JM · 2026-06-28) — no reabrir; sin parches, construir el primer slice
Decisiones de §5 ratificadas. **No re-preguntar el alcance.**
- **Primer slice (preview) = directriz horizontal recta+arco.** Clotoide y alzado → slices siguientes (el **contrato ya los contempla enteros**, no se re-toca).
- Alineación = **objeto propio** (`IfcAlignment`), no una 4.ª variante de `Placement`.
- Definición **opt-in**; derivación desde el parking → 2.º slice.
- **Asistencia de radios en este slice**: mínimo parametrizable + self-check; consulta real a `obras-lineales` → después.
- **Emitir ya** `alineaciones[]` en el `alto.json` — y **YA compila**: C1 está firmado y completo (ver abajo).
- **Contrato LISTO:** C1 «apertura familias P1» **FIRMADA** (`iso19650-openbim 0.10.0`, 28-jun) autora `alineaciones[]` → `IfcAlignment` (planta recta+arco+clotoide, alzado, sección+peralte). El cebo trabaja **contra el contrato completo**, no contra una RFC pendiente.

---

## 0. Encuadre — un tercer paradigma geométrico (no «más elementos»)
- Hasta ahora el visor modela geometría **acotada** (huellas/áreas/volúmenes: el mundo del edificio).
  Esta familia es otra cosa: la **alineación** — una directriz 1D con sección barrida. En IFC 4.3 =
  **`IfcAlignment`**: planta (recta + arco + **clotoide**), alzado (rasantes + acuerdos) y la **sección
  barrida** a lo largo.
- **Construye sobre lo que ya hay:** el *placement de LÍNEA* (muros) y los *EJES explícitos* de la
  retícula son **alineaciones degeneradas** (rectas). Lo nuevo = la **curva** (arco, clotoide) y el
  barrido de sección. No empezamos de cero.
- **Entrada por el PARKING:** la circulación (viales, rampas) obedece **radios de giro y pendientes**
  dentro de un edificio — donde edificación e infraestructura se tocan; ya hay un generador
  `parking-comb` (hoy con circulación «tonta», en peine). Es el punto 3 del brainstorm: el parking
  resuelto **desde la circulación**, anclada en los núcleos (puntos fijos: escalera/ascensor + rampa).
- **Engancha con un plugin que YA existe:** `obras-lineales` **consume `IfcAlignment`** y hace el
  trazado (3.1-IC: radios mínimos, clotoides, acuerdos, visibilidad), drenaje, firmes. **El visor
  dibuja la alineación; el plugin la asiste/audita** — mismo patrón que el CTE en edificación.

## 1. CEBO y frontera — el contrato YA está completo
- Regla CEBO: preview vivo, **sin export firmable, sin medidor visible**; el IFC autoritativo lo
  compila C1 desde `alto.json`.
- **C1 YA autora `IfcAlignment`.** La evolución «apertura familias P1» (`iso19650-openbim 0.10.0`,
  FIRMADA 28-jun, golden `C1-APERTURA-01` verde) añadió el handler `alineaciones[]` → `IfcAlignment`
  (planta recta+arco+clotoide, alzado rasantes+acuerdos, sección+peralte), reutilizando la maquinaria
  de la Ola 5 (`scripts/lineal/`). **Ya no hay RFC pendiente ni frontera abierta para alineaciones.**
- **Consecuencia:** el cebo modela y previsualiza la alineación, **asiste los radios vía
  `obras-lineales`**, y **emite `alineaciones[]` que C1 compila de verdad** (salida autoritativa
  disponible). El sellado de cada slice sigue la regla de dos llaves (golden + firma JM).

## 2. Lo que YA existe (no se reescribe)
`Entorno/publico/demo/src`: `model.ts` (`Placement` point/polygon/line; `ElementInstance`; spaces;
generadores `residence-corridor`/`parking-comb`; retícula con **ejes explícitos** `resolveGrid`/
`buildGrid`), `diseno.ts` (render 3D isométrico + planta 2D, árbol de instancias IFC, acciones del
operador IA, selección→resaltado), `c1-bridge.ts` (`toAltoSpec` → `alto.json`), `fixture.ts` (golden
determinista), `vite.config.ts` (operador IA `/__aqyra/llm` + vocabulario de acciones + prompt).
Golden `columns.golden` **35/35** + `parking.golden` 7/7 verde. Plugin **`obras-lineales`** (IFC 4.3,
3.1-IC, drenaje, firmes). **C1 0.10.0** autora `alineaciones[]` → `IfcAlignment` (golden
`C1-APERTURA-01`). (Historia detallada de la capa de elementos: en la memoria del proyecto.)

## 3. Reglas (no romper)
- **Determinismo verificable:** mismo input → misma salida; arnés + fixture golden por caso.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara y propone; NO certifica.
- **CEBO:** sin export firmable, sin medidor. El cebo previsualiza; el IFC lo compila C1.
- **Contrato C1 = COMPLETO** para alineaciones (`iso19650-openbim 0.10.0` anclado en `versions.lock`).
  El cebo consume esa versión; cualquier capacidad nueva fuera de lo previsto sí sería evolución de C1
  (bump → golden → firma, reservado a JM), pero el trazado **no** la necesita.
- **Reservado a JM:** alcance de cada slice y qué reglas de trazado entran en la asistencia/auditoría.

## 4. Alcance del primer slice (recomendado)
La **directriz horizontal** como primitivo nuevo del cebo: una **alineación = secuencia de segmentos
(recta + arco)**, con el **render de la curva** en 2D/3D. Aislar la variable nueva (la curva) antes de
aplicarla a nada. Concretamente:
- **Modelo:** una `Alineacion` determinista (lista de segmentos: recta `{inicio,fin}`, arco
  `{centro,radio,ang0,ang1}` — o el patrón PI + radio). Discretización en puntos para el dibujo.
- **Render:** el arco **real** (no una recta) en la planta 2D y en la caja 3D.
- **Asistencia:** el **radio de giro** de cada arco frente a un mínimo (parametrizable en este slice;
  consulta real a `obras-lineales` después). Avisa si no cumple (como el self-check del parking).
- **Puente:** `c1-bridge.ts` emite `alineaciones[]` en el `alto.json` → **C1 0.10.0 lo compila**
  (handoff real, ya no «pendiente»).
- **SIN** clotoide todavía en el cebo (recta+arco primero; la clotoide es el clon siguiente — el
  contrato ya la soporta), **sin** alzado/rampa (pendiente), **sin** sección barrida (después), y
  **sin** reorganizar aún la circulación del parking (ese es el 2.º slice, una vez la alineación
  existe como pieza).

## 5. Primer paso — el alcance YA ESTÁ CERRADO (ver bloque ✅ arriba)
**No re-preguntes el alcance**; construye directamente el primer slice según el bloque «ALCANCE
CERRADO» y el contrato ya firmado (C1 0.10.0). Las decisiones de abajo quedan **solo como registro**
de por qué se decidió así (ya resueltas con la recomendación):
1. Directriz horizontal **recta+arco** primero (clotoide/alzado después; el contrato ya los soporta).
2. Alineación como **objeto propio** (`IfcAlignment`), no 4.ª variante de `Placement`.
3. Definición **opt-in** (el copiloto da puntos/segmentos); derivación del parking en el 2.º slice.
4. **Asistencia de radios**: mínimo parametrizable + self-check ahora; consulta real a `obras-lineales` después.
5. **Emitir ya** `alineaciones[]` → C1 0.10.0 lo compila (handoff real).

Construye el slice, pruébalo en pantalla y déjalo con su arnés + fixture golden para la firma de JM.
La IA prepara; JM firma.

*Procedencia: P1 Visor/Editor · Aqyra · inicio de hilo de la familia de TRAZADO (geometría por alineaciones) · act. 2026-06-28 (C1 0.10.0 firmada).*

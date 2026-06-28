# Inicio de hilo — P1·B Visor/Editor · familia de TRAZADO (geometría por alineaciones)

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo abre la **TERCERA familia geométrica** del visor: la **geometría por
ALINEACIONES** (obras lineales / infraestructura), distinta del catálogo de elementos de edificación
(ya completo) y de la auditoría normativa (transversal). Empieza por la **circulación del parking** y
escala a **trazado de carretera y urbanización**.

## ✅ ALCANCE CERRADO (JM · 2026-06-28) — no reabrir; sin parches, construir el primer slice
Decisiones de §5 ratificadas. **No re-preguntar el alcance.**
- **Primer slice (preview) = directriz horizontal recta+arco.** Clotoide y alzado → slices siguientes (el **contrato** ya los contempla enteros, no se re-toca).
- Alineación = **objeto propio** (`IfcAlignment`), no una 4.ª variante de `Placement`.
- Definición **opt-in**; derivación desde el parking → 2.º slice.
- **Asistencia de radios en este slice**: mínimo parametrizable + self-check; consulta real a `obras-lineales` → después.
- **Emitir ya** `alineaciones[]` en el `alto.json` (handoff).
- Contrato: C1 **ya parsea y genera `IfcAlignment`** (Ola 5); la evolución completa (planta+alzado+sección+peralte, **sin parches**) está en `RFC_C1-apertura_familias-P1.md` / `CIERRE-ALCANCE_P1-A-B-C.md`. El cebo arranca ya sin esperar a C1.

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

## 1. CEBO y frontera — la familia ARRANCA sin esperar a C1
- Regla CEBO: preview vivo, **sin export firmable, sin medidor visible**; el IFC autoritativo lo
  compila C1 desde `alto.json`.
- PERO C1 **aún no autora `IfcAlignment`** (sus primitivas son de edificación: pilares/muros/losas/
  escaleras/rampas-de-edificio). Hay una **RFC abierta en el PANEL** (`Aqyra-Raiz/PANEL_Ahora-cebo.md`)
  para extender C1 → autoría de `IfcAlignment`.
- **Consecuencia clave:** este hilo **arranca en el cebo** (modela + previsualiza la alineación y
  **asiste los radios vía `obras-lineales`**) **sin esperar a C1**. La RFC gatea solo la **salida
  autoritativa** (que C1 compile el alignment). El puente prepara el handoff (`alineaciones[]`); la
  adopción es de JM. Igual que con `losa.huecos`, pero a mayor escala.

## 2. Lo que YA existe (no se reescribe)
`Entorno/publico/demo/src`: `model.ts` (`Placement` point/polygon/line; `ElementInstance`; spaces;
generadores `residence-corridor`/`parking-comb`; retícula con **ejes explícitos** `resolveGrid`/
`buildGrid`), `diseno.ts` (render 3D isométrico + planta 2D, árbol de instancias IFC, acciones del
operador IA, selección→resaltado), `c1-bridge.ts` (`toAltoSpec` → `alto.json`), `fixture.ts` (golden
determinista), `vite.config.ts` (operador IA `/__aqyra/llm` + vocabulario de acciones + prompt).
Golden `columns.golden` **35/35** + `parking.golden` 7/7 verde. Plugin **`obras-lineales`** (IFC 4.3,
3.1-IC, drenaje, firmes). **RFC C1→`IfcAlignment`** planteada en el PANEL. (Historia detallada de la
capa de elementos: en la memoria del proyecto.)

## 3. Reglas (no romper)
- **Determinismo verificable:** mismo input → misma salida; arnés + fixture golden por caso.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara y propone; NO certifica.
- **CEBO:** sin export firmable, sin medidor. El cebo previsualiza; el IFC lo compila C1.
- **Frontera C1** = bump → golden → adoptar si verde → anclar en `versions.lock` (reservado a JM). La
  salida autoritativa de alineaciones **espera la RFC**; mientras, el cebo previsualiza y
  `obras-lineales` asiste.
- **Reservado a JM:** alcance de cada slice, qué entra en C1 (la RFC), y qué reglas de trazado entran
  en la asistencia/auditoría.

## 4. Alcance del primer slice (recomendado)
La **directriz horizontal** como primitivo nuevo del cebo: una **alineación = secuencia de segmentos
(recta + arco)**, con el **render de la curva** en 2D/3D. Aislar la variable nueva (la curva) antes de
aplicarla a nada. Concretamente:
- **Modelo:** una `Alineacion` determinista (lista de segmentos: recta `{inicio,fin}`, arco
  `{centro,radio,ang0,ang1}` — o el patrón PI + radio). Discretización en puntos para el dibujo.
- **Render:** el arco **real** (no una recta) en la planta 2D y en la caja 3D.
- **Asistencia:** el **radio de giro** de cada arco frente a un mínimo (parametrizable en este slice;
  consulta real a `obras-lineales` después). Avisa si no cumple (como el self-check del parking).
- **Puente:** preparar `alineaciones[]` en el `alto.json` (handoff), marcado **pendiente de la RFC de
  C1** (no compila aún).
- **SIN** clotoide todavía (recta+arco primero; la clotoide es el clon siguiente), **sin** alzado/rampa
  (pendiente), **sin** sección barrida (después), y **sin** reorganizar aún la circulación del parking
  (ese es el 2.º slice, una vez la alineación existe como pieza).

## 5. Primer paso — cierra el alcance
Antes de tocar código, dime tus decisiones (reservadas a JM):
1. ¿Solo la **directriz horizontal recta+arco** primero (recomendado), o ya la clotoide / el alzado?
2. ¿La alineación como **4.ª variante de `Placement`** (`kind:"alignment"`, segmentos) o como
   **objeto/elemento propio** (`IfcAlignment` con su lista de segmentos)? (rec.: objeto propio.)
3. ¿Cómo se define en este slice: **acción opt-in** (el copiloto da puntos/segmentos) o **derivada del
   parking** ya aquí? (rec.: opt-in primero; derivación del parking en el siguiente.)
4. **Asistencia de radios** (`obras-lineales`): ¿en este slice o después? ¿mínimo parametrizable o
   consulta real al plugin? (rec.: mínimo parametrizable + self-check ahora; consulta real después.)
5. ¿Emitimos ya el handoff `alineaciones[]` al puente (preparado para la RFC), o esperamos a que la RFC
   de C1 esté firmada? (rec.: prepararlo ya, marcado como pendiente de RFC.)

Con eso cerrado, construyo el slice, lo pruebo en tu pantalla y lo dejo con su arnés + fixture golden
para tu firma. La IA prepara; JM firma.

*Procedencia: P1 Visor/Editor · Aqyra · inicio de hilo de la familia de TRAZADO (geometría por alineaciones) · para JM.*

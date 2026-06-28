# Inicio de hilo — P1·A Visor/Editor · geometría de EDIFICACIÓN (envolvente poligonal + cierre de catálogo)

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo continúa la familia de **geometría de EDIFICACIÓN**. El catálogo de
elementos ya está completo; quedan **dos frentes**: cerrar cabos del catálogo (ascensor, rampa de
edificio…) y, sobre todo, **el SALTO** — generalizar la huella de **rectángulo a POLÍGONO**, que
desbloquea solares reales (Catastro).

## ✅ ALCANCE CERRADO (JM · 2026-06-28) — no reabrir; sin parches, construir el primer slice
Decisiones de §5 ratificadas. **No re-preguntar el alcance.**
- **Primer slice = envolvente POLIGONAL** (el salto), no el ascensor.
- Solo **envolvente** (fachada=aristas · forjado/cubierta=polígono · retícula **recortada** a nudos dentro). Subdivisión poligonal de espacios → diferida.
- Polígono **opt-in** (vértices del copiloto); Catastro como fuente → después.
- **W×D se mantiene como bbox/marco.**
- Emitir **todo explícito**; el macro `edificio` ancho×largo queda solo informativo.
- **Ascensor:** `ifcClass:"IfcTransportElement"` por el handler genérico `elementos[]` (catálogo abierto, sin tocar el contrato).
- **Contrato LISTO:** C1 «apertura familias P1» **FIRMADA** (`iso19650-openbim 0.10.0`, 28-jun) — huecos generalizados, **catálogo de clases abierto**, doble clasificación bsDD+Uniclass, alineaciones. El cebo emite **contra el contrato completo**; A es **frontera-cero**. Dos llaves siguen para sellar cada slice.

---

## 0. Encuadre — geometría acotada, dos frentes
La geometría de edificación es **acotada** (huellas/áreas/volúmenes). El catálogo de elementos está
hecho: pilares (retícula con **ejes explícitos**), forjados + cubierta + huecos de núcleo, muros
(fachada · tabique por línea · divisoria por lindes · núcleo **pasante**), carpintería (puerta/ventana
con `host`), escalera. Quedan:

- **A.1 — cerrar el catálogo:** el **ascensor** (clon de la escalera: contenido del núcleo) y la
  **rampa de edificio** (C1 ya tiene `rampas`), más las clases que falten. Clones del molde
  (`ElementInstance` + otra `ifcClass`).
- **A.2 — el SALTO: huella POLIGONAL.** Hoy todo se apoya en un rectángulo `W×D`. Generalizar a
  **polígono** (contorno arbitrario): la **fachada** pasa a ser las aristas del polígono, el **forjado/
  cubierta** el polígono, la **retícula recortada** al polígono. **Desbloquea solares reales** y
  conecta con el **contorno de Catastro** (P1·A). El forjado **ya es polígono** y los muros **ya son
  segmentos**, así que estamos a medio camino. Lo difícil que se **difiere**: subdividir un polígono en
  **habitaciones** (los generadores sobre forma irregular).

## 1. CEBO y frontera — el salto es (casi) frontera-cero
- Regla CEBO: preview vivo, **sin export firmable, sin medidor**; el IFC autoritativo lo compila C1.
- **Frontera amable:** el cebo ya **autora explícito** (`losas`-polígono, `muros`-segmento, `pilares`,
  `escaleras`); C1 monta polígonos y muros arbitrarios **sin tocar nada**. El único supuesto rectangular
  en la frontera es el macro `edificio` (ancho×largo), que el cebo **casi no usa** (ya pone
  `pilares/forjados/muros_perimetrales:false`). Por eso la **envolvente poligonal es mayormente
  frontera-cero**.
- **Ascensor: ya cubierto.** C1 0.10.0 autora **cualquier `ifcClass`** (catálogo abierto;
  `IfcTransportElement`/ELEVATOR verificado en la golden `C1-APERTURA-01`) → **frontera-cero, sin bump**.

## 2. Lo que YA existe (no se reescribe)
`Entorno/publico/demo/src`: `model.ts` (`Placement` point/polygon/line; `ElementInstance`; spaces;
generadores `residence-corridor`/`parking-comb`; retícula con **ejes explícitos** `resolveGrid`/
`buildGrid`; `spaceBoundaryWalls` para lindes; `findHostWall` para carpintería), `diseno.ts` (render 3D
isométrico + planta 2D, árbol IFC, acciones del operador IA, selección→resaltado), `c1-bridge.ts`
(`toAltoSpec` → `alto.json`; ya emite `pilares`/`losas`(con huecos)/`muros`/`escaleras` explícitos),
`fixture.ts` (golden determinista), `vite.config.ts` (operador IA + acciones + prompt). Golden
`columns.golden` **35/35** + `parking.golden` 7/7 verde. (Historia detallada de la capa de elementos:
en la memoria del proyecto.)

## 3. Reglas (no romper)
- **Determinismo verificable:** mismo input → misma salida; arnés + fixture golden por caso.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara y propone; NO certifica.
- **CEBO:** sin export firmable, sin medidor. El cebo previsualiza; el IFC lo compila C1.
- **Frontera C1** = bump → golden → adoptar si verde → anclar en `versions.lock` (reservado a JM).
- **Reservado a JM:** alcance de cada slice, qué clases del catálogo entran, qué entra en C1.

## 4. Alcance del primer slice (recomendado)
Dos candidatos. Recomiendo abrir por **el salto (A.2)** porque es lo que **define** este hilo; el
**ascensor (A.1)** es un **calentamiento rápido** si prefieres cerrar el núcleo primero.

**Opción SALTO — envolvente poligonal (shell):** introducir un **contorno de edificio poligonal**
(lista de vértices) y hacer que deriven de él, **aislando la variable nueva** (el contorno):
- **Fachada** = aristas del polígono (cualquier nº/ángulo), por planta.
- **Forjado/cubierta** = el polígono.
- **Retícula** = ejes rectangulares **recortados** al polígono (solo nudos **dentro**).
- Mantener el bbox `W×D` como **marco** (cámara/extent).
- **Sin** subdivisión poligonal de espacios (el caso difícil; después), **sin** Catastro como fuente
  todavía (opt-in: el copiloto da los vértices; Catastro después), **sin** alzado/voladizos.

**Opción CALENTAMIENTO — ascensor:** clon de la escalera, contenido en el núcleo
(`ifcClass:"IfcTransportElement"` por el handler genérico), por planta/hueco. **C1 0.10.0 ya lo
soporta (frontera-cero).**

## 5. Primer paso — el alcance YA ESTÁ CERRADO (ver bloque ✅ arriba)
**No re-preguntes el alcance**; construye directamente el primer slice (envolvente poligonal) según el
bloque «ALCANCE CERRADO», contra C1 0.10.0 ya firmado. Las decisiones de abajo quedan **solo como
registro** de por qué se decidió así (ya resueltas con la recomendación):

Envolvente poligonal:
1. ¿Solo la **envolvente** (fachada/forjado/retícula recortada) primero, o ya la **subdivisión
   poligonal de espacios**? (rec.: solo envolvente; subdivisión después.)
2. ¿El polígono por **acción opt-in** (vértices del copiloto) o del **contorno de Catastro** (P1·A)?
   (rec.: opt-in primero; Catastro como fuente después.)
3. ¿Retícula **recortada** al polígono (nudos dentro) o rectangular sobre el bbox? (rec.: recortada.)
4. ¿Mantenemos `W×D` como **bbox/marco** junto al polígono? (rec.: sí.)
5. Frontera: ¿dejamos de usar el macro `edificio` ancho×largo (emitir **todo explícito**) o lo
   mantenemos como bbox informativo? (rec.: explícito; bbox solo informativo.)

Ascensor (calentamiento opcional): driver = cada `Nucleo` con detalle «ascensor» → N ascensores,
contenidos en el espacio del núcleo, con `ifcClass:"IfcTransportElement"` (ya soportado por C1 0.10.0;
frontera-cero).

Con eso cerrado, construyo el slice, lo pruebo en tu pantalla y lo dejo con su arnés + fixture golden
para tu firma. La IA prepara; JM firma.

*Procedencia: P1 Visor/Editor · Aqyra · inicio de hilo de la familia de geometría de EDIFICACIÓN · para JM.*

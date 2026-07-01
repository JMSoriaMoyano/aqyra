# Decopak — Depósito enterrado · Hilo de inicio: cálculo de la estructura desde el IFC

Cómo usar este texto: copia todo lo que hay bajo la línea y pégalo como **primer mensaje** de un hilo nuevo del proyecto Estructurando 2.0 («Estructura del Depósito de Decopak»). Es autocontenido.

---

## 0. Objetivo

A partir del modelo IFC del **depósito enterrado de Decopak** y con los plugins/agentes del ecosistema Estructurando, calcular la estructura: obtener esfuerzos, comprobar/armar los elementos según Eurocódigos (Anejo Nacional español) y preparar la memoria de cálculo y la evidencia de QA para que JM firme.

## 1. Entrada

- **Modelo:** `pilotos/decopak-deposito/modelo/DepositoDecopakEnterrado.ifc`
- **Qué es:** IFC2X3 (export de Revit, vista de coordinación; «DECOPAK_4_CIMENTACIÓN»). Estructura de **hormigón armado de un depósito enterrado** (cajón estanco), del mismo cliente y emplazamiento que Decopak HQ (Rubí, Barcelona). Elementos del modelo:
  - **Losa de fondo / cimentación** («Losa depósito», `IfcSlab` BASESLAB).
  - **Muros perimetrales de contención de 50 cm** (`IfcWall`/`IfcWallStandardCase`, «Muro contención 50cm») — los **4 muros laterales que contienen tierras**.
  - **Muros interiores de 20 cm** («Mur contenció 20») que **compartimentan** el depósito.
  - **Losas superiores de 60 cm y 70 cm** (`IfcSlab` FLOOR) — incluyen la **losa superior transitable**.
  - **Juntas de estanqueidad** Sika Waterbar (`IfcCovering`, no estructural).
  - Materiales: hormigón in situ + hormigón de cimentación HA (grado a confirmar; proponer HA-30/B500S salvo dato).
- **Condiciones de servicio (dadas por JM):**
  1. El **depósito interior mayor está lleno de agua** → empuje hidrostático sobre los muros que lo limitan y sobre la losa de fondo.
  2. Por la **losa superior transitan vehículos pesados** → sobrecarga de tráfico en la losa de cubierta.
  3. Los **4 muros laterales contienen tierras** → empuje del terreno (+ sobrecarga en trasdós).
- **Estado del modelo:** es **físico** (geometría + materiales), en coordenadas compartidas de Revit, **sin dominio de análisis** (ni cargas, ni apoyos, ni eje analítico): hay que **idealizar desde el físico** y **autorar las acciones**. Confirmar dimensiones reales y cota de implantación al idealizar (las coordenadas Z del IFC son de sitio, no la altura de la pieza).

## 2. Plugins / agentes a usar (ecosistema Estructurando)

- **Orquestador:** agente `motor-calculo-estructural:ingeniero-estructurista` — clasifica cada elemento/caso, lo enruta y corre el flujo IFC → modelo → FEM → combinaciones ELU/ELS → verificación → memoria. Casos del catálogo aplicables: **muro de contención (ménsula)**, **losa sobre apoyos / losa plana + punzonamiento**, **losa de cimentación (raft) sobre lecho elástico**.
- **Lectura/validación del modelo:** plugin `iso19650-openbim` (`ifc-validate`, parser) para extraer el dominio estructural y comprobar el modelo antes de calcular.
- **Normativa de cálculo:** plugin `estructuras-eurocodigos` —
  - `bases-acciones` (EC0/EC1): combinaciones, coeficientes; cargas de agua, tierras, tráfico, térmicas.
  - `hormigon-ec2` (EC2): muros, losas, cimentación; flexión, cortante, **punzonamiento** (losa superior bajo vehículos) y **fisuración**.
  - `geotecnia-sismico-ec7-ec8` (EC7/EC8): **empuje de tierras**, **flotación/subpresión**, capacidad portante de la losa de fondo, y sismo si aplica.
  - `memoria-calculo` y `criterios-memoria`.
- **Tráfico:** para la sobrecarga de **vehículos pesados** sobre la losa superior, modelo de carga tipo **IAP-11 (LM1: tándem + UDL)** o vehículo pesado equivalente (apoyarse en `bases-acciones` / el vertical de cargas móviles del ecosistema).
- **Estanqueidad/fisuración:** aplicar **EN 1992-3** (estructuras de contención de líquidos) además de EC2, por ser un depósito de agua.

## 3. Flujo de trabajo

1. Leer los README de las carpetas implicadas (`pilotos/decopak-deposito/`, `qa/`, `contratos-golden/`) y el `GOBIERNO_QA_Y_VERSIONES.md` antes de empezar.
2. **Parsear y validar el IFC** (IFC2X3): extraer muros (50/20 cm), losas (fondo, 60, 70 cm), compartimentos, geometría y materiales; confirmar dimensiones y cota de implantación; comprobar coherencia.
3. **Fijar las bases de acciones (propuesta para JM)** — EC0/EC1 + AN español:
   - **Peso propio** (HA).
   - **Empuje hidrostático del agua** (γw = 10 kN/m³) con el **compartimento mayor lleno**; casos **depósito lleno** y **vacío**.
   - **Empuje de tierras** sobre los 4 muros perimetrales (EC7): al **reposo K0** (estructura enterrada y arriostrada por las losas) + **sobrecarga en trasdós** (tráfico junto al depósito).
   - **Sobrecarga de tráfico pesado** sobre la losa superior (IAP-11 LM1 / vehículo pesado): flexión y **punzonamiento**; reparto a través del relleno si lo hay.
   - **Subpresión / flotación** (depósito enterrado + nivel freático): **caso depósito vacío** → estabilidad a flotación (EC7).
   - **Térmica y retracción** + **estanqueidad** (EN 1992-3): control de fisuración estricto (wk según clase de exposición; depósito de agua).
   - **Sismo** (mismo emplazamiento que HQ: ab = 0,04 g, ac ≈ 0,046 g) + **empuje hidrodinámico** del agua (EC8-4, depósitos) — **proponer y justificar** si procede.
4. **Clasificar y calcular por elemento**, con foco en los criterios que dan sentido al caso (**estanqueidad/fisuración** y **flotación**):
   - Muros perimetrales 50 cm: flexión vertical/horizontal por agua+tierras (EC2) + estabilidad (EC7).
   - Muros interiores 20 cm: empuje diferencial de agua entre compartimentos.
   - Losa de fondo: reacción del terreno + subpresión (raft sobre lecho elástico, EC2/EC7).
   - Losa superior: tráfico pesado → flexión + **punzonamiento** (EC2).
   - Comprobaciones globales: **flotación** (vacío + freático), fisuración/estanqueidad (EN 1992-3).
5. **Entregar:** esfuerzos, aprovechamientos (≤ 1), armado por elemento y la memoria de cálculo.

## 4. Gobierno (obligatorio)

- **QA independiente de dos llaves:** este hilo **produce** el cálculo (rol build). La verificación la hace un agente de QA en **ejecución separada**, con su propio oráculo (PyNite por defecto; analítico / 2.º código FEM / MMS donde no llegue). Aquí se **prepara la evidencia**, no se certifica.
- **La IA no firma ni certifica.** Un resultado solo se certifica con **golden verde + informe de QA limpio + firma de JM**. Marca todo entregable como **propuesta pendiente de verificación y firma**.
- **Versiones ancladas:** el cálculo consume las versiones del núcleo de `versions.lock`; registra la versión real usada (si sigue en `0.0.0`, márcalo «versión no anclada») para que el cálculo sea reproducible.
- **Reutiliza el geotécnico del emplazamiento:** el informe SOCOTEC de Rubí ya sintetizado para HQ (`pilotos/decopak-hq/calculo/04_geotecnia_sintesis.md`) aporta unidades UG2/UG3, **nivel freático (+142,6 a +144,6 msnm)** —clave para la flotación— y sismo (ab=0,04 g). ⚠️ **Confirmar la cota de implantación del depósito** (puede diferir de la de HQ) antes de aplicar empujes, freático y portante.
- **Casos golden candidatos:** propón a `pilotos/decopak-deposito/golden-candidatos/` los casos que lo merezcan (muro a flexión por agua+tierras; losa superior a punzonamiento por tándem; flotación del vaso vacío), con su oráculo y tolerancia; los aprueba JM.
- **ROI:** registra horas y retrabajo en `pilotos/decopak-deposito/roi/` (unidades A2.1).

## 5. Entregables

- Hipótesis de acciones y combinaciones (propuesta para JM), incluidos los **casos críticos**: (a) servicio = lleno + tierras + tráfico; (b) **flotación** = vacío + freático alto; (c) losa superior bajo tándem pesado (punzonamiento).
- Esfuerzos, aprovechamientos y **armado** por elemento/subsistema.
- Memoria de cálculo en `pilotos/decopak-deposito/calculo/`.
- Evidencia para QA (entrada → versión → norma → resultado → oráculo) y candidatos a golden.
- Formato: Markdown en el repo. Sin .docx salvo que JM lo pida.

## Procedencia

Brief preparado por la IA (PM/estructurista) en el hilo principal de Estructurando 2.0 · 2026-06-24 · para lanzar el hilo de cálculo del Depósito enterrado de Decopak, replicando el flujo aplicado a Decopak HQ. La IA opera; JM firma.

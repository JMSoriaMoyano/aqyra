# Decopak HQ — Hilo de inicio: cálculo de la estructura desde el IFC

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como primer mensaje de un hilo nuevo del proyecto Estructurando 2.0. Es autocontenido.

---

## 0. Objetivo

A partir del **modelo IFC de Decopak HQ** y apoyándote en los **plugins/agentes del ecosistema Estructurando**, **calcular la estructura**: obtener esfuerzos, comprobar los elementos según Eurocódigos (Anejo Nacional español) y preparar la **memoria de cálculo** y la **evidencia de QA** para que JM firme.

## 1. Entrada

- **Modelo:** `pilotos/decopak-hq/modelo/DEC-PB-EBAN-HQ-Y-BIM-EST-02-EstructuraNucleoLateral-S1-v0.0.ifc`
- **Qué es:** IFC4 (texto, openBIM), edificio de oficinas en Rubí (Barcelona), nacido en lenguaje natural ("Variante B v3 OPTIMIZADO EC3"). 7 plantas (cota −1,5 cimentación → +15 cubierta). Estructura **mixta**: acero **S355** + hormigón **HA-30 / B500S** + forjados **CLT/cassette** (ligeros, para resolver grandes voladizos). Contiene vigas, montantes, pilotes, zapatas, losas y muros, con Psets de límite elástico y fuego (R60).
- **Foco del proyecto:** es un edificio de **grandes voladizos**; la solución de voladizo ligero (CLT) es el criterio que da sentido al caso.

> Estado del modelo: es la **semilla** (geometría + materiales + estructura espacial). No trae cargas ni resultados de análisis: hay que definir las hipótesis de acciones.

## 2. Plugins / agentes a usar (ecosistema Estructurando)

- **Orquestador:** agente `motor-calculo-estructural:ingeniero-estructurista` — clasifica cada elemento/caso, lo enruta al módulo de cálculo, corre el flujo IFC → modelo → FEM → combinaciones ELU/ELS → verificación → memoria.
- **Lectura/validación del modelo:** plugin `iso19650-openbim` (`ifc-validate`, parser) para extraer del IFC el dominio estructural y comprobar nomenclatura/Psets antes de calcular.
- **Normativa de cálculo:** plugin `estructuras-eurocodigos` —
  - `bases-acciones` (EC0/EC1): combinaciones, coeficientes parciales y de simultaneidad, cargas de uso/viento/nieve/térmicas.
  - `acero-ec3` (EC3): perfiles metálicos, pandeo, clasificación, uniones.
  - `hormigon-ec2` (EC2): zapatas, muros, losas de hormigón.
  - `mixtas-madera-ec4-ec5` (EC4/EC5): forjados mixtos / CLT.
  - `geotecnia-sismico-ec7-ec8` (EC7/EC8): pilotes, zapatas, sismo si aplica.
  - `memoria-calculo`: redacción de la memoria justificativa.
  - `criterios-memoria`: para que el piloto recuerde decisiones/hipótesis entre hilos.

## 3. Flujo de trabajo

1. **Leer los README** de las carpetas implicadas (`pilotos/decopak-hq/`, `qa/`, `contratos-golden/`) y el `GOBIERNO_QA_Y_VERSIONES.md` antes de empezar.
2. **Parsear y validar el IFC**: extraer el dominio estructural (elementos, materiales, geometría, niveles), comprobar coherencia.
3. **Fijar las bases de acciones** (EC0/EC1, Anejo Nacional): uso administrativo, cargas permanentes y de uso, viento (emplazamiento Rubí), nieve, térmicas y sismo (zona) — **dejar las hipótesis escritas y propuestas a JM**.
4. **Clasificar y calcular por elemento/subsistema**, con foco en los **voladizos** y el forjado CLT: esfuerzos (FEM) → combinaciones ELU/ELS → comprobación por Eurocódigo (EC3 acero, EC2 hormigón, EC4/EC5 mixtas/madera, EC7 cimentación).
5. **Entregar resultados:** esfuerzos, aprovechamientos (≤ 1), comprobaciones por elemento, y la **memoria de cálculo**.

## 4. Gobierno (obligatorio)

- **QA independiente de dos llaves:** este hilo **produce** el cálculo (rol *build*). La **verificación la hace un agente de QA en ejecución separada**, con su propio oráculo (PyNite por defecto; jerarquía analítico / 2.º código FEM / MMS donde no llegue). Aquí se **prepara la evidencia**, no se certifica.
- **La IA no firma ni certifica.** Un resultado solo se certifica con golden verde + informe de QA limpio + **firma de JM**. Marca todo entregable como *propuesta pendiente de verificación y firma*.
- **Versiones ancladas:** el cálculo consume las versiones del núcleo fijadas en `versions.lock`. ⚠️ Hoy están en `0.0.0` (pendiente del primer tag, tarea N1.1): **registrar qué versión real se usa** para que el cálculo sea reproducible.
- **Casos golden candidatos:** propón a `pilotos/decopak-hq/golden-candidatos/` los casos que merezcan entrar en la suite (con su oráculo y tolerancia); los aprueba JM.
- **ROI:** registra horas y retrabajo en `pilotos/decopak-hq/roi/` (unidades A2.1: comprobación por elemento, memoria de cálculo).

## 5. Entregables

- Hipótesis de acciones y combinaciones (propuesta para JM).
- Esfuerzos y comprobaciones por elemento/subsistema, con aprovechamientos.
- **Memoria de cálculo** en `pilotos/decopak-hq/calculo/`.
- Evidencia para QA (entrada → versión → norma → resultado → oráculo) y candidatos a golden.
- **Formato: Markdown** en el repo. Sin .docx salvo que JM lo pida.

---

### Procedencia

Brief preparado por la IA (PM/estructurista) en el hilo principal de Estructurando 2.0 · 2026-06-23 · para lanzar el hilo de cálculo de Decopak HQ.

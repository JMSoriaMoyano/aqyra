# CN-3 — Convención de acciones / bases de cálculo / bases de demanda

> **Reconciliación de numeración (2026-06-27, firmada por JM).** Lo que el ecosistema venía rotulando «C4 — acciones / bases de cálculo / bases de demanda» **no es una interfaz entre piezas, es una convención de entrada compartida**; por el criterio de nomenclatura (interfaces C1–C8 · convenciones de núcleo CN-*) pasa a **CN-3**. El número **C4 canónico queda libre para "red"** (la interfaz del grafo de red, aún sin documento de contrato). Se ejecutó un barrido de las referencias «C4 = acciones/demanda» en las disciplinas, renombrándolas a CN-3 (sin tocar EC4, MITC4, C40/50 ni etiquetas de pieza).

**Núcleo transversal.** Define la **capa de entrada común** a cualquier disciplina: las acciones y bases de cálculo de las que parte el dimensionado. Estado a 2026-06-27.

> Principio: es **dato de entrada**, no cálculo. El grafo/modelo de red (interfaz **C4 = red**) y los solvers consumen esta convención; aquí solo se fija **qué cargas/demandas entran y cómo se expresan**.

---

## 1. Alcance (las tres formas de la misma convención)

- **Estructuras:** acciones y combinaciones EC0/EC1 + DB-SE-AE (permanentes, sobrecargas de uso, viento, nieve, térmicas, sísmica). Implementa: skill `estructuras-eurocodigos:bases-acciones`.
- **Instalaciones (MEP):** bases de demanda (caudales, potencias, ocupación, simultaneidad). Implementa: `instalaciones/scripts/.../bases_demanda.py` (gancho `demanda` del modelo neutro de red, C1 §4).
- **Obra lineal:** acción del tráfico (categoría de tráfico pesado para firmes), hidrología (caudales de cálculo 5.2-IC), demanda residual/abastecimiento (EN 752 / EN 805). Implementa: `obras-lineales/scripts/.../bases_*.py`.

## 2. Reglas

- **Es entrada, no interfaz de pieza:** se expresa como datos (acciones/combinaciones, demandas) que alimentan el modelo de red (C4) y los solvers.
- **Trazabilidad normativa:** citar la norma (EC0/EC1, DB-SE-AE, RIPCI/UNE, 5.2-IC, EN 752/805); marcar **[confirmar AN]** los NDP.
- **Unidades SI** declaradas.
- **Frontera:** C1 lee el IFC y da el modelo neutro/red; **CN-3** rellena las acciones/demandas; el solver de la disciplina calcula. (En el contrato C1 esta frontera aparece como «C1 lectura ↔ CN-3 demanda ↔ cálculo».)

## 3. Relación con los demás contratos

- **C1** (parser/IFC) entrega el modelo neutro y el grafo de red; deja el gancho `demanda` para CN-3.
- **C4** (red) es la **interfaz** del grafo de red (nodos/tramos) — distinta de esta convención de entrada.
- **C5** (motor-fem) consume las acciones estructurales de CN-3 para el cálculo FEM.

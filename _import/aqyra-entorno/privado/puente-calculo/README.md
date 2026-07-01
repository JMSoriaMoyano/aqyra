# puente-calculo/ — adaptador del contrato C5 (ANZUELO · privado)

Adaptador que conecta el **modelo analítico `proposal`** del visor (cebo, `publico/`) con el **motor de cálculo anclado** (`motor-fem 0.1.0`, `../../integracion/versions.lock`) y devuelve **resultados con su estado de dato** para que el visor los pinte **bajo dos llaves**. Es el contrato **C5** del ecosistema (D-019).

> **Frontera cebo/anzuelo:** los **tipos** del modelo de entrada y del esquema de resultados son **públicos** (`publico/openbim`); el **adaptador** (esta carpeta: traducción de ejes/signos/releases, invocación del *solve*, mapeo) y el **motor** son **privados**. La regla: si filtrarlo erosiona el foso, es privado. La traducción rol→motor→Eurocódigo y la disciplina de signos son criterio de ingeniería = moat.

## Qué hace (D-019·B)

1. **Serialización modelo→motor** — recibe el `StructuralModel` C5 serializado (JSON del visor) y lo parsea (`contract.py`).
2. **Traducción (el moat, D-018/D-020)** — `translate.py`:
   - ejes locales **por rol** (`strong`→PyNite z/`Iz`, `weak`→PyNite y/`Iy`) — nunca se pasa la letra cruda entre capas;
   - **N>0 = tracción**; V/M/T en la convención canónica de PyNite;
   - **releases** (true=liberado) → `def_releases`; **apoyos** (true=restringido) → `def_support`;
   - **gravedad −Z** global; **combinaciones** `{caso: factor}` → combos del motor;
   - **carga por área** repartida a vigas de borde / nudos por área tributaria.
3. **Invocación del solve** — `engine.py` consume `motor-fem 0.1.0` **anclado** vía un **puerto** (`MotorFemPort`); no lo bifurca. Si el motor no está instalado, falla con un mensaje claro (en CI/JM se instala el motor anclado).
4. **Mapeo de resultados** — `adapter.py` traduce la salida del motor al esquema público (`ResultGroup`/`MemberResult`/`NodeResult`/`SurfaceResult`), alineando signos, y marca cada grupo **`computed`** (0 llaves). El paso a `qa-passed` (PyNite, D-023) y a `verified-signed` (firma de JM) es de los otros carriles.
5. **Write-back** — `writeback.py` anexa los resultados al IFC como bloque alineado a **`IfcStructuralResultGroup`** / **`IfcStructuralReaction`**, diff-able (mecanismo *append* de D-013), con su estado.

## Dos llaves (gobierno)

Este adaptador produce **solo `computed`** — nunca `verified-signed`. La 1.ª llave la pone la **QA independiente con PyNite** (`../`, D-023; código ≠ `motor-fem`); la 2.ª, la **firma de JM**. La IA opera; **JM firma**.

## Estado

Primer corte de V3 (paso 3 del §8 de la spec). La traducción, el mapeo y el write-back están implementados y testeados con un **motor falso** (`FakeMotor`) porque `motor-fem` se consume anclado y no se vendoriza aquí; el *solve* real corre en el entorno de JM con el motor anclado. Pendientes: binding concreto a la API de `motor-fem 0.1.0`, comprobación EC3 de aprovechamiento (paso 5 / D-022) y reparto tributario geométrico fino de la carga por área.

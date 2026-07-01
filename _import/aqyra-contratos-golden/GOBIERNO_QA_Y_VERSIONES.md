# Gobierno de QA y de versiones — Estructurando 2.0

**Documento de gobierno** · pseudotécnico, para el equipo (JM + agentes IA)
**Versión** 1.0 · Junio 2026 · **Estado:** vigente
**Ámbito:** ejecución del backlog de la Fase 0 (industrialización del ecosistema). Define cómo se verifican los cálculos (QA independiente) y cómo conviven los dos proyectos mediante versiones (Estructurando = productor · Estructurando 2.0 = consumidor).

---

## 0. Principio rector

Dos mecanismos, un único propósito:

> **El control de versiones da un blanco estable; la QA independiente da confianza en ese blanco.**

Sin lo primero, la QA verifica algo que cambia bajo sus pies. Sin lo segundo, se tiene un blanco estable en el que nadie confía. Ambos son la columna que lleva el ecosistema del nivel artesanal (N0) al de producción certificada (N4–N5).

---

## A. Control de versiones — contrato productor/consumidor

### A.1. Se versionan los contratos, no solo el código

Los **contratos** (C1, C4, C5…) son la superficie de interfaz entre el núcleo y sus consumidores: qué entra, qué sale y con qué significado, con independencia de la implementación interna. Se versionan con **SemVer** `MAJOR.MINOR.PATCH`:

- **MAJOR** — cambia un contrato (incompatible). Los consumidores deben adaptarse y revalidar.
- **MINOR** — añade capacidad de forma compatible. Se puede actualizar sin tocar nada.
- **PATCH** — corrige un fallo sin cambiar comportamiento ni interfaz.

El dígito MAJOR salta cuando cambia un contrato; ese es el criterio que gobierna el versionado.

### A.2. Productor / consumidor

- **Estructurando = productor.** Desarrolla de forma artesanal en su rama, pero *publica* releases etiquetadas y firmadas (empaquetado de N1.3): `nucleo-vX.Y.Z`, `iso19650-vX.Y.Z`, `puentes-vX.Y.Z`, etc., cada una con changelog y la versión de contrato que satisface.
- **Estructurando 2.0 = consumidor.** Fija versiones exactas en un **lockfile** (`versions.lock`). Nunca consume la rama viva ni «latest». Subir de versión es deliberado: bump del pin → re-correr la suite golden → adoptar solo si verde.

Es el modelo npm/pip aplicado puertas adentro: el productor publica paquetes versionados; el consumidor los ancla con lockfile, para que cada cálculo sea **reproducible** y defendible en el tiempo.

### A.3. Flujo y puerta de compatibilidad

Sobre el monorepo (N1.1), «publicar» = tag + paquete interno versionado y firmado. Cuando Estructurando publica una versión nueva, la CI de 2.0 la prueba contra la suite golden en una rama *candidata*:

- **Verde** → se adopta (se sube el pin en `versions.lock`).
- **Rojo** → o es una **regresión** accidental (la corrige Estructurando) o es un cambio de contrato intencionado (**MAJOR**: 2.0 adapta su adaptador y actualiza los valores esperados por el proceso aprobado por JM).

Es la disciplina «strangler / sin regresión vs PyNite» generalizada a la frontera entre proyectos.

### A.4. Anti-divergencia

Un único núcleo, propiedad de Estructurando. 2.0 **nunca lo bifurca de forma permanente**; si necesita un cambio, lo *solicita* y Estructurando publica una versión nueva. Una sola fuente de verdad.

---

## B. QA independiente — que nadie corrija su propio examen

### B.1. Principio: separación de funciones

Quien produce no aprueba. El agente que escribe el código o genera el cálculo es **distinto** del que verifica, en **ejecución separada** (subagente con su propio contexto y prompt) — el principio de «ojos frescos».

### B.2. Tres capas de verificación

Formalizan el `verificar_espejo_nucleo.py`:

1. **Numérica (oráculo).** Cada módulo se contrasta contra una referencia *independiente del propio motor* (ver jerarquía en B.3). Tolerancias por magnitud → veredicto determinista.
2. **Normativa.** Un comprobador de reglas separado verifica límites de código: cuantías, flechas, aprovechamiento ≤ 1, EC2/EC3/CTE/IC.
3. **Regresión.** La suite de **casos golden**, congelada, corre en CI en cada cambio; cualquier desviación = puerta roja.

### B.3. Jerarquía de oráculos *(criterio; punto 2 abierto)*

El cálculo a mano solo sirve para casos triviales. Para cada caso se usa el oráculo de mayor nivel disponible:

1. **Solución analítica (cerrada)** para casos canónicos —incluida la forma cerrada de Timoshenko, p. ej. `δ = 5wL⁴/384EI + wL²/8κGA`— codificada como referencia exacta.
2. **Un segundo código FEM independiente y validado** que cubra la formulación donde PyNite (Euler-Bernoulli + DKMQ) no llegue. Candidatos a evaluar: Frame3DD, CalculiX, code_aster, OpenSees. El espejo debe usar la **misma teoría** que se comprueba.
3. **Método de las soluciones manufacturadas (MMS)** como recurso general cuando no hay ni fórmula ni segundo código.

Transversalmente, **verificaciones sin oráculo** (correctitud matemática): patch test, estudio de convergencia / orden de precisión, balance de energía y equilibrio, modos de sólido rígido. Y **benchmarks NAFEMS** (Scordelis-Lo, cilindro pellizcado, Cook's membrane, MacNeal-Harder) como dianas estándar.

> **Punto abierto:** la redacción definitiva y la elección del segundo código (Frame3DD / CalculiX / code_aster / OpenSees) se resolverán **caso a caso** cuando aparezca la formulación concreta (previsiblemente Timoshenko en un piloto). PyNite es el espejo por defecto. **JM elige el oráculo y fija la tolerancia.**

### B.4. Quién hace qué

| Actor | Función | No puede |
|---|---|---|
| **Agente de build** (BIM-IFC / código) | Produce código y cálculos. | Aprobar su salida; tocar valores esperados o tolerancias. |
| **Agente de QA** (run separado, su oráculo) | Ejecuta las 3 capas; emite el *Informe de QA por cálculo*. | Arreglar el código (solo lo juzga y lo devuelve). |
| **JM (firma)** | Cierra el gate; acepta tolerancias; firma la certificación. | Delegar la firma en la IA. |

La IA prepara la evidencia; la **responsabilidad sigue siendo de un ingeniero humano**.

### B.5. Reglas anti-gaming y certificación

- Golden y tolerancias en **zona protegida**; cambiarlas exige **PR aprobado por JM**, con traza.
- Un fallo de QA **no** se resuelve aflojando la tolerancia ni editando el valor esperado — **solo arreglando el código**.
- Todo caso golden nuevo registra la **procedencia de su oráculo** (analítico / segundo código / MMS / mano firmada por JM).
- **Certificación de dos llaves:** un resultado es «certificado» solo si (a) golden verde, (b) Informe de QA limpio y (c) **firma de JM** registrada. Es el peldaño **N4** (trazable) hecho operativo.

---

## C. Cómo encajan (ciclo de vida de un cambio)

Un agente modifica un módulo → lo integra (**CI**) → se recalculan los **casos golden** comparándolos por **espejo** contra el **oráculo** (la **QA**) → si hay **regresión**, el **gate** técnico la bloquea → si todo verde, **CD** publica una versión con número **SemVer** que indica si toca un **contrato** (MAJOR) → Estructurando (**productor**) publica; 2.0 (**consumidor**) decide cuándo subir su **pin** en el **lockfile** → cuando toda la suite está verde y **JM firma**, se abre el **gate de fase**.

---

## D. Decisiones (estado)

| # | Decisión | Estado |
|---|---|---|
| 1 | Golden y contratos en zona «contratos + golden» dentro de 2.0, propiedad de QA/JM, atados a la versión de contrato (golden vN valida contrato vN). | **Ratificado** |
| 2 | Oráculo: PyNite por defecto; jerarquía de espejos (analítico / 2.º código / MMS) a resolver caso a caso donde PyNite no llegue. | **Abierto** (se resuelve en su momento) |
| 3 | Solo JM cambia tolerancias y valores golden, vía PR. | **Ratificado** |

---

## E. Glosario

- **QA (aseguramiento de la calidad).** Sistema para demostrar, de forma repetible, que un resultado es correcto antes de usarlo o entregarlo.
- **Caso golden.** Caso de prueba cuya respuesta correcta se conoce y se congela como patrón de referencia (la «pieza calibrada»).
- **Espejo.** Calcular el mismo problema por dos caminos independientes y comprobar que coinciden (doble cálculo).
- **Oráculo.** La fuente de verdad contra la que se compara (solución analítica, segundo código FEM, MMS, mano firmada).
- **Gate (puerta).** Punto de control que bloquea el avance si no se cumplen las condiciones (punto de parada obligatorio).
- **Regresión.** Un cambio que rompe, sin querer, algo que antes funcionaba; la suite golden existe para cazarlas.
- **SemVer.** Numeración `MAJOR.MINOR.PATCH` que indica cuánto afecta un cambio.
- **Contrato.** Acuerdo de interfaz entre dos piezas (qué entra/sale), independiente de la implementación interna (los C1, C4, C5…).
- **Pin / lockfile.** Fijar la versión exacta de cada dependencia, por escrito, para que el resultado sea reproducible.
- **Productor / consumidor.** Estructurando publica versiones; Estructurando 2.0 las consume ancladas.
- **CI/CD.** Integración Continua (comprobar en cada cambio, automático) / Entrega Continua (publicar versión lista tras pasar la QA).
- **MMS (soluciones manufacturadas).** Elegir un campo exacto, deducir las cargas que lo producen y comprobar que el motor lo recupera; verifica cualquier formulación sin solución analítica.
- **Patch test.** Comprobación de que un parche de elementos reproduce exacto un estado de deformación constante.

---

*Referencias internas: roadmap de industrialización (N0→N5), `Backlog_Fase0_operativo.xlsx`. Este documento se actualiza cuando se cierre el punto 2 o cambie un contrato.*

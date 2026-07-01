# INICIO de hilo — P2: Predim Estructuras (cebo, contrato C5)

> Pega este texto al abrir el hilo supervisor de P2. Es autocontenido. Trabaja sobre `Documents\Claude\Projects` (ecosistema Aqyra). Gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md`. **Depende de P1 (Visor).**

## Texto de arranque (copiar al abrir el hilo)

> "Actúa como ingeniero de software del **Predimensionado de Estructuras de Aqyra**, bajo supervisión de JM. Tu trabajo es **aflorar el motor de cálculo (contrato C5, ya FIRMADO) dentro del visor como predimensionado GRATIS** — cebo, marcado `proposal`, **sin export firmable**. Lo que separa el predim (gratis) de la memoria de cálculo (de pago) **no es el motor, es la doble puerta del muro** (pago + certificación): aquí no se cruza. *Definition of done*: golden verde (coincide con la golden de su familia DEC-* dentro de tolerancia) + firma de JM. El motor vive en `Estructurando` (`motor-fem`/`motor-calculo`); la superficie, en el visor de P1. Material: `contratos-golden/contratos/C5_motor-fem.md`, las fichas `contratos-golden/golden/DEC-*.md`, `Aqyra-Raiz/PANEL_Ahora-cebo.md`."

## Rol y contexto

Ingeniero de software del ecosistema **Aqyra** (AEC, OpenBIM), gobierno de dos llaves. Este hilo **supervisa un solo proyecto**: el Predim Estructuras, que es **cebo** — cubre la carencia del autónomo en estructuras sin que pague, alimenta el dato y la confianza, y prepara la conversión al anzuelo (la memoria de cálculo firmable, que NO es parte de este hilo).

## Objetivo de ESTE hilo

Aflorar el motor C5 en el visor como **predimensionado de estructuras gratuito**:

- el usuario ve dominio de análisis, apoyos, cargas y un **predimensionado propuesto** (`proposal`), sin export firmable;
- usa el motor **a baja fidelidad / en modo predim**, reutilizando las familias ya validadas de C5 v0 (barra/celosía, lámina, modal, EC2/EC3/EC5/EC7);
- el salto a la memoria de cálculo firmable queda **explícitamente fuera** (es anzuelo: doble puerta de pago + certificación).

## Dónde vive el código

- **Motor (C5):** `Estructurando` — `motor-fem` (solver, release 0.1.0 anclado / build 0.3.0) y `motor-calculo-estructural` (agente orquestador, build 0.23.0). **C5 v0 está FIRMADO** (golden 7/7 verde + firma GPG de JM, 2026-06-26).
- **Superficie:** dentro del visor de **P1** (`Entorno/publico/visor`).
- **Anclaje:** `Entorno/integracion/versions.lock` (motor-fem 0.1.0, estructuras 0.1.0).

## Contrato y golden (las dos llaves)

- **Contrato:** **C5** (motor-fem), ya firmado — no hay que construir el motor, hay que **aflorarlo en modo predim**. Ver `C5_motor-fem.md` (entrada como `proposal`, salida O1–O4: deformada, esfuerzos, modal, aprovechamientos).
- **Llave 1 (golden):** el predim **coincide con la golden de su familia (DEC-*) dentro de tolerancia**, marcado `proposal`, **sin export firmable**. Reutilizar las fichas `DEC-*` como referencia.
- **Llave 2:** firma de JM para liberar versión.

## Dependencias

- **Aguas arriba:** **P1 Visor** (necesita la superficie donde aflorar) y **C5** (ya listo y firmado).
- **Aguas abajo:** prepara —pero no implementa— el anzuelo (memoria de cálculo firmable, horizonte Siguiente del roadmap).

## Decisiones que solo cierra JM

- **Fidelidad del predim** y qué familias entran en v0 (¿barra + lámina? ¿modal?).
- **Cómo se marca `proposal`** y cómo se comunica al usuario que es predimensionado a revisar/firmar por técnico competente.
- **Dónde cae exactamente la frontera** predim-gratis / cálculo-firmable (qué se ve en pantalla gratis vs qué exige cruzar el muro).

## Reglas (no romper)

- **Predim es cebo:** `proposal`, sin export firmable, sin medidor visible. El muro (pago + certificación) vive en el anzuelo, no aquí.
- Todo es predimensionado **a revisar y firmar por técnico competente**; Anejo Nacional España, NDP marcados `[confirmar AN]`.
- Un fallo no se arregla aflojando tolerancia — solo corrigiendo el código. Solo JM toca valores/tolerancias golden.
- El consumidor ancla versión de C5 y adopta solo si verde.

## Primer paso propuesto

1. Leer `C5_motor-fem.md` y las fichas `DEC-*` (las 7 golden verdes de C5 v0).
2. Coordinar con **P1** la superficie del visor donde aflora el predim.
3. Definir el **golden de predim** (qué caso, qué tolerancia, marca `proposal`, sin export) y pasarlo a JM.
4. Implementar el afloramiento del motor en modo predim sobre la familia más barata y visible.

# Inicio de hilo — Estrategia del ecosistema: evolución del cebo y del anzuelo

> **Texto de arranque** del hilo estratégico de Aqyra-Raiz. Se abre tras cerrar el diseño de N1.1
> (gobierno/piloto). Este hilo es el **plano hacia delante**: hacia dónde va el producto, no cómo se ordena
> lo que existía. Arranca con un **brainstorm** (interlocutor crítico) y desemboca en un **roadmap** con
> horizontes **Ahora / Siguiente / Después**.

## Texto de arranque (copiar al abrir el hilo)

> "Planificar estratégicamente la evolución del ecosistema Aqyra: cómo evoluciona el **cebo** (visor +
> OpenBIM) y cómo evoluciona el **anzuelo** (motor de cálculo) en funcionalidades futuras. Empezar con un
> **brainstorm** como interlocutor crítico y converger en un **roadmap** (pistas cebo/anzuelo × horizontes
> Ahora/Siguiente/Después, cada ítem atado a la versión de contrato que toca). Retomar desde la tensión del
> embudo planteada en `INICIO-hilo_estrategia_cebo-anzuelo.md`."
> Material: `Aqyra-Raiz/MAPA_ECOSISTEMA.md`, `Aqyra-Raiz/N1.1_es_el_piloto_del_gobierno.md`,
> `Estructurando 2.0/contratos-golden/`, `Estructurando 2.0/producto-wedge/`.

## Principio rector (no mezclar planos)

Aqyra-Raiz tiene **tres planos** que no hay que confundir:
- **Consolidación** (hacia atrás) — `PLAN_CONSOLIDACION.md`, los 6 Focos. Ordenar lo que existía. Casi cerrado.
- **Gobierno / piloto** (los raíles) — N1.1, contratos C1–C8, sello de dos llaves. El cómo se entrega cada paso.
- **Estrategia** (hacia delante) — ESTE hilo. Hacia dónde va el producto.

> **Enganche clave:** la estrategia se escribe en el **idioma del gobierno**. Cada funcionalidad futura se
> entrega como una **evolución de contrato/versión** bajo el sello de dos llaves (bump → golden → adoptar si
> verde). El roadmap es, por tanto, una secuencia de versiones de contrato con su golden, no una lista de deseos.
> Este hilo **no depende** de la ejecución de N1.1 (PyNite/tag): corre en paralelo.

## El eje cebo / anzuelo (disciplina del roadmap)

Cada ítem del roadmap debe responder: ¿ensancha el embudo (cebo) o profundiza el foso (anzuelo)? ¿y preserva
el salto abierto→valor (la frontera C5)?

- **Cebo — visor + OpenBIM.** Trabajo: *ensanchar el embudo* (adopción, baja fricción, confianza, datos que
  entran). Debe seguir siendo genuinamente abierto y útil aunque no se pague. Eje de evolución: ver IFC →
  navegar/propiedades (V1) → BCF/IDS/incidencias → write-back de propuestas → integración CDE.
- **Anzuelo — motor de cálculo.** Trabajo: *profundizar el foso* (defensibilidad, valor que se firma/cobra).
  Eje: familias C5 v0 (barra, lámina, modal, EC2/3/5/7) → más tipologías (puentes, obras lineales,
  instalaciones, ya empaquetadas) → sismo (el 5c diferido) → memoria automática → certificación.

## Dónde retomar: la tensión del embudo (punto vivo del brainstorm)

Todo se juega en el **salto**, no en las dos puntas. Grieta a mirar de frente: **¿el cebo y el anzuelo son
para la misma persona?** En AEC el que abre/navega el IFC suele ser el coordinador BIM / arquitecto /
constructor; el que necesita el cálculo firmado es el ingeniero de estructuras. Son peces distintos: si el
visor pesca coordinadores pero el motor sirve a estructuristas, el embudo tiene una fuga estructural.

Tres salidas, cada una manda un roadmap distinto:

1. **Mismo usuario, doble necesidad** — el estructurista también quiere el visor abierto; el cebo se diseña
   *para el calculista* (ve dominio de análisis, apoyos, cargas), no para el coordinador.
2. **Usuarios distintos, el cebo crea el pull** — el coordinador entra, y desde el visor *nace/encarga* el
   cálculo; el visor es el sitio donde aparece la petición y arrastra al estructurista a la plataforma.
3. **El cebo no es el visor, es el OpenBIM** — el gancho real no es "ver", es que tus datos viven en formato
   abierto y diff-able (no presos de Revit/Tekla). El anzuelo: "y además calculo sobre esos mismos datos
   abiertos, sin reimportar".

**Posición inicial de la IA (para reaccionar):** la nº3 parece la más defensible; la nº1 la más rentable a
corto; la nº2 es probablemente una trampa (depende de un comportamiento de "encargo" que no controlas).
**Pregunta de encuadre pendiente:** ¿cuál es la *tesis de conversión* — qué hace que quien entra por el visor
acabe necesitando el motor? Empezar el hilo respondiendo a esto.

## Cómo correr el hilo

1. **Brainstorm** (sparring, no informe): resolver la tensión del embudo y la tesis de conversión.
2. **Converger** en 2–3 direcciones fuertes por pista (cebo / anzuelo).
3. **Roadmap** `ROADMAP_cebo-anzuelo.md` en Aqyra-Raiz: dos pistas × Ahora/Siguiente/Después, cada ítem con
   su contrato (C1/C4/C5…) y su golden previsto.
4. Opcional: one-pager o research plan de la asunción más arriesgada.

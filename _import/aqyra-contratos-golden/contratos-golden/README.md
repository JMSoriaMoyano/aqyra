# contratos-golden/ — zona protegida (propiedad QA/JM)

Decisión **(1) ratificada**: los contratos y los casos golden viven aquí, atados a la versión de contrato (**golden vN valida contrato vN**).

## Registro único de contratos (reconciliación firmada por JM, 2026-06-27)

Este índice es el **registro de la verdad**. Dos familias: **interfaces C1–C8** (enchufes entre piezas) y **convenciones de núcleo CN-*** (transversales, no son interfaces). Un fichero canónico por contrato; las copias quedan como punteros.

| Nº | Contrato | Fichero canónico | Estado |
|---|---|---|---|
| **C1** | Parser / IFC / modelo neutro | `Estructurando/Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` | Firmado |
| **C2** | Datos (crudo ↔ aprendido) | `contratos/C2_datos.md` | Borrador |
| **C3** | *Reservado (libre)* | — | Libre |
| **C4** | Red | *(pendiente de redactar)* | Referenciado |
| **C5** | Motor-fem (interfaz) | `contratos/C5_motor-fem.md` | **Firmado** |
| **C6** | Corpus golden / recuperación | carpeta `golden/` | Propuesto |
| **C7** | Operador IA | `contratos/C7_operador-ia.md` | Borrador |
| **C8** | Intercambio CDE | `contratos/C8_intercambio_CDE.md` | Borrador |
| **CN-1** | Memoria del despacho (era C2 heredado) | `Estructurando/Nucleo-transversal/CN-1_Convencion-memoria-despacho.md` | Vigente |
| **CN-2** | Entregables / documentación (era C3 heredado) | `Estructurando/Nucleo-transversal/CN-2_Convencion-entregables-documentacion.md` | Vigente |
| **CN-3** | Acciones / bases de cálculo / demanda (era rotulada «C4») | `Estructurando/Nucleo-transversal/CN-3_Convencion-acciones-bases-de-calculo.md` | Vigente |

> **C4 = red** queda como **interfaz** (grafo de red nodos/tramos), aún **sin documento de contrato** (pendiente de redactar). La convención de entrada «acciones/bases de cálculo/demanda» que antes se rotulaba «C4» es ahora **CN-3** (barrido de referencias en disciplinas ejecutado 2026-06-27). La spec de ingeniería del motor `Nucleo-transversal/C5_Contrato-motor-FEM.md` se conserva activa; verificar divergencia con la interfaz canónica C5 (tarea del hilo motor-fem).

## Reglas

- **Solo JM** cambia valores golden o tolerancias, **vía PR** con traza (decisión 3).
- Un fallo de QA **no** se resuelve aflojando tolerancia ni editando el valor esperado — solo arreglando el código.
- Todo caso golden registra la **procedencia de su oráculo**: analítico / segundo código FEM / MMS / mano firmada por JM (ver Gobierno §B.3).

## Estructura

```
contratos/   · especificaciones de interfaz C1, C4, C5... versionadas (SemVer)
golden/      · casos patrón con: entrada · salida esperada · oráculo · tolerancia · responsable
```

## Ficha mínima de un caso golden

```
id:           PUE-xx / LIN-xx / ...
contrato:     C5 vN
entrada:      <parámetros>
esperado:     <valores de referencia>
oraculo:      analitico | pynite | mms | mano-JM   (+ fuente)
tolerancia:   <por magnitud>
responsable:  JM
```

- 2026-06-28 - Golden **C1-APERTURA-01** registrada (C1 apertura familias P1, iso19650-openbim 0.10.0): Llave 1 VERDE + firma JM.

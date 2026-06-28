# Puente cebo → C1 (Inc 3) y fixtures golden

Decisión JM (P1·B·2): **híbrido**. El cebo dibuja el preview al vuelo (web-ifc); el IFC
**autoritativo** —el que será el Maestro y pasa por auditoría— lo compila **C1**
(`iso19650-openbim/narracion-a-ifc`) desde su *spec de alto nivel* (`<m>.alto.json`).

## Flujo

```
modelo del cebo  --toAltoSpec()-->  alto.json  --[C1] compilar_spec.py + spec_to_ifc.py-->  IFC4X3 autoritativo
   (preview vivo)      (handoff)                  (geometría real + Psets + bsDD)              --> Visor / auditoría
```

- **Costura:** `demo/src/c1-bridge.ts` → `toAltoSpec(model, {ancho, largo, altura})` produce
  el `alto.json` (determinista). En la consola del navegador: `aqyraToC1()` lo devuelve.
- **C1 ya tiene** los primitivos `niveles`, `edificios`, `rampas`, `escaleras`, `muros`,
  `losas`, `elementos` (ver `narracion-a-ifc/SKILL.md`). El cebo rellena `niveles` (plantas
  + altura) y `edificios` (la caja: ancho × fondo, muros perimetrales + forjados).

## Lo que falta en C1 = FRONTERA (la firma JM)

El cebo modela **IfcSpace** (habitaciones, plazas, pasillos, núcleos) con su footprint, zona
y URI bsDD. El `alto.json` de C1 **aún no tiene un primitivo `espacios`**. Por eso el puente
emite un array `espacios[]` (ver `AltoEspacio` en `c1-bridge.ts`) que C1 debe **adoptar**:

```jsonc
"espacios": [
  { "nombre": "AQ-ESP-PLA-P00-F1-01", "nivel": "Planta baja", "clase": "IfcSpace",
    "objectType": "PlazaAparcamiento", "zona": "aparcamiento",
    "contorno": [[0,4.5],[2.5,4.5],[2.5,9.5],[0,9.5]],
    "uri_bsdd": "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/IfcSpace" } ]
```

Añadir `espacios` a `compilar_spec.py`/`spec_to_ifc.py` es un **cambio en la frontera de C1**:
→ **bump → golden → adoptar si verde → anclar en `versions.lock`**. La IA preparó el adaptador
y el contrato; el cruce de frontera (tocar C1 + golden) lo corre y firma JM. Regla CEBO: el
cebo NO escribe IFC firmable; produce el handoff, C1 produce el IFC.

## Caso → fixture golden (anti-regresión)

`demo/src/fixture.ts` congela un caso: su entrada (`BuildingInput` + `ctx`) + un **snapshot
determinista** del modelo (cuentas por objectType, zonas, totales, códigos de muestra).

- En el navegador: `aqyraFixture("nombre")` → JSON del caso actual → guardar en
  `demo/fixtures/<nombre>.json` (hay un ejemplo: `parking-120x24-2filas.json`).
- Golden (propuesto, `outputs/fixtures.proposed.test.ts` → mover a `demo/test/`): replica cada
  fixture con `checkFixture` y exige que el snapshot no cambie. Si afinas un generador y rompes
  un caso ya validado, el golden lo caza. Así la capacidad acumulada **nunca regresiona**.

# servicio-calculo — el puente motor↔pantalla (anzuelo · D-019·C.4)

Envuelve el pipeline privado (**produce → QA → EC3 → firma**) en endpoints HTTP
**locales** que el **post-proceso** del visor llama por `fetch`. El visor (cebo)
sigue **sin servidor para VER**; solo el post llama aquí. El cálculo, la QA, el
criterio EC y la firma —el foso— viven en este servicio, no en el cebo.

Es un servidor de la **librería estándar** (`http.server`): sin dependencias
propias. El cálculo lo aportan los paquetes hermanos (`puente-calculo`, `qa-pynite`,
`verificacion-ec`, `firma`), anclados por `PYTHONPATH` (ver `INICIAR_SERVICIO_CALCULO.bat`).

## Endpoints (una transición de llave por endpoint, D-021/D-023)

`POST /solve` — modelo C5 → grupos **`computed`** (0 llaves) con aprovechamiento
EC3 ya relleno (el visor pinta deformada + «qué no cumple» de inmediato).
`POST /qa` — gate de equilibrio + re-cálculo + reconciliación → **`qa-passed`**
(1.ª llave) o **bloqueo** (`qa-fail`, discrepancia expuesta; no se eleva nada).
`POST /sign` — firma de JM → **`verified-signed`** (2.ª llave). Exige `qa-passed`
(si no, **409**). Falta `signer` → **400** (la IA no firma).
`POST /ec3` — recomprueba aprovechamiento + «qué no cumple» sobre un grupo dado.
`GET /health` — vivo + si PyNite está disponible + meta de gobierno.

El **verde** (`verified-signed`) **solo** lo acuña `/sign`. Ningún otro endpoint lo
devuelve. Es la regla inviolable de V3.

## Productor: PyNite **provisional** (decisión del hilo V3-CONEXIÓN)

`/solve` delega en un **productor inyectable** (`producer.py`). Por defecto es
**PyNite** (`pynite_producer`): números reales **ya**, para reproducir los casos de
Estructurando. Salvedad de gobierno: mientras productor y QA sean el **mismo** motor
(PyNite), la 2.ª llave **no es independiente** (el *gate de equilibrio* sí es
significativo). El servicio lo marca explícito en `meta` (`provisional: true`,
`independent: false`, `warning`). La independencia real (D-023) llega al cablear
**motor-fem**: cambiar **solo** `default_producer` a `motorfem_producer` (punto único).

## Arrancar y probar

- Arrancar:  doble clic en **`INICIAR_SERVICIO_CALCULO.bat`** (raíz del repo).
- Probar:    **`VERIFICAR_SERVICIO.bat`** → 12 tests (no requieren PyNite; usan
  productor/solver falsos). Cubren: estados de las dos llaves, EC3 «qué no cumple»,
  guarda de firma (409/400), meta provisional/independiente y el servidor HTTP.

## Frontera cebo/anzuelo

Público (cebo): el **cliente** `fetch` (`publico/demo/src/calc-service.ts`) — un
POST tonto. Privado (anzuelo): **todo** lo de aquí. Si filtrarlo erosiona el foso,
es privado: el criterio EC, la reconciliación QA y la firma lo son.

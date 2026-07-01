# Hilo V3-CONEXIÓN — estado tras el primer corte (motor↔pantalla)

**Decisión de JM (este hilo):** productor **PyNite provisional** + construir el
servicio y cablear el visor **ya** (sin esperar a conectar `Estructurando`).

## Qué se ha construido

**Servicio de cálculo privado** — `privado/servicio-calculo/` (anzuelo · D-019·C.4).
Servidor de la **librería estándar** (`http.server`, sin dependencias propias) que
envuelve el pipeline existente en endpoints HTTP locales:

- `POST /solve` → grupos **`computed`** con aprovechamiento EC3 ya relleno.
- `POST /qa` → **`qa-passed`** (1.ª llave) o **bloqueo** `qa-fail` (discrepancia expuesta).
- `POST /sign` → **`verified-signed`** (2.ª llave, firma de JM); exige `qa-passed` (409 si no), exige `signer` (400 si falta).
- `POST /ec3` → recomprueba aprovechamiento + «qué no cumple».
- `GET /health` → vivo + PyNite disponible + meta de gobierno.

El **productor** de `/solve` es **inyectable** (`producer.py`): por defecto PyNite
(`pynite_producer`); el swap a `motor-fem` es **un único punto** (`default_producer`
→ `motorfem_producer`). El servicio marca en `meta`: `provisional: true`,
`independent: false`, `warning` (la 2.ª llave **no** es independiente mientras
productor y QA sean PyNite; el gate de equilibrio sí es significativo).

**Cliente público** — `publico/demo/src/calc-service.ts` (cebo): cliente `fetch`
"tonto" (POST + JSON) tipado contra el contrato. El visor sigue **sin servidor para
VER**; solo el post-proceso llama.

**Skin cableada** — `publico/demo/src/calculista.ts`: deja de fabricar el
`ResultGroup` ilustrativo. «deformada/post-proceso» → `/solve` (real); botón
**"Pasar QA"** → `/qa`; botón **"Firmar (JM)"** → `/sign`. Si el servicio no está
arrancado, **fallback a DEMO** con aviso claro. `element.showResultGroup` pinta
igual; solo cambia el origen de los datos.

## Verificación

- **Servicio (Python): 12/12 tests verdes** en sandbox, con productor/solver falsos
  (no requieren PyNite). Cubren la máquina de las dos llaves, EC3 «qué no cumple»,
  guarda de firma (409/400), meta provisional/independiente y el servidor HTTP
  (health, CORS, 404). Reproducible en Windows con **`VERIFICAR_SERVICIO.bat`**.
- **Arranque:** **`INICIAR_SERVICIO_CALCULO.bat`** (instala PyNite la 1.ª vez, ancla
  los paquetes por `PYTHONPATH`, sirve en `127.0.0.1:8765`).

## Pendiente (la IA propone; JM decide/sella)

1. **Re-sellar TS en Windows** (`RESELLAR.bat` / `pnpm typecheck && pnpm test` en
   `publico/`): los cambios de `calculista.ts` + el nuevo `calc-service.ts` se han
   escrito en el FS real, pero **no** se han typecheckeado aquí (el sandbox no corre
   el toolchain y su mount sirve copias *stale* de los `.ts`). Si el typecheck falla,
   avísame y lo corrijo.
2. **Conectar `Estructurando`** para el **paso 4**: reproducir los casos de uso uno a
   uno desde la pantalla y **comparar con el golden**. Hoy no está conectada.
3. **Cablear motor-fem** (independencia real de la 2.ª llave, D-023): swap único en
   `producer.default_producer` + confirmar entrypoint y convenio de signo
   (`axial_tension_positive`) — ver `puente-calculo/MOTOR_FEM_BINDING.md`.
4. **Verificar end-to-end con PyNite real en Windows** (arrancar el servicio y
   ejercitar `/solve→/qa→/sign` desde el visor sobre un IFC con estructura).

## Frontera cebo/anzuelo (intacta)

Cebo (público): visor + cliente `fetch`. Anzuelo (privado): cálculo, reconciliación
QA, criterio EC y firma (el servicio). El verde **solo** lo acuña `/sign`.

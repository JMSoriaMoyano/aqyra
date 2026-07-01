# Aqyra · V3 — Hilo de CONEXIÓN (motor real → pantalla) y validación de casos de uso

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como **primer mensaje** del nuevo hilo (proyecto Cowork *Aqyra/Entorno*). Es autocontenido. La espina de V3 (pasos 1–5) ya está implementada; este hilo **conecta el cálculo real a la pantalla** y **reproduce los casos de uso de Estructurando uno a uno**, mejorando la experiencia con JM sobre la marcha.

---

## 0. Quién eres y objetivo

Eres el equipo de producto e ingeniería de **Aqyra** (visor OpenBIM asistido por IA; el "cebo"): Producto, frontend (web-ifc/That Open + Three.js), integración OpenBIM y la superficie del copiloto NL. **JM** dirige y **firma**; la IA opera y **no firma ni certifica**.

**Misión de este hilo:** **conectar el motor que da los números reales con la pantalla** —hoy el visor pinta el post-proceso con datos *ilustrativos*— y, una vez conectado, **JM reproduce desde la pantalla, uno a uno, los casos de uso creados en la carpeta `Estructurando`**, validando resultado y **estado de dato**, mientras IA+JM **corrigen y mejoran la experiencia de usuario** en cada iteración. La IA prepara la evidencia; **JM decide y firma**.

## 1. Estado a día de hoy (de dónde vienes)

- **V3 — espina completa (pasos 1–5) implementada y verificada:**
  - **Público (`publico/`, el cebo):** contrato C5 con tipos de entrada (releases D-020, sección/material numéricos, `combination.terms`, `surface.areaLoad`) y de **resultado** (`ResultGroup`/`MemberResult`/`NodeResult`/`SurfaceResult`); **estado de dato** de 4 valores (`proposal`/`computed`/`qa-passed`/`verified-signed`, D-021) con **chip + marca de agua** (ya **atenuada**, poco protagonismo) y **guarda de exportación**; **render** `viewer.setDeformed` + `element.showResultGroup` (deformada + color por aprovechamiento). Skin Calculista con comandos NL y el flujo de estado caminable.
  - **Privado (`privado/`, el anzuelo):** `puente-calculo/` (adaptador C5: traducción rol→motor, signos D-018, releases, gravedad −Z, combinaciones, carga por área; **ensamblado/parseo del binding listo**, `MotorFemBinding` cableado hasta el borde de la llamada — ver `MOTOR_FEM_BINDING.md`); `qa-pynite/` (QA **independiente** con PyNite: equilibrio + reconciliación → `qa-passed`, D-023); `verificacion-ec/` (aprovechamiento **EC3** §6.2 + «qué no cumple», D-022); `firma/` (única fuente de `verified-signed`).
  - **Verde:** typecheck + **62/62 tests TS** en Windows; suites Python (adapter, QA con PyNite real, EC3, pipeline `computed→qa-passed→verified-signed`) verdes en sandbox.
- **Lo que aún NO está conectado (el motivo de este hilo):**
  1. **No hay servicio de cálculo** que el visor pueda llamar: el pipeline privado existe como funciones Python, no como endpoint.
  2. El visor pinta el post-proceso con un **`ResultGroup` ilustrativo** (la skin lo fabrica); no consume números reales.
  3. **`MotorFemBinding.solve` no apunta a un motor real** (`motor-fem 0.1.0` vive en `Estructurando`, no vendorizado aquí).

## 2. Antes de tocar nada

- **Conecta la carpeta `Estructurando`** a la sesión (hoy solo está `Entorno`): ahí viven `motor-fem 0.1.0`, su API, y **los casos de uso/golden** que JM quiere reproducir. Si no se puede conectar, pide a JM los IFC de los casos y sus resultados esperados.
- Lee los README de `publico/`, `privado/` y de cada paquete privado (`puente-calculo`, `qa-pynite`, `verificacion-ec`, `firma`), más **`MOTOR_FEM_BINDING.md`** (contrato petición/respuesta del binding), **`COMO_PROBAR_V3.md`**, `HILO-V3_spec.md` y `DECISIONES.md` (D-018…D-023).
- **Verifica el entorno:** TS con `pnpm typecheck && pnpm test` en Windows (el sandbox Linux **no** corre el toolchain real: su mount sirve copias cacheadas de los ficheros modificados). Python privado: `VERIFICAR_CALCULO.bat`.

## 3. Qué implementar (orden)

1. **Servicio de cálculo privado (D-019·C.4).** Envolver el pipeline en un endpoint HTTP **local** (p. ej. FastAPI/Flask en `privado/`), que reciba el `StructuralModel` serializado del visor y devuelva el esquema de resultados:
   - `POST /solve` → motor → `ResultGroup` **`computed`**.
   - `POST /qa` → QA PyNite (equilibrio + reconciliación) → `qa-passed` o `qa-fail` con discrepancia.
   - `POST /sign` → firma de JM → `verified-signed` (exige `qa-passed`).
   - `POST /ec3` (o integrado) → rellena aprovechamiento + «qué no cumple».
   El **visor sigue sin servidor para VER**; solo el **post** llama a este servicio (cebo intacto, anzuelo en el servicio).
2. **Cablear el motor real.** `MotorFemBinding.solve` → `motor-fem 0.1.0` de `Estructurando` (confirmar entrypoint y `axial_tension_positive`; el ensamblado/parseo ya está). **Decisión para JM:** mientras `motor-fem` no esté disponible/cableado, ¿usar **PyNite como productor provisional** para tener ya números reales en pantalla (con la salvedad de que la independencia de la 2.ª llave D-023 exige otro motor en producción), o esperar a `motor-fem`? *Recomendación: PyNite provisional para desbloquear la validación de casos; marcar claramente que la independencia real llega con motor-fem.*
3. **Conectar el visor.** La skin Calculista deja de fabricar el `ResultGroup` ilustrativo y **llama al servicio** (`fetch`): `solve` → pinta `computed`; botón "Pasar QA" → `qa`; botón "Firmar (JM)" → `sign`. `element.showResultGroup` ya pinta deformada + aprovechamiento + estado; solo cambia el origen de los datos (real, no demo).
4. **Reproducir los casos de uso de `Estructurando`, uno a uno, desde la pantalla.** Por cada caso: cargar su IFC, ver el **pre** (cargas/apoyos) y el **post** (deformada/aprovechamiento/«qué no cumple») con su **estado de dato**, y **comparar con el resultado golden** del caso. JM reproduce; IA+JM **corrigen e iteran la UX** (chip, colores, escala de deformada, textos, comandos NL, marca de agua).

## 4. Principios y frontera (no negociables)

- **Cebo/anzuelo:** el visor (ver/autorar) es público y **sin servidor**; el **cálculo, la QA, el criterio EC y la firma** son privados (servicio). Si filtrarlo erosiona el foso, es privado.
- **Dos llaves (D-021/D-023):** el visor **nunca** pinta como `verified-signed` lo no firmado; `qa-passed` (PyNite) + **firma de JM**. El verde solo lo acuña la firma.
- **Consumo anclado** del núcleo (`integracion/versions.lock`): `motor-fem 0.1.0` se consume, **no se bifurca**.
- **Formato abierto:** IFC entra/sale como texto; resultados al IFC como `IfcStructuralResultGroup` (write-back diff-able ya esbozado).

## 5. Bucle de experiencia de usuario (cómo trabajamos JM e IA)

JM reproduce cada caso **desde la pantalla** y señala lo que chirría o se puede mejorar; la IA lo corrige en caliente (el visor corre con recarga automática). Puntos de UX ya conocidos para vigilar: **marca de agua** (ya atenuada; ajustable o quitable dejando solo el chip), **escala de la deformada**, **rampa de colores** de aprovechamiento, **textos/carteles** de estado, y los **comandos en lenguaje natural** (hoy: «deformada», «esfuerzos», «aprovechamiento», «flecha», «momento», «cortante», «axil», «tensión», «combinación», «ELU», «qué no cumple», «post-proceso»; y «estado de dato»/«leyenda»/«dos llaves»).

## 6. Fuera de alcance de este hilo

- **Copiloto NL con criterio del corpus** (qué cargas/combinaciones tocan por norma) → **V4**.
- **Armado EC2** (elementos + núcleo) y **pandeo de barra EC3 §6.3** → incrementos posteriores (D-022·C.2.a).
- **Despliegue SaaS / cebo externo** → V5.

## 7. Definición de Hecho del hilo

Cada **caso de uso de `Estructurando`** se **reproduce desde la pantalla** con **números reales** del servicio de cálculo, mostrando deformada + aprovechamiento + «qué no cumple», **cada resultado con su estado de dato** correcto; el flujo `computed → qa-passed → verified-signed` operativo end-to-end (el verde solo con la firma de JM); el resultado **concuerda con el golden** del caso dentro de tolerancia; la **UX queda validada por JM** caso a caso; tests verdes y contrato sin romper.

## 8. Pendientes heredados (la IA propone; JM firma)

- Confirmar **entrypoint y convenio de signo** de `motor-fem 0.1.0` (binding listo salvo ese punto).
- **Sello de dos llaves del release N1.1** del núcleo en `versions.lock` (golden verde + tag GPG de JM) — condición para apoyarse en el motor en producción.
- Reparto **tributario geométrico fino** de la carga por área; **write-back nativo** de entidades `IfcStructuralResultGroup`.
- Re-sellar TS en Windows tras cada incremento.

---

*Continuidad preparada por la IA · proyecto Aqyra, paso de la espina de V3 a la conexión motor↔pantalla y validación de casos de uso de Estructurando · La IA opera; JM firma.*

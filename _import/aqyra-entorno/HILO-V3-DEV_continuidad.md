# Aqyra · V3 — Hilo de DESARROLLO (post-proceso bajo dos llaves: marco de decisiones firmado)

> **Cómo usar este texto:** copia todo lo que hay bajo la línea y pégalo como **primer mensaje** del hilo de desarrollo de V3 (proyecto Cowork *Aqyra*). Es autocontenido. Las seis decisiones de V3 (D-018 a D-023) ya están **firmadas**; aquí se **implementa**.

---

## 0. Quién eres y objetivo

Eres el equipo de producto e ingeniería de **Aqyra** (visor OpenBIM asistido por IA; el "cebo"): Producto, frontend (web-ifc/That Open + Three.js), integración OpenBIM y la superficie del copiloto NL. **JM** dirige y **firma**; la IA opera y **no firma ni certifica**.

Tu misión en este hilo: **implementar V3, el post-proceso estructural bajo dos llaves** — conectar el modelo analítico `proposal` de V2 con el motor de cálculo anclado y devolver **esfuerzos, deformada y aprovechamientos** pintados sobre el modelo, **con su estado de dato**, marcando `verified-signed` **solo** tras QA independiente + firma de JM. Es el lado "post" de Decopak HQ y lo que de verdad resuelve al **Calculista**.

**Empieza por la espina:** los **tipos públicos del contrato C5** (lo que desbloquea todo lo demás), no por el motor.

## 1. Estado a día de hoy (de dónde vienes)

- **V1 (visor) cerrado en F2** y **V2 (pre-proceso) implementado:** `StructuralModel` derivado del físico (barras por PCA, nudos por clustering, superficies, núcleos columna-cajón / 4 láminas cosidas), apoyos/cargas/casos/combinaciones **autorados** (`proposal`), write-back diff-able por *append* STEP. Contrato `pre` cableado (`@aqyra/embed`). Skin **Calculista** (`demo/calculista.html`) con barra de comandos NL (stub de reglas). **38 tests** (con la salvedad de §9: re-sellar en Windows los añadidos tras los 38 verdes).
- **Marco de decisiones de V3 FIRMADO por JM (2026-06-25)** en `DECISIONES.md` — **D-018 a D-023** (ver §4). Cada una con su documento de evidencia `HILO-V3_para-firma_*.md` y la spec maestra `HILO-V3_spec.md`.
- **Contrato y tipos de V2** en `publico/openbim/src/index.ts` (`StructuralModel`, `StructuralMember`, `SectionRef`, `Support`, `Load`, `LoadCase`, `Combination`, `StructuralSurface`, `StructuralCore`…), re-exportados en `publico/embed/src/contract.ts` (con `DataState = "proposal" | "verified-signed"` reservado desde V1).
- **`privado/` es cáscara** (solo `README`): `puente-calculo/` se construye nuevo. **`motor-fem 0.1.0`** anclado en `integracion/versions.lock` (consumir, no bifurcar).

## 2. Antes de tocar nada

Lee los README de las carpetas implicadas (`publico/`, `privado/`, `integracion/`), la spec **`HILO-V3_spec.md`**, los seis **`HILO-V3_para-firma_*.md`** (D-018…D-023) y **`DECISIONES.md`** (D-018 a D-023). **Verifica el entorno:** `cd publico && pnpm install && pnpm typecheck && pnpm test` (deben seguir verdes; re-sella los tests pendientes de §9).

## 3. Qué implementar (orden; del §8 de la spec)

1. **Tipos públicos del contrato C5** (`publico/`, D-019) — *el arranque*:
   - **Entrada:** extender `StructuralMember` con `releases?` (6 GdL/extremo i,j, true=liberado, ejes por rol — D-020); añadir **propiedades numéricas** de sección (`{ A, I_strong, I_weak, J, … }`) y material (`{ E, G, density, fy_or_fck }`) resueltas en el lado Aqyra (D-019·C.1.a); `combination.terms` como mapa `{ caso: factor }` (D-019·C.2.a, conservando `expression` solo para mostrar); `surface.areaLoad?` (D-019·C.3.a).
   - **Salida:** definir los **tipos de resultado** — `ResultGroup` (por combinación, `state: DataState`), `MemberResult` (N/V/M/T por x i→j, deformada local, aprovechamiento; signos D-018, N>0 tracción), `NodeResult` (desplazamientos + reacciones), `SurfaceResult` (membrana/placa), envolventes con combinación gobernante.
   - **Estado:** ampliar `DataState` con `computed` y `qa-passed` (D-021); `PreDataState` espeja.
   - **Corrección D-018:** cambiar el *default* de carga gravitatoria de `direction="y"`/−Y a **−Z global** en `PreAdapter`/`element.ts`/`calculista.ts`.
   - Bump **SemVer** de `@aqyra/embed`.
2. **Estado de dato en el visor** (`publico/`, D-021) — *en paralelo, no depende del motor:* chip de estado + marca de agua «NO VERIFICADO» + leyenda, con el tratamiento «certificado» (verde/limpio) **gated** a `state==="verified-signed"`; **guarda de exportación** (toda salida no firmada estampa la marca). Reutiliza el `warnBanner` persistente de la skin.
3. **Adaptador C5 + servicio de cálculo** (`privado/puente-calculo/`, D-019·C.4): serialización modelo→motor, **traducción rol→PyNite→EC** y de signos/releases (D-018/D-020), invocación del *solve* del `motor-fem` anclado, mapeo de resultados al esquema con estado; *write-back* al IFC como `IfcStructuralResultGroup`.
4. **QA PyNite** (`privado/`, D-023): re-cálculo **independiente** (PyNite ≠ núcleo de `motor-fem`) + **chequeo de equilibrio** (Σreacciones=Σacciones, gate previo) + reconciliación con tolerancias (equilibrio ~0,1 %; reacciones/desplazamientos ±2–5 %; esfuerzos/aprovechamientos ±5 %) → `qa-passed`; `qa-fail` **bloquea** y expone la discrepancia.
5. **Suelo de V3 / DoD** (D-022·C.1): sobre Decopak HQ, deformada bajo una combinación ELU + **aprovechamiento EC3** (acero) + «qué no cumple», cada resultado con su estado, bajo dos llaves. El **armado EC2** (elementos + núcleo por sándwich/columna-cajón) entra **después**, como incremento de V3 (D-022·C.2.a).

> **Frontera:** los **tipos** (entrada + resultados) y el render son **públicos** (`publico/`); el **adaptador, el servicio de cálculo, la QA y el armado** son **privados** (`privado/`). El motor se **consume anclado**, no se reescribe.

## 4. Decisiones firmadas que gobiernan la implementación (D-018…D-023)

- **D-018 · Signos y ejes.** Global **Z-up**, gravedad −Z; ejes locales por **rol** (`axis`/`strong`/`weak`) con mapeo explícito a PyNite (x/z/y) y Eurocódigo (x/y-y/z-z) — nunca pasar la letra cruda entre capas; **N>0 tracción**; V/M/T canónico PyNite; *releases* con polaridad invertida frente a `Restraints`.
- **D-019 · Contrato C5.** Forma de entrada (extendida) y de salida (resultados con `DataState`); props sección/material **en el lado Aqyra** (C.1.a); combinación como **mapa** (C.2.a); **carga por área** en C5 (C.3.a); **servicio de cálculo privado** (C.4) — el visor sigue sin-servidor para *ver*. SemVer, MAJOR = rotura.
- **D-020 · Uniones/releases.** Rígido por defecto; extremos liberables; **aspas (`brace`) biarticuladas por defecto** (C.b, excepción acotada); rótula = liberar los dos flectores; prohibido liberar axil/torsión en ambos extremos.
- **D-021 · Estado de dato.** 4 estados `proposal`/`computed`/`qa-passed`/`verified-signed` (≅ ISO 19650 S0/S0/S3/A); **regla binaria** (solo `verified-signed` = certificado); el verde **solo lo acuña la firma** (`privado/`); **guarda de exportación** (C.2 = sí).
- **D-022 · Alcance del armado.** Suelo de V3 = verificación + «qué no cumple» (cierra el DoD); **armado EC2 escalonado dentro de V3** (C.2.a). En hormigón, **verificar exige dimensionar**.
- **D-023 · QA PyNite (2.ª llave).** PyNite **independiente** de `motor-fem` produce `qa-passed`; equilibrio como gate previo (C.3); tolerancias propuestas (C.2); ante `qa-fail`, **bloqueo con anulación documentada** (C.4.a). Anclado en chequeo independiente **Cat 3** (BS 5975).

## 5. Principios y frontera (no negociables)

- **Formato abierto:** IFC entra/sale como texto; *write-back* diff-able; resultados al IFC como `IfcStructuralResultGroup`.
- **Web sin servidor para VER (D-002); servicio de cálculo privado para el POST (D-019·C.4).** El cebo (ver/autorar) sigue en el navegador; solo el cálculo llama al servicio (anzuelo).
- **Dos llaves (D-021/D-023):** el visor **nunca** pinta como `verified-signed` lo no firmado; `qa-passed` (1.ª llave, PyNite) + firma de JM (2.ª llave). La IA prepara la evidencia; **JM firma**.
- **Cebo/anzuelo:** mecánica (tipos, render, estado) = `publico/`; criterio, motor, QA, armado = `privado/`. El **criterio normativo** (qué combinaciones/detalle por norma) sigue siendo anzuelo → **V4**.
- **Consumo anclado** del núcleo (`versions.lock`); no bifurcar.

## 6. Fuera de alcance de V3

Copiloto NL con criterio del corpus → **V4**. BCF/IDS → V1·F3/F4. Sísmica (espectro/ductilidad EC8) → gancho diferido. Despliegue SaaS / cebo externo → V5.

## 7. Definición de Hecho

Sobre **Decopak HQ**: cargar el IFC, ver la **deformada** bajo una combinación ELU, **colorear por aprovechamiento EC3** y listar los **elementos al límite**, cada resultado con su **estado de dato** visible; el flujo `computed → qa-passed → verified-signed` operativo (la firma vira a verde, no antes); todo el render en `publico/`, el cálculo/QA en `privado/`; **tests verdes**; contrato extendido sin romper (bump SemVer al cerrar). El **armado EC2** (elementos + núcleo) es el **incremento** posterior dentro de V3.

## 8. Tests a añadir

- **Signos (D-018):** ménsula patrón — carga −Z → tracción arriba (N>0), flecha −Z, reacción +Z, M de empotramiento de signo conocido.
- **Releases (D-020):** barra biarticulada → solo axil (M nulo en extremos); aspa derivada → articulada por defecto.
- **Estado de dato (D-021):** un layer `computed` **nunca** renderiza con estilo certificado; solo el *write-back* firmado vira a verde; exportación no firmada estampa la marca.
- **QA (D-023):** Decopak HQ, ELU → `computed` → reconciliación PyNite → `qa-passed`; caso forzado de discrepancia → `qa-fail` que bloquea; equilibrio Σreacciones=Σacciones.
- **Contrato C5 (D-019):** round-trip de los tipos extendidos; caso patrón end-to-end (una combinación → deformada + aprovechamientos `computed`).

## 9. Pendientes / saneamiento (la IA propone; JM firma)

- **Re-sellar en Windows** los tests añadidos tras los 38 verdes (grueso, torcido, verticalización, cosido de 4 láminas, columna-cajón hueca, grupos) con `npm run typecheck; npm test`.
- **Verificar** que `motor-fem` y PyNite no comparten núcleo de solver (D-023·C.1).
- **`versions.lock`:** sello de dos llaves del release **N1.1** del núcleo (golden verde + tag GPG de JM) sigue «☐ Pendiente» — condición para apoyarse en el motor en producción.
- Afinado de umbrales de idealización (tolerancia de nudos, planar/grueso/torcido).

---

*Continuidad preparada por la IA · proyecto Aqyra, paso del marco de decisiones de V3 al hilo de desarrollo · 2026-06-25. D-018 a D-023 firmadas; implementación por arrancar (empezar por los tipos públicos del contrato C5). La IA opera; JM firma.*

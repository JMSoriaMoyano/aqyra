# HILO-V3 · D-022 — Alcance del armado en V3 — FIRMADO

> **✅ ESTADO: FIRMADO por JM el 2026-06-25 con C.1 sí + C.2.a.** Suelo de V3 = verificación + «qué no cumple» (cierra el DoD); armado EC2 escalonado dentro de V3 (tras probar la espina). Inscrita en `DECISIONES.md` como **D-022**. Este documento se conserva como evidencia. La IA preparó la evidencia; **JM decidió y firmó**.
> **Propuesta original de la IA** (Ing. estructural / Producto) con evidencia. **La IA prepara la evidencia; JM decide y firma.**
> **Qué resuelve:** cuánto hace V3 por el lado del **armado/dimensionado** — si entrega verificación de aprovechamiento + «qué no cumple», o además calcula la **armadura necesaria** de elementos y núcleo. Acota el alcance antes de implementar.
> **Apoyo ya firmado:** **D-019** (esquema de resultados, incl. esfuerzos de membrana/placa), **D-021/D-023** (estado de dato y QA: todo armado es resultado **bajo dos llaves**).
> **Fecha:** 2026-06-25.

---

## A. La distinción que ordena la decisión

Dos cosas que se confunden y aquí hay que separar:

- **Verificar aprovechamiento** (*unity check*): dada una sección **con sus propiedades de resistencia**, comprobar capacidad vs demanda → ratio de aprovechamiento y «cumple / no cumple».
- **Dimensionar / armar** (*design*): calcular la **armadura necesaria** (áreas de acero, disposición) para satisfacer los estados límite.

La diferencia **depende del material**:

- **Acero (EC3):** los elementos llevan la **sección completa** → la **verificación es directa** (interacción N-M-V, pandeo de barra y lateral). El «armado» del acero es, en esencia, que el perfil basta + las uniones. → **Computable en V3 sin dato extra.**
- **Hormigón (EC2) y núcleo:** el aprovechamiento **necesita la armadura**. Si el IFC **no trae el armado** (Decopak HQ modela geometría, no barras de refuerzo), no se puede «verificar» un diseño que no existe: hay que **dimensionarlo** (As necesaria). → **Verificación y armado van acoplados.** Para el **núcleo**, la armadura sale por el **modelo sándwich** (EN 1992-2 Anejo LL / EN 1992-1-1:2023: tres capas; las exteriores toman membrana+flexión, el núcleo el cortante) a partir de los esfuerzos de lámina, o por la **columna-cajón equivalente** — las dos idealizaciones que V2 ya deja como `proposal` (D-016/D-017).

**Consecuencia:** «aprovechamiento EC3» (acero) es alcance ligero; el «qué no cumple» del **hormigón** exige meterse en el **armado**.

**Anclaje del DoD (roadmap V3):** «ver la deformada bajo una combinación ELU, **colorear por aprovechamiento EC3** y listar los elementos al límite». El DoD es, literalmente, **verificación** (acero), no armado.

---

## B. Propuesta (lo que se firma)

### B.1 · Suelo de V3 (cumple el DoD) — siempre dentro
Para **todo** el modelo, bajo combinación: **esfuerzos** N/V/M + **deformada** + **reacciones**, con su `DataState` (D-021). Para **acero**: **aprovechamiento EC3** (interacción + pandeo) + **«qué no cumple»**. Esto **cierra el DoD** del roadmap.

### B.2 · Armado EC2 (la capa pesada) — por fases
El dimensionado de hormigón —elementos (vigas/pilares/losas EC2) y **núcleo** (sándwich de 4 láminas o columna-cajón, según la idealización que el ingeniero eligió en V2)— es un alcance EC2 grande. Se propone **escalonarlo dentro de V3**: primero probar la **espina** (modelo→motor→resultados→QA→firma→pintado con estado) sobre la verificación; **después** el armado como el siguiente incremento de V3. Todo armado es resultado **bajo dos llaves** (D-023) y vive en el **entorno certificado** (`privado/`).

### B.3 · Gobierno y frontera
La **mecánica** del armado (fórmulas EC2/EC3, sándwich, cuantías) es cálculo certificado en `privado/`; el **criterio** de qué combinaciones/detalle aplican por norma sigue siendo anzuelo (V4). El resultado del armado se pinta en el visor con su estado (nunca `verified-signed` sin las dos llaves).

---

## C. Puntos abiertos para JM

**C.1 · Suelo de V3 = verificación + «qué no cumple» (B.1).** ¿Confirmar que el primer corte de V3 entrega esfuerzos + deformada + **aprovechamiento EC3 (acero)** + «qué no cumple», cerrando el DoD del roadmap? *Recomendado sí.*

**C.2 · Cuándo entra el armado EC2 (elementos + núcleo).**
- **C.2.a (recomendada) — escalonado dentro de V3:** primero el lazo end-to-end con verificación (B.1) y las dos llaves probadas; **luego** el armado (elementos EC2 + núcleo por sándwich/columna-cajón) como incremento de V3. Disciplina: probar la espina antes de cargar el armado; el hormigón obtiene su «qué no cumple» en ese incremento.
- **C.2.b — armado completo en el primer corte de V3:** incluir el dimensionado de elementos y núcleo desde el principio. Más valor de golpe, pero mucho más alcance EC2 (sándwich) **antes** de tener el pipeline probado → más riesgo de no cerrar V3.
- **C.2.c — armado fuera de V3:** V3 solo verificación (acero); todo el armado va a una versión posterior. Más ligero, pero deja el **hormigón sin «qué no cumple» real** en V3 (solo esfuerzos/deformada).

**Nota técnica (no es bifurcación):** el armado del núcleo **sigue la idealización que el ingeniero eligió en V2** — 4 láminas cosidas (sándwich) o columna-cajón equivalente (D-016/D-017); el motor arma sobre la que esté activa.

---

## D. Entrada lista para `DECISIONES.md` (al firmar)

### D-022 · Alcance del armado en V3 (V3)
- **Fecha de firma:** ____ · **Firmante:** JM · **FIRMA: ☐ pendiente**
- **Decisión:** el **suelo de V3** (cumple el DoD del roadmap) entrega, para todo el modelo y por combinación, **esfuerzos N/V/M + deformada + reacciones** con su `DataState`, y para **acero** el **aprovechamiento EC3** (interacción N-M-V, pandeo) + **«qué no cumple»**. El **armado EC2** (elementos de hormigón + **núcleo** por **modelo sándwich** —EN 1992-2 Anejo LL / EN 1992-1-1:2023— o columna-cajón equivalente, según la idealización elegida en V2) es la **capa pesada**, [opción C.2 firmada]. Distinción clave: en hormigón sin armadura en el IFC, **verificar exige dimensionar** (el «qué no cumple» del hormigón vive en el armado). Todo armado es resultado **bajo dos llaves** (D-023), en entorno certificado (`privado/`); la mecánica es cálculo, el criterio normativo sigue siendo anzuelo (V4).
- **Bifurcaciones firmadas por JM:** [C.1 suelo de V3 = verificación + «qué no cumple»: sí] · [C.2 armado EC2: a) escalonado dentro de V3 / b) completo en el primer corte / c) fuera de V3].
- **Evidencia:** roadmap V3 DoD (deformada + aprovechamiento EC3 + elementos al límite = verificación); EN 1992-2 Anejo LL / EN 1992-1-1:2023 — **modelo sándwich** de 3 capas para armar láminas/núcleo desde esfuerzos de membrana/placa (verificado 2026-06-25); EC3 — interacción y pandeo para verificación de acero; D-016/D-017 (idealización del núcleo: 4 láminas / columna-cajón), D-019/D-021/D-023. Detalle en `HILO-V3_para-firma_D-022-armado.md`.
- **Acciones que dispara:** (1) implementar el **suelo de V3** (esfuerzos/deformada/reacciones + aprovechamiento EC3 + «qué no cumple») sobre el contrato C5 (D-019); (2) [según C.2] planificar el **armado EC2** (elementos + núcleo sándwich/columna-cajón) como incremento o primer corte; (3) pintar aprovechamiento/armado con `DataState` (D-021) y bajo QA (D-023); (4) caso patrón: Decopak HQ → aprovechamiento EC3 de las barras de acero al límite (DoD), y un elemento/núcleo de hormigón armado de ejemplo en el incremento de armado.

---

## Fuentes

- **Modelo sándwich EC2 (armado de lámina/núcleo):** idealización en 3 capas; las capas exteriores resisten membrana + flexión, el núcleo el cortante transversal; la armadura de las capas exteriores se estima de las demandas de membrana (principios en EN 1992-2:2005 Anejo LL; consolidado en EN 1992-1-1:2023). Consultado 2026-06-25: [Design of RC wall panels — Eurocode sandwich model (Taylor & Francis)](https://www.tandfonline.com/doi/full/10.1080/19648189.2022.2090446) · [Shell Design Guide as per Eurocode 2 — midas](https://resource.midasuser.com/en/blog/structure/shell_design_guide_as_per_eurocode2)
- **Estado interno:** `HOJA_DE_RUTA.md` §3·V3 (DoD = deformada + aprovechamiento EC3 + elementos al límite), `HILO-V2_observaciones-idealizacion.md` §3 (armado del núcleo de membrana/placa o sección cajón → diferido a V3), `DECISIONES.md` D-016/D-017 (idealización del núcleo), D-019/D-021/D-023 — repo Aqyra, 2026-06-25.

---

*Para-firma de D-022 · proyecto Aqyra, hilo V3 · evidencia preparada por la IA · 2026-06-25. Tras la firma, trasladar §D a `DECISIONES.md`. La IA opera; JM firma.*

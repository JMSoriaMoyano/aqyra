# Aqyra · V3 — Spec de arranque (post-proceso bajo dos llaves)

> **Qué es:** documento maestro que ordena las piezas de V3 antes de escribir código. Fija alcance (dentro/fuera), las piezas y su contrato, el orden de trabajo con sus dependencias, las decisiones que **JM debe firmar** y la Definición de Hecho. La IA propone; **JM decide y firma**.
> **Estado:** propuesta de la IA (PM / Ing. BIM-IFC) para revisión y firma de JM · 2026-06-25.
> **Procedencia:** `HILO-V2_cierre-y-arranque-V3.md` (cierre V2), `HOJA_DE_RUTA.md` (V3), `DECISIONES.md`, `ESTRATEGIA_NEGOCIO.md`, `integracion/versions.lock` y el código real de V2 (`publico/embed/src/contract.ts`, `publico/openbim/src/index.ts`, `publico/visor/src/idealize.ts`).

---

## 0. V3 en una frase

> **V3 conecta el modelo analítico `proposal` que V2 deriva del IFC con el motor de cálculo anclado, y devuelve esfuerzos, deformada y aprovechamientos pintados sobre el modelo — pero solo los marca como `verified-signed` tras QA independiente y la firma de JM.** El pre (V2) ya está; V3 es el post que resuelve al ingeniero de Decopak HQ.

**DoD de la versión (heredada de `HOJA_DE_RUTA.md` §3·V3):** sobre Decopak HQ, ver la deformada bajo una combinación ELU, colorear por aprovechamiento EC3 y listar los elementos al límite — cada resultado con su **estado de dato** visible.

---

## 1. Lo que V3 hereda de V2 (el input ya existe en código)

V3 no parte de cero: el **input del cálculo ya está modelado y testeado** en `publico/`. El `StructuralModel` de V2 (`publico/openbim/src/index.ts`) es exactamente lo que el motor consume:

| Pieza del modelo | Tipo en código | Estado V2 |
|---|---|---|
| Nudos | `StructuralNode[]` | Derivado (clustering, tol. 150 mm · D-014) |
| Barras | `StructuralMember[]` + `SectionRef` | Derivado (PCA, clasificación, partido/cruces) |
| Superficies | `StructuralSurface[]` (`diaphragm`/`shell`, área real, planar/thick/skewed) | Derivado + idealización editable (D-016) |
| Núcleos | `StructuralCore` (columna-cajón hueca + J de Bredt), `StructuralCoreGroup` (4 láminas cosidas) | Derivado |
| Apoyos | `Support` + `Restraints` (6 GdL) | Autorado (`proposal`) |
| Cargas | `Load` (puntual/distribuida) | Autorado (`proposal`) |
| Casos / combinaciones | `LoadCase`, `Combination` (expresión genérica editable) | Autorado (`proposal`) |

Dos cimientos de V3 **ya están puestos** en el contrato del cebo:

- **`DataState = "proposal" | "verified-signed"`** está reservado en `embed/src/contract.ts` desde V1, con el comentario explícito de que «el post-proceso firmado (V3, contrato C5) podrá marcar `verified-signed`». La mecánica de las dos llaves tiene punto de apoyo; falta cablearla.
- **Write-back diff-able** (`appendStructuralPset`, D-013): el mismo mecanismo de anejo `Pset_Aqyra*` sirve para persistir resultados con su estado.

**Lo que V2 dejó pendiente y V3 necesita como input** (de `HILO-V2_cierre-y-arranque-V3.md` §2): la **tipificación de uniones rígido/articulado** (releases) y el **convenio de signos definitivo**. Son prerequisitos del contrato, no piezas de V3 — ver §4.

---

## 2. Las piezas de V3

### P1 · Contrato C5 — puente al motor (`privado/`, anclado)
El núcleo del anzuelo. Vive en `privado/puente-calculo/` (hoy la carpeta es solo `README`, cáscara), consume `motor-fem 0.1.0` **anclado** (`versions.lock`), no lo bifurca.
- **Entrada:** el `StructuralModel` completo + casos + combinaciones + **releases** (nuevo) + **área de carga** (nuevo).
- **Trabajo del motor:** ensambla y resuelve el FEM — cose las mallas shell (4 láminas → sección cerrada real), resuelve la columna-cajón, aplica releases / área de carga / combinaciones (ELU/ELS; sísmica fuera, ver §6).
- **Salida:** esfuerzos (N/V/M), deformada, reacciones, aprovechamientos y el «qué no cumple», **cada resultado con su `DataState`**.
- **Anclaje de estándar:** la salida mapea al **IFC StructuralAnalysisDomain** — `IfcStructuralResultGroup` agrupa los resultados y referencia el `IfcStructuralAnalysisModel` (`ResultGroupFor`); las reacciones de apoyo son `IfcStructuralReaction`. Es la vía estándar para devolver resultados que el visor pinte y para el write-back. *(Verificado: IFC4.3, buildingSMART — ver Fuentes.)*

### P2 · Resultados sobre el modelo (`publico/visor`, cebo)
La superficie pública: pintar lo que el puente devuelve.
- Deformada escalable, mapas de color por esfuerzo/aprovechamiento, diagramas N/V/M por barra, **elementos críticos** (aprov. > 0,9), envolventes por combinación.
- **Cada capa de resultado lleva su estado de dato visible**; el visor nunca pinta como verificado lo no firmado.
- Los **tipos del esquema de resultados** (la forma de datos que el visor consume) son públicos; el **adaptador que los produce** es privado.

### P3 · Dos llaves (gobierno) — el diferencial
- Un resultado nace `proposal` (lo que el motor calcula sin certificar).
- Pasa a `verified-signed` **solo** tras (a) QA independiente (P5) y (b) **firma de JM**.
- El visor **bloquea** el pintado como verificado de lo no firmado (regla inviolable de `privado/README.md` y del contrato).
- Decisión de producto pendiente: **cómo se representa** ese estado en pantalla (P3 → D-021).

### P4 · Armado (entorno certificado)
- Del **núcleo** (de esfuerzos de membrana/placa de las láminas o de la sección cajón) y de **elementos**.
- Vive en entorno certificado (anzuelo); usa las skills EC ancladas (`estructuras-eurocodigos 0.1.0`).
- Alcance en V3 a firmar (D-022): ¿armado completo o solo verificación de aprovechamiento + «qué no cumple»?

### P5 · QA con PyNite (carril *Estructurando 2.0*)
- **Re-ejecución independiente** del cálculo con PyNite como **segunda llave** técnica, separada del motor principal (productor ≠ QA).
- Es lo que habilita el paso `proposal → verified-signed` antes de la firma de JM.

---

## 3. Frontera cebo / anzuelo en V3

| Pieza | `publico/` (cebo) | `privado/` (anzuelo) |
|---|---|---|
| C5 puente al motor | — | **adaptador** `puente-calculo/` |
| Motor FEM | — | anclado (no se publica) |
| Esquema de resultados (tipos) | **sí** (tipos que el visor consume) | — |
| Render de resultados en el visor | **sí** | — |
| Estado de dato en pantalla | **sí** (mecánica) | — |
| Verificación de dos llaves | — | **sí** (QA + firma) |
| Armado / criterio normativo | — | **sí** |
| QA con PyNite + corpus | — | **sí** |

**Regla:** si filtrarlo erosiona el foso, es privado. El visor pinta; el criterio y la verificación que dan valor, no.

---

## 4. Orden de trabajo y dependencias

```
PREREQUISITOS DE V2 (bloquean C5)
  A. Convenio de signos definitivo + ejes locales/globales  ── D-018
  B. Tipificación de uniones rígido/articulado (releases)    ── D-020
  C. (Saneamiento) re-sellar tests Windows + back-fill DECISIONES.md (§7)
        │
        ▼
P1. Contrato C5  ── D-019 (forma de entrada + result group de salida)
        │
        ▼
P1'. Cableado del motor anclado (privado/puente-calculo)
        │
        ▼
P2. Render de resultados sobre el modelo
        │
        ▼
P4. Armado  +  P5. QA PyNite (segunda llave)
        │
        ▼
P3·cierre. Flujo verified-signed (firma de JM)

EN PARALELO (no depende del motor):
P3. Diseño del estado de dato en el visor (proposal vs verified-signed) ── D-021
```

**Razón del orden:** el contrato C5 no se puede cerrar bien sin fijar antes el **convenio de signos** (si motor y visor no comparten signos, la deformada y los esfuerzos salen «del revés») ni sin los **releases** (son input del FEM). P3 (cómo se pinta el estado) es independiente del motor y puede avanzar ya, en `publico/`.

---

## 5. Decisiones para firma de JM

> **✅ SET COMPLETO — FIRMADO 2026-06-25.** Las seis decisiones de V3 (D-018 a D-023) están firmadas e inscritas en `DECISIONES.md`. El frente de decisiones de V3 queda cerrado; lo que sigue es **implementación**.

- **D-018 · Convenio de signos y ejes (prerequisito).** ✅ **FIRMADA 2026-06-25 (+Z).** Global Z-up / gravedad −Z; ejes locales por rol (`axis`/`strong`/`weak`) con mapeo a PyNite y Eurocódigo; N>0 tracción; V/M/T canónico PyNite; *releases* con polaridad invertida. Sustituye D-015. Detalle en `HILO-V3_para-firma_D-018-signos.md`.
- **D-019 · Contrato C5 (forma de datos).** ✅ **FIRMADA 2026-06-25 (C.1.a + C.2.a + C.3.a + C.4 sí).** Entrada = `StructuralModel` extendido (releases, sección/material numéricos resueltos en Aqyra, combinación `{caso: factor}`, `surface.areaLoad`); salida = esquema de resultados con `DataState`, alineado a `IfcStructuralResultGroup`/`IfcStructuralReaction`; tipos públicos, adaptador+motor privados; servicio de cálculo privado para el post-proceso. SemVer, MAJOR = rotura. Detalle en `HILO-V3_para-firma_D-019-contrato-C5.md`.
- **D-020 · Tipificación de uniones (releases).** ✅ **FIRMADA 2026-06-25 (C.b).** Nudos rígidos por defecto; extremos liberables a articulado; **aspas (`brace`) por defecto biarticuladas**; *releases* 6 GdL/extremo (true=liberado) en `StructuralMember.releases?` + `Pset`; semirrígido diferido. Detalle en `HILO-V3_para-firma_D-020-uniones.md`. *Input del FEM; prerequisito de C5.*
- **D-021 · Estado de dato en el visor.** ✅ **FIRMADA 2026-06-25 (C.1.a + C.2).** 4 estados (`proposal`/`computed`/`qa-passed`/`verified-signed`) mapeados a ISO 19650 (S0/S0/S3/A); regla visual binaria (solo `verified-signed` = certificado); verde *gated* a `verified-signed`, acuñado solo por el flujo de firma de `privado/`; guarda de exportación (toda salida no firmada estampa «NO VERIFICADO»). Detalle en `HILO-V3_para-firma_D-021-estado-dato.md`. *Independiente del motor; en `publico/`.*
- **D-022 · Alcance del armado en V3.** ✅ **FIRMADA 2026-06-25 (C.1 sí + C.2.a).** Suelo de V3 = esfuerzos + deformada + reacciones + aprovechamiento EC3 (acero) + «qué no cumple» (cierra el DoD); armado EC2 (elementos + núcleo por sándwich/columna-cajón) **escalonado dentro de V3** tras probar la espina. En hormigón, verificar exige dimensionar. Detalle en `HILO-V3_para-firma_D-022-armado.md`.
- **D-023 · Carril QA (segunda llave).** ✅ **FIRMADA 2026-06-25 (C.1 sí, C.2 propuesta, C.3 sí, C.4.a).** PyNite = QA independiente (código ≠ `motor-fem`) que produce `qa-passed`; reconcilia equilibrio/reacciones/desplazamientos/esfuerzos/aprovechamientos con tolerancias; equilibrio como gate previo; `qa-fail` bloquea con anulación documentada. Anclado en Cat 3 (BS 5975). Detalle en `HILO-V3_para-firma_D-023-qa-pynite.md`.

---

## 6. Fuera de V3 (límites explícitos)

- **Copiloto NL con criterio del corpus** (qué cargas/combinaciones tocan por norma) → **V4**.
- **BCF / IDS** → V1·F3/F4 (no es post-proceso).
- **Sísmica:** el motor podrá aplicar combinación sísmica, pero el **alcance sísmico de V3** (espectro, ductilidad EC8) se trata como gancho diferido salvo que D-022/D-019 lo incluyan explícitamente.
- **Despliegue SaaS / cebo externo** → V5.

---

## 7. Gaps detectados (acción de JM recomendada antes de anclar V3)

Cotejo de la spec contra el repo real al 2026-06-25:

1. **`DECISIONES.md` está completo y al día — VERIFICADO 2026-06-25.** Registra D-001..D-017, todas firmadas por JM, y D-007 está íntegro. Notas de estado, no gaps: **D-015** (signos) está firmada como **provisional** y queda **superada por D-018** en V3; **D-017** está firmada **parcial**, con sus diferidos (4 láminas para EST-02, carga por área, cosido FE) trazados hacia V3.
2. **`privado/` es solo `README` (cáscara).** No existe aún `puente-calculo/`; C5 se construye sobre carpeta vacía — esperado, pero es trabajo nuevo íntegro.
3. **Prerequisitos de V2 — DECIDIDOS, pendientes de implementar:** convenio de signos (D-018), releases de uniones (D-020) y carga por área (D-019·C.3.a) ya están **firmados**; falta **cablearlos en código**. Sigue abierto el **saneamiento**: re-sellar en Windows los tests añadidos tras los 38 verdes y afinar umbrales.
4. **`versions.lock`:** `motor-fem 0.1.0` está anclado, pero el **sello de dos llaves del release N1.1** (suite golden verde + tag GPG de JM) sigue «☐ Pendiente». La firma del release del núcleo es condición para apoyarse en el motor en producción.

---

## 8. Próximo paso propuesto

**Decisiones cerradas (D-018 a D-023, firmadas 2026-06-25); empieza la implementación.** Orden natural, todo sobre el marco firmado:

1. **Tipos públicos del contrato C5** (`publico/`, D-019): extender la entrada (`member.releases` D-020, sección/material numéricos, `combination.terms`, `surface.areaLoad`) y definir los **tipos de resultado** con `DataState` (D-021, añadir `computed`/`qa-passed`). Corregir el *default* de carga a −Z (D-018). Bump SemVer.
2. **Estado de dato en el visor** (`publico/`, D-021): chip + marca de agua + leyenda + guarda de exportación, con el verde *gated* a `verified-signed`. No depende del motor → en paralelo.
3. **Adaptador C5 + servicio de cálculo** (`privado/puente-calculo/`, D-019·C.4): serialización modelo→motor, traducción ejes/signos/releases, *solve*, mapeo de resultados.
4. **QA PyNite** (`privado/`, D-023): re-cálculo independiente + equilibrio + reconciliación → `qa-passed`.
5. **Suelo de V3 / DoD** (D-022·C.1): deformada + aprovechamiento EC3 + «qué no cumple» sobre Decopak HQ, bajo dos llaves. Luego, el **armado EC2** como incremento (D-022·C.2.a).

Saneamiento en paralelo (§7.3): re-sellar tests en Windows. JM decide por dónde empezar.

---

## Fuentes

- IFC StructuralAnalysisDomain — `IfcStructuralResultGroup` (agrupa resultados; `ResultGroupFor` → modelo de análisis), `IfcStructuralReaction`, `IfcStructuralAnalysisModel`. buildingSMART, IFC4.3 (consultado 2026-06-25): [IfcStructuralResultGroup](https://standards.buildingsmart.org/IFC/DEV/IFC4_3/RC1/HTML/schema/ifcstructuralanalysisdomain/lexical/ifcstructuralresultgroup.htm) · [IfcStructuralReaction (IFC4.3)](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcStructuralReaction.htm) · [IfcStructuralAnalysisDomain (IFC4.3)](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/ifcstructuralanalysisdomain/content.html)
- Estado interno: `HILO-V2_cierre-y-arranque-V3.md`, `HOJA_DE_RUTA.md`, `DECISIONES.md`, `ESTRATEGIA_NEGOCIO.md`, `integracion/versions.lock`, `publico/embed/src/contract.ts`, `publico/openbim/src/index.ts` (repo Aqyra, 2026-06-25).

---

*Spec de arranque de V3 · proyecto Aqyra · IA (PM / Ing. BIM-IFC) · 2026-06-25 · para firma de JM.*

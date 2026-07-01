# Decopak HQ — Plan de cálculo de la estructura completa

- **Documento:** plan de trabajo del cálculo · **rol:** build (producción)
- **Estado:** PROPUESTA — se ejecuta **tras** la aprobación de `02_bases_acciones_HIPOTESIS.md` por JM.
- **Fecha:** 2026-06-24

> Gobierno: este hilo **produce**; la **QA la ejecuta un agente independiente** con su propio oráculo. La IA **no firma ni certifica**. Todo entregable nace como **propuesta pendiente de verificación + firma de JM** (certificación de dos llaves).

---

## 1. Reproducibilidad — anclaje de versiones (BLOQUEANTE)

`versions.lock` está hoy en `0.0.0` para todo el núcleo y plugins (pendiente del primer tag, **N1.1**). Un cálculo sobre versiones `0.0.0` **no es reproducible ni defendible en el tiempo**.

**Propuesta:** registrar, al ejecutar, el **commit/tag real** de cada módulo usado (motor-fem, motor-calculo, estructuras-eurocodigos, iso19650-openbim) en una cabecera de evidencia, y subir el pin en `versions.lock` en cuanto Estructurando publique. Hasta entonces, marcar los resultados como **«calculados sobre versión no anclada»**.

## 2. Clasificación de elementos y ruta de cálculo

Orquestador: agente `motor-calculo-estructural:ingeniero-estructurista` (clasifica → enruta → FEM → combinaciones → verificación → memoria). Módulos por subsistema:

| Subsistema | Elementos (del IFC) | Norma / skill | Módulo |
|---|---|---|---|
| **A. Forjado CLT cassette** (voladizo ligero) | 4 losas CLT + 128 costillas JOIST | EC5 (kmod, clase servicio) + EC1 vibraciones | `mixtas-madera-ec4-ec5` |
| **B. Cajón O / Cercha E / Alma C** (celosías de acero, voladizos) | cordones, diagonales, montantes, diafragmas (≈ 200 IfcMember) | EC3 (clasificación, pandeo, pandeo lateral, abolladura, uniones) | `acero-ec3` |
| **C. Vigas/dinteles y tirantes de acero** | conexiones dintel O/E (32), tirantes altillo (6), conexiones (24) | EC3 | `acero-ec3` |
| **D. Muros de hormigón** | NC-Lab, NC-Vest (HA-30, e=0,30) | EC2 (flexocompresión, cortante, fisuración) | `hormigon-ec2` |
| **E. Cimentación profunda** | 2 encepados (PILE_CAP) + 10 pilotes BORED (D650×6, D450×4) | EC2 (encepado por bielas y tirantes) + EC7 (pilotes: carga, asientos) | `hormigon-ec2` + `geotecnia-sismico-ec7-ec8` |
| **F. Global / sismo** | modelo completo arriostrado | EC8 / NCSE-02 (si JM lo aprueba) | `geotecnia-sismico-ec7-ec8` + `bases-acciones` |

## 3. Flujo por elemento (build)

1. **Idealizar** desde el IFC (geometría, nudos, apoyos, secciones, materiales) → modelo de análisis.
2. **Aplicar acciones** (las hipótesis aprobadas) y generar **combinaciones ELU/ELS** (`bases-acciones`).
3. **Resolver FEM** → esfuerzos (N, V, M) y envolventes.
4. **Comprobar por Eurocódigo** → aprovechamientos (objetivo ≤ 1,0).
5. **Registrar evidencia** (entrada → versión → norma → resultado → oráculo) para QA.
6. **Write-back** de Psets de resultado al IFC (cierra V2/V3 de la validación).

**Orden propuesto** (de la carga a la cimentación, priorizando el corazón del caso): A (CLT) → B (celosías/voladizos) → C (enlaces) → D (muros) → E (cimentación) → F (global/sismo). Así los esfuerzos de los voladizos alimentan apoyos, muros y cimientos.

## 4. QA — qué preparar para el agente verificador

Para cada cálculo relevante, dejar lista la evidencia de las **tres capas** (Gobierno §B.2):

1. **Numérica (oráculo):** PyNite por defecto; donde no llegue (p. ej. voladizo con cortante a deformación tipo Timoshenko, o lámina), proponer oráculo de mayor nivel —analítico cerrado / 2.º código FEM / MMS— **a elección de JM**, que fija la tolerancia.
2. **Normativa:** comprobador de reglas separado (cuantías, flechas, aprovechamiento ≤ 1, EC2/EC3/EC5/EC7).
3. **Regresión:** los casos que se promuevan a golden corren en CI.

## 5. Candidatos a caso golden (a proponer a JM)

| id (prov.) | Caso | Oráculo candidato | Por qué |
|---|---|---|---|
| DEC-A1 | Costilla/losa CLT en voladizo (flecha + vibración) | analítico (voladizo) + EC5 | corazón del caso; ligereza |
| DEC-B1 | Diagonal del cajón a compresión (pandeo, EC3) | analítico Euler/EC3 + PyNite | barra crítica de la celosía |
| DEC-B2 | Cordón del cajón a flexión+axil | PyNite + EC3 | reparto del voladizo |
| DEC-E1 | Encepado 6 pilotes D650 (bielas y tirantes) | analítico (modelo de bielas) | región D, cimentación |
| DEC-E2 | Pilote D650 (carga vertical + asiento, EC7) | analítico EC7 | geotecnia |

Cada golden registrará su **procedencia de oráculo y tolerancia**; los aprueba JM (`contratos-golden/`).

## 6. Entregables del cálculo (cuando se ejecute, tras visto bueno)

- Esfuerzos y aprovechamientos por elemento/subsistema (≤ 1,0).
- Comprobaciones EC3 / EC2 / EC5 / EC7 documentadas.
- **Memoria de cálculo** en `calculo/` (skill `memoria-calculo`).
- Evidencia para QA + candidatos golden a `golden-candidatos/`.
- Registro de ROI (horas, retrabajo) en `roi/` (unidades A2.1: comprobación por elemento, memoria).
- IFC con write-back de resultados.

## 7. Puntos abiertos para JM (puerta de aprobación)

1. Aprobar las **hipótesis de acciones** (`02_…`), incluida la **decisión sobre sismo** (§5 de ese doc).
2. Confirmar **cargas muertas/fachada/cubierta** y **límites de flecha de voladizo**.
3. Definir si se ancla ya `versions.lock` o se calcula sobre «versión no anclada».
4. Elegir **oráculo y tolerancia** para los casos donde PyNite no baste (lámina/Timoshenko).
5. Aportar/confirmar **datos geotécnicos** (UG3, C del terreno, capacidad de pilote) para E y F.

---

**Estado del hilo:** ⏸️ detenido a la espera de tu visto bueno de las hipótesis. Tras tu aprobación, arranca el cálculo en el orden A→F.

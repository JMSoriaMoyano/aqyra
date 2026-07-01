# Política de versión y firma + mapeo build↔release (N1.1)

**Punto 8 del cierre N1.1** · 2026-06-26 · la IA prepara y recomienda; **decide y firma JM**.
Complementa `GOBIERNO_QA_Y_VERSIONES.md` (no lo contradice). Afecta a P4–P5 de `Aqyra-Raiz/FOCO6_cierre_N1.1.md`.

---

## A. Los dos espacios de numeración (y por qué hoy se confunden)

Conviven dos contadores que **no** son el mismo, pero hoy ambos se escriben `vX.Y.Z` y por eso se mezclan:

- **Build interno del taller** — el número del paquete `.plugin` que produce Estructurando (p. ej.
  `motor-calculo-estructural-v0.23.0.plugin`). Sube con cada iteración artesanal del productor.
- **Tag de release al consumidor** — lo que se ancla en `versions.lock` (p. ej. `motor-calculo 0.1.0`).
  Es el espacio SemVer **atado a contratos** (MAJOR = cambia C1..C8) que consumen 2.0 y Entorno.

**Estado de hecho hoy (2026-06-26):**

| Componente | Tag release anclado (`versions.lock`) | Paquetes `.plugin` en disco (build) | ¿Alineados? |
|---|---|---|---|
| `motor-fem` | 0.1.0 | 0.1.0 · 0.2.0 · 0.2.1 (histórico) · **0.3.0** (actual) | sí en el corte (0.1.0=0.1.0); build ya en 0.3.0 |
| `motor-calculo` | 0.1.0 | **0.22.1** (histórico) · **0.23.0** (actual) — **no existe paquete 0.1.0** | **NO — esta es la brecha** |
| `iso19650-openbim` | 0.8.2 | … 0.8.2 … **0.9.2** (actual) | sí (0.8.2=0.8.2); build ya en 0.9.2 |
| `estructuras-eurocodigos` | 0.1.0 | (skills EC) | sí |
| `visor-ifc` | 0.1.0 | 0.1.0 | sí |
| `puentes` / `obras-lineales` / `instalaciones` | 0.0.0 | 0.6.0 / 0.4.0 / 0.3.0 | fuera de N1.1 (placeholder) |

> La "brecha" 0.1.0→0.23.0 de motor-calculo **no son 22 versiones de contrato**: es build-interno vs
> tag-de-release. El motor-calculo nació numerando alto (0.2x) y nunca tuvo un paquete 0.1.0.

## B. Decisión de mapeo (recomendada): espacios separados + manifiesto

**Opción M1 (recomendada).** Mantener el **build interno tal cual** (no renumerar; 0.23.0 conserva el
significado "refactor R1–R5 byte a byte") y publicar el **release como un tag explícito** que es lo único que
`versions.lock` ancla. Cada release registra de qué build se cortó (`built-from`). Encaja con el campo
`build_interno` que ya existe en `C5_resultados.schema.json` y en `Pset_AqyraStructuralResult_Meta`.

- **Descartada M2** (renumerar todo al espacio release): destruye el historial de build y su semántica.
- **Descartada M3** (forzar build=release): motor-fem e iso19650 ya están alineados de hecho, pero forzarlo
  en motor-calculo obligaría a renumerar; mejor el manifiesto.

**Tabla de mapeo N1.1 (a fijar en P4, tras golden verde):**

| Componente | Tag release N1.1 | Se corta del build | Nota |
|---|---|---|---|
| `motor-fem` | 0.1.0 | `motor-fem-v0.1.0.plugin` | ya alineado; **no** se adopta 0.3.0 sin golden verde |
| `motor-calculo` | 0.1.0 | **el build que pase la golden corregida** (≥0.23.0, tras DEC-A1 Opción A + P3 PyNite) | el tag 0.1.0 **no** se corta hoy: se corta cuando la golden esté verde |
| `iso19650-openbim` | 0.8.2 | `iso19650-openbim-v0.8.2.plugin` | ya alineado; 0.9.2 disponible-no-adoptado |
| `estructuras-eurocodigos` | 0.1.0 | skills en uso | — |
| `visor-ifc` | 0.1.0 | `visor-ifc` V1 | — |

> **Consecuencia operativa:** anclar `motor-calculo 0.1.0` **hoy** sería prematuro (la golden tiene DEC-A1 en
> rojo y se corrió sin PyNite). El tag 0.1.0 se fija en **P4**, sobre el build que pase la golden verde (P2+P3).
> Mientras tanto el `0.1.0` anclado es un **placeholder de paridad**, no un release certificado.

**Manifiesto de release (formato propuesto)** — un `release.manifest.json` por corte, firmado:

```json
{
  "release": "N1.1",
  "fecha": "2026-06-2x",
  "componentes": [
    {"nombre": "motor-fem", "tag": "0.1.0", "built_from": "0.1.0",
     "artefacto": "motor-fem-v0.1.0.plugin", "sha256": "…",
     "contrato": "C5 v0", "golden_run": "N1.1-decopak-…", "golden": "verde"}
  ],
  "firma": "release.manifest.json.asc (GPG JM)"
}
```

## C. Política de versión: **0.x pre-estable** (recomendada)

| Opción | Implicación | Recomendación |
|---|---|---|
| **0.x pre-estable** | interfaz/contratos aún inestables; se admiten cambios incompatibles entre minors; nadie externo depende todavía | **SÍ para N1.1 y mientras dure el piloto** — coherente con C5/C8 marcados "DRAFT pre-1.0" y con todos los contratos en v0 |
| `1.0.0` | promesa de estabilidad de contrato (MAJOR = ruptura); apropiado cuando consumidores externos adoptan en serio | **diferir** — hito posterior, cuando los contratos C1/C4/C5 se congelen y haya uso real fuera del piloto |

**Regla:** subir a 1.0.0 es una decisión de JM ligada a la estabilidad de contratos, no al volumen de build.
Hasta entonces, MINOR puede romper interfaz (avisado), MAJOR se reserva para cuando exista el compromiso 1.x.

## D. Mecanismo de firma: **GPG sobre manifiesto ahora → tag GPG en git después**

Realidad hoy: empaquetado **basado en ficheros `.plugin`**, **sin repo git**. Eso condiciona el mecanismo.

| Opción | Qué firma JM | Requisitos | Recomendación |
|---|---|---|---|
| **S1 · GPG sobre manifiesto + artefactos** | `release.manifest.json` (con sha256 de cada `.plugin`) y/o cada `.plugin` con firma separada `.asc` | clave GPG de JM; **no necesita git** | **AHORA** (N1.1): es la 2ª llave operativa sin esperar a montar git |
| **S2 · tag git GPG-firmado** | el tag de release en el monorepo | **exige montar el repo git** (ver §E) | **objetivo** cuando exista el monorepo; integra con CI/CD |
| **S3 · sigstore/cosign (keyless)** | artefacto vía OIDC + transparency log | identidad OIDC + log online; orientado a OSS público | **diferir** — sobredimensionado para el piloto |

> **Matiz importante para el DoD:** el FOCO6 §6 pide "**tag GPG firmado por JM**". Con S1 (sin git) la 2ª llave
> es la **firma GPG del manifiesto de release**, equivalente funcional del tag firmado. Si se quiere literalmente
> un *tag* git firmado (S2), hay que montar el git **antes** de P5. Recomendación: cerrar N1.1 con **S1** y
> migrar a **S2** en el siguiente corte, para no acoplar el cierre del piloto a la infraestructura git.

## E. Monorepo del productor: **confirmar y montar git (recomendado), interino sin él**

- `GOBIERNO_QA_Y_VERSIONES.md` ya asume **monorepo** ("un único núcleo, propiedad de Estructurando;
  2.0 nunca lo bifurca"). Pero hoy es una **carpeta** `Estructurando/` con `.plugin` + `_releases-historico/`,
  **sin git**. La intención está; la infraestructura no.
- **Recomendación:** confirmar el monorepo y **montar un único repo git** del productor con un paquete por
  componente (`motor-fem/`, `motor-calculo/`, `iso19650-openbim/`, …), cada uno declarando su contrato y su
  SemVer; "publicar" = tag + `.plugin` + manifiesto firmado. Es prerrequisito de S2 y del CI de la "puerta de
  compatibilidad" (§8 del plan de release).
- **Interino (N1.1):** mientras no exista el git, el empaquetado `.plugin` + `_releases-historico/` +
  **manifiesto firmado (S1)** es suficiente para cerrar el piloto con trazabilidad.

---

## F. Decisiones que necesita JM (resumen)

| # | Decisión | Recomendación IA |
|---|---|---|
| 8.1 | Mapeo build↔release | **M1** (espacios separados + manifiesto `built_from`) |
| 8.2 | ¿Cuándo se corta `motor-calculo 0.1.0`? | en **P4**, del build que pase la golden verde (≥0.23.0 tras DEC-A1+P3); no hoy |
| 8.3 | Política de versión | **0.x** durante el piloto; 1.0.0 diferido a contratos estables |
| 8.4 | Mecanismo de firma | **S1 (GPG sobre manifiesto)** ahora; **S2 (tag git GPG)** en el siguiente corte; sigstore descartado |
| 8.5 | Monorepo | **confirmar y montar git**; interino con `.plugin`+manifiesto firmado |

> Con 8.1–8.5 ratificadas, P4 (anclar el tag real) y P5 (sello de dos llaves) quedan sin bloqueos de diseño:
> solo restan las acciones de ejecución (corregir DEC-A1, P3 con PyNite, cortar y firmar el release).

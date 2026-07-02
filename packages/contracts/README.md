# packages/contracts — registro de contratos

Contratos **autoritativos**: cada uno es una carpeta con su **ficha** (`contrato.md`) + su
**esquema** ejecutable (`*.schema.json`). Versionados y anclados en `../../versions.lock`.
Protegido por **CODEOWNERS**: cambios por PR aprobado.

> **No se publica** a ningún registro de paquetes: el CDE (C8) se desarrolla fuera y solo
> cumple la API en runtime. Sin infraestructura de paquetes por ahora.

## Registro (estado por contrato)

| Contrato | Ficha | Esquema | Golden | Estado |
|---|---|---|---|---|
| **C1** interoperabilidad | ✅ | ✅ `modelo-neutro` + `alto-spec` | ✅ `C1-APERTURA-01` | **Formalizado (Fase 0)** |
| **C4** federación | ✅ | ✅ `reglas-federacion` + `maestro-manifiesto` + `informe-qa` (BCF 3.0 por referencia) | ✅ `C4-FED-01` (recompute + anclado) | **Service v0 (Fase II·h2) — `services/federacion` 0.1.0, costura cerrada** |
| C9 estructura (fem) | ✅ | ⏳ | ✅ 7/7 | firmado aguas arriba; esquema a formalizar |
| C3 cumplimiento | ✅ | ⏳ | — | Fase 2 |
| C5 presupuesto | ✅ | ⏳ | — | Fase 3 |
| C10 red · C7 · C2 · C8 · C6 | ✅ | ⏳ | — | por fase |

**Contract-first, just-in-time:** el esquema de cada contrato se escribe cuando se construye
su pieza, no todos ahora. Las fichas ya existen para C1–C10 en `../../../Aqyra-Raiz`.

## Cómo se añade/promueve un esquema

1. Copiar la ficha desde `Aqyra-Raiz` a `<C>/contrato.md`.
2. Escribir el/los `*.schema.json` (JSON Schema 2020-12, *forward-open*).
3. Sembrar su golden en `../golden/<C>/` (caso + oráculo + tolerancia).
4. PR → CI verde (Llave 1) → anclar en `versions.lock` → **firma GPG de JM** (Llave 2).

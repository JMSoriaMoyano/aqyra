# INICIO de hilo — Foco 6: cierre del release N1.1 del núcleo

> Pega este texto al abrir el hilo nuevo. Es autocontenido. Trabaja sobre la carpeta `Documents\Claude\Projects` (ecosistema Aqyra).

## Rol y contexto

Actúa como ingeniero de software/QA del ecosistema **Aqyra** (industria AEC, OpenBIM), bajo supervisión de JM (Ingeniero de Caminos). El ecosistema sigue el modelo **productor → consumidor** con contratos versionados (C1..C8) y gobierno de dos llaves: **control de versiones** (blanco estable) + **QA independiente** (confianza en ese blanco).

Estructura (ver `Aqyra-Raiz/MAPA_ECOSISTEMA.md`):
- **Estructurando/** = taller/productor (motor de cálculo IFC→FEM→Eurocódigos, motor-fem, plugins). Build interno en `plugin.json` (motor-calculo va por 0.23.0).
- **Estructurando 2.0/** = gobierno/consumidor (QA, `versions.lock`, `contratos-golden/`).
- **Entorno/** = producto Aqyra (visor); consumidor que ancla el núcleo en `integracion/versions.lock`.

## Objetivo de ESTE hilo

**Cerrar el release N1.1** del núcleo (primer corte con sello de dos llaves) y dejar listo el salto de versión de los consumidores. Guion completo en `Aqyra-Raiz/FOCO6_cierre_N1.1.md` — seguirlo paso a paso.

## Estado de partida (verificado 2026-06-26)

N1.1 **no es cerrable aún**. Bloqueos:

1. **Corpus golden vacío:** `Estructurando 2.0/contratos-golden/golden/` tiene reglas y formato de ficha, pero **ningún caso poblado**.
2. **Defecto abierto DEC-A1 (NO APTO):** nervio mixto IPE 160 + CLT de Decopak — flecha 9,87 mm (build daba 2,6) y f₁ < 8 Hz (incumple EC5 §7.3). Sin corregir.
3. **QA sin oráculo certificado:** se corrió con FEM nodal numpy por no poder instalar PyNite → **re-ejecutar con PyNite**.
4. **Verificada sobre versión no anclada** (`versions.lock=0.0.0` entonces).
5. **Falta la segunda llave:** tag GPG firmado por JM + golden verde.

Material de QA existente (a reutilizar como semilla golden): `Estructurando 2.0/qa/informes/` — `QA_RESUMEN.md` (6 casos: A1, B1, B2, B4, E1, E2 con oráculos y veredictos), scripts `qa_geom_extract.py`, `qa_truss2d_cajonO.py`, `qa_normativa.py`, salidas JSON.

## Nomenclatura de versiones (no mezclar)

- **Build interno del taller** = `version` del `plugin.json` (motor-calculo 0.23.0; "refactor sin cambio funcional R1–R5 byte a byte").
- **Tag de release al consumidor** = lo anclado en `versions.lock` (motor-calculo 0.1.0 del corte N1.1), espacio SemVer atado a contratos.
- La "brecha" 0.1.0→0.23.0 es build-interno vs tag-de-release; **fijar el mapeo** es parte del cierre.

## Secuencia a ejecutar (de FOCO6_cierre_N1.1.md)

- **P1 — Sembrar golden:** convertir los 6 casos de Decopak HQ en fichas formales en `contratos-golden/golden/`, atadas a **C5 v0** (id · entrada · esperado · oráculo · tolerancia · responsable=JM). *IA redacta; JM ratifica valores y tolerancias (regla: solo JM toca golden).* **Empezar por aquí.**
- **P2 — Corregir DEC-A1:** recalcular flecha y vibración del nervio CLT y re-verificar. *IA/ingeniería; JM decide el modelo (sección mixta con conexión / más canto / criterio de aceleración).*
- **P3 — Re-ejecutar QA con PyNite** sobre la golden de P1. *Requiere entorno con PyNite instalable.*
- **P4 — Anclar versión real:** fijar el build que pasa la golden, publicarlo como tag de release, actualizar **ambos** `versions.lock` (2.0 + Entorno). *IA prepara; JM corta el tag.*
- **P5 — Sello de dos llaves:** golden verde + **tag GPG firmado por JM** + evidencia. → N1.1 CERRADO.

## Decisiones que solo cierra JM

- DEC-A1: cómo resolver f₁ < 8 Hz.
- DEC-B4: confirmar coacción lateral del montante cada 3,08 m en planos.
- DEC-E2: formato EC7 (admisible SOCOTEC vs parcial γ_R).
- DEC-B1: identificar el perfil real de la diagonal crítica (7 perfiles en el IFC).
- Política de versión (`0.x` vs `1.0.0`) y mecanismo de firma (GPG/sigstore); confirmar monorepo.
- Mapeo build↔release.

## Restricciones y reglas (no romper)

- Un fallo de QA **se arregla en el código**, nunca aflojando tolerancia ni editando el valor esperado.
- **Solo JM** cambia valores/tolerancias golden (vía PR con traza). La IA **no certifica**; prepara y propone, JM firma.
- Todo es predimensionado a revisar/firmar por técnico competente. Anejo Nacional España; NDP marcados [confirmar AN].
- El consumidor nunca consume "latest" ni rama viva: bump → golden → adoptar solo si verde.

## Requisito de entorno

P3 necesita **PyNite instalable** (`pip install PyNiteFEA --break-system-packages`); en la QA previa falló por disco/tiempo. Verificarlo al arranque; si no, P1–P2 avanzan igual y P3 espera.

## Primer paso propuesto

1. Leer `FOCO6_cierre_N1.1.md` y `Estructurando 2.0/qa/informes/QA_RESUMEN.md`.
2. Comprobar si PyNite es instalable en este entorno.
3. **P1:** redactar las 6 fichas golden (A1, B1, B2, B4, E1, E2) en `contratos-golden/golden/` con el formato del README de `contratos-golden/`, atadas a C5 v0, y pasarlas a JM para ratificar valores/tolerancias.
4. Encadenar P2 (DEC-A1) y, si PyNite está disponible, P3.

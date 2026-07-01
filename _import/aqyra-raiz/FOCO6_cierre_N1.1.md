# Foco 6 — Hoja de ruta de cierre del release N1.1

> **Qué es:** la secuencia real para cerrar el primer corte del núcleo (N1.1) con el sello de dos llaves, y para decidir después el salto de los consumidores a las versiones nuevas del taller. Sale del diagnóstico del 2026-06-26 (ver `PLAN_CONSOLIDACION.md` Foco 6).
>
> **Estado:** N1.1 **NO cerrable hoy**. No es un "firmar y listo": faltan piezas de fondo. Esta hoja las ordena.
>
> **Regla rectora (del gobierno):** el control de versiones da un blanco estable; la QA independiente da confianza en ese blanco. Un fallo de QA **no** se resuelve aflojando tolerancia ni editando el valor esperado — solo arreglando el código.

---

## 1. Por qué N1.1 no está cerrado (los bloqueos)

1. **El corpus golden está vacío.** `Estructurando 2.0/contratos-golden/golden/` tiene estructura y reglas, pero **cero casos** poblados. Sin golden no hay blanco que validar.
2. **Hay un defecto abierto (DEC-A1, NO APTO).** La QA de Decopak HQ detectó errores aritméticos del build en el nervio mixto IPE 160 + CLT: flecha 9,87 mm (no 2,6) y frecuencia f₁ < 8 Hz (incumple EC5 §7.3). Pendiente de corrección en el build.
3. **La QA se corrió sin el oráculo certificado.** Se usó un FEM nodal propio (numpy) por no poder instalar PyNite. Falta **re-ejecutar con PyNite** para el cierre definitivo.
4. **Se verificó sobre versión no anclada** (`versions.lock = 0.0.0` en el momento de la QA). Hay que **anclar la versión real** que pasa la golden.
5. **Falta la segunda llave.** El release N1.1 exige tag GPG **firmado por JM** + golden en verde. Hoy figura "☐ Pendiente".

---

## 2. Aclaración de nomenclatura de versiones (evita confusión)

Conviven **dos espacios de numeración** que no hay que mezclar:

- **Build interno del taller** — el `version` del `plugin.json` (p. ej. `motor-calculo 0.23.0`). Es el contador artesanal del productor; sube con cada iteración. La 0.23.0 es "refactor sin cambio funcional (R1–R5 byte a byte)".
- **Tag de release al consumidor** — lo que se ancla en `versions.lock` (p. ej. `motor-calculo 0.1.0`, primer corte N1.1). Es el espacio SemVer atado a **contratos** (MAJOR = cambia C1..C8).

> La "brecha" 0.1.0 → 0.23.0 **no es** necesariamente un salto de 22 versiones de contrato: es build-interno vs tag-de-release. El cierre de N1.1 debe **fijar el mapeo** entre ambos (qué build del taller se publica como qué tag de release).

---

## 3. Secuencia de cierre (en orden, con responsable)

| # | Paso | Quién | Desbloquea |
|---|---|---|---|
| P1 | **Sembrar el corpus golden** con los 6 casos de Decopak HQ (A1, B1, B2, B4, E1, E2) como fichas formales atadas a **C5 v0** (entrada · esperado · oráculo · tolerancia · responsable). | IA redacta · **JM ratifica valores** | Da el blanco a validar |
| P2 | **Corregir el defecto DEC-A1** en el build (flecha y vibración del nervio CLT) y re-verificar. | IA/ingeniería · **JM decide modelo** | Quita el NO APTO |
| P3 | **Re-ejecutar la QA con PyNite** (oráculo certificado) sobre la golden de P1, en entorno con PyNite instalable. | IA (en entorno apto) | Cierre definitivo de la QA |
| P4 | **Anclar la versión real**: fijar el build del taller que pasa la golden y publicarlo como tag de release; actualizar **ambos** `versions.lock` (Estructurando 2.0 + Entorno) a ese tag. | IA prepara · **JM corta el tag** | Blanco estable y reproducible |
| P5 | **Sello de dos llaves**: golden en verde (llave QA) + **tag GPG firmado por JM** (llave release). Registrar evidencia. | **JM firma** | N1.1 CERRADO |

> P1 es el desbloqueo de fondo y puede empezar ya. P2 es ingeniería pura. P3 exige entorno con PyNite. P4–P5 son de JM.

---

## 4. Decisiones que solo cierra JM

Heredadas de la QA de Decopak HQ y del plan N1.1 §10:

- **DEC-A1:** cómo resolver la vibración (f₁ < 8 Hz) — ¿sección mixta acero-CLT con conexión, más canto/rigidez, o justificación por aceleración?
- **DEC-B4:** confirmar en planos de detalle la coacción lateral del montante cada 3,08 m (si no se materializa → NO APTO).
- **DEC-E2:** fijar el formato EC7 (admisible tipo SOCOTEC vs parcial con γ_R).
- **DEC-B1:** identificar el perfil real de la diagonal crítica (el IFC tiene 7 perfiles distintos).
- **Política de versión y firma:** `0.x` pre-estable (recomendado) vs `1.0.0`; mecanismo de firma (GPG / sigstore); confirmar monorepo del productor.
- **Mapeo build↔release** (§2): qué build del taller se publica como el tag anclado.

---

## 5. La decisión del salto de versión (cuelga del cierre)

Subir los consumidores (Estructurando 2.0 y Entorno) desde la base anclada N1.1 a las versiones nuevas del taller (iso19650 0.9.2, motor-fem 0.3.0, puentes 0.6.0, obras-lineales 0.4.0, instalaciones 0.3.0, motor-calculo build 0.23.0) **no se hace hasta tener golden** (P1) y **solo si pasa en verde** (regla del consumidor: bump → golden → adoptar si verde). Registrado en `Estructurando 2.0/versions.lock` (bloque `disponible-no-adoptado`).

---

## 6. Definición de "N1.1 cerrado" (DoD)

- [ ] Corpus golden poblado y atado a contrato (al menos C5 v0) — P1.
- [ ] DEC-A1 corregido y re-verificado APTO — P2.
- [ ] Golden en **verde con PyNite** — P3.
- [ ] `versions.lock` (2.0 + Entorno) con el **tag real** que pasa la golden — P4.
- [ ] **Tag GPG firmado por JM** + evidencia registrada — P5.

---

## 7. Cómo se trabaja a partir de aquí

El Foco 6 es ingeniería + QA + certificación, distinto de la consolidación de Aqyra-Raiz. Se ejecuta en un **hilo dedicado** (texto de arranque en `INICIO-hilo_Foco6_cierre-N1.1.md`), idealmente en un entorno donde **PyNite sea instalable** (requisito de P3). Esta hoja de ruta es el guion de ese hilo.

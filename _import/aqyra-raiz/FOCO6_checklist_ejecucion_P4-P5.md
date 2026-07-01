# N1.1 — Checklist de ejecución P4–P5 (runbook para el siguiente hilo)

> **Qué es:** el guion paso a paso para CERRAR N1.1, a ejecutar en un entorno con **PyNite instalable**,
> **git** y tu **clave GPG**. El diseño ya está hecho (golden, contrato C5, NDP, política); aquí solo se
> ejecuta y se firma. Orden: prerrequisitos → P3 → P4 → P5 → verificación.
>
> **Regla de oro:** un fallo de la golden se arregla en el código, NUNCA aflojando tolerancia ni editando el
> esperado. Solo JM firma; la IA prepara.

---

## 0. Prerrequisitos (antes de P4 nada se ancla)

- [ ] **Entorno con PyNite** (P3 lo exige). Comprobar: `pip install PyNiteFEA --break-system-packages` y `python -c "from Pynite import FEModel3D"`.
- [ ] **DEC-A1 corregido** en el build (Opción A, sección mixta acero-CLT): EI_eff ≥ 1,42·EI_acero (≥2,59 MN·m²), flecha = 9,87 mm, **f₁ ≥ 8 Hz** con masa realista ≈450 kg/m. Re-verificar → debe pasar de NO APTO a APTO.
- [ ] **DEC-E2 re-baseline** en formato DA-2: el build aporta las resistencias **características** R_b,k y R_s,k del pilote (separadas del admisible SOCOTEC). Recalcular R_d = (R_b,k/1,35 + R_s,k/1,10)/1,40 y comparar con E_d (ELU). JM ratifica el nuevo esperado.
- [ ] **Tabla NDP ratificada** por JM (`contratos-golden/contratos/C5_NDP_anejo_nacional_ES.md`) → los `confirmado` quedan firmes.
- [ ] **7 fichas golden ratificadas** por JM (valores + tolerancias).

## 1. P3 — Re-ejecutar la golden con PyNite (oráculo certificado)

```bash
# entorno
pip install PyNiteFEA --break-system-packages

# correr la suite golden contra el oráculo (los 7 casos)
#   barra/celosía/modal -> PyNite ;  lámina (DEC-S1) -> folded-plate QA + Navier ;  EC7 (DEC-E2) -> analítico DA-2
python qa/run_golden.py            # (script de ejecución de la suite; produce el informe verde/rojo)
```

- [ ] **Las 7 fichas en VERDE** con PyNite (DEC-A1 ya corregido; DEC-S1 con su oráculo lámina; DEC-E2 en DA-2).
- [ ] Si algún caso sale rojo → vuelve al build, se corrige, se repite. No se avanza a P4 hasta verde total.

## 2. P4 — Anclar la versión real (cortar el tag)

**2.1 Elegir el build que pasa la golden** (mapeo M1, ver `Estructurando 2.0/POLITICA_VERSION_Y_FIRMA_N1.1.md`):

| Componente | Tag release a anclar | Se corta del build (`built_from`) |
|---|---|---|
| `motor-fem` | 0.1.0 | el `.plugin` que pase la golden (hoy 0.1.0; si se usa 0.3.x, anótalo) |
| `motor-calculo` | 0.1.0 | el build que pase la golden corregida (≥0.23.0 tras DEC-A1) |
| `iso19650-openbim` | 0.8.2 | 0.8.2 |
| `estructuras-eurocodigos` | 0.1.0 | en uso |
| `visor-ifc` | 0.1.0 | V1 |

**2.2 Generar el manifiesto de release** (sha256 de cada artefacto):

```bash
cd Estructurando
sha256sum motor-fem-v0.1.0.plugin motor-calculo-estructural-v0.23.0.plugin \
          iso19650-openbim-v0.8.2.plugin > N1.1.sha256
# crear release.manifest.json con: release, fecha, por componente {nombre, tag, built_from,
# artefacto, sha256, contrato, golden_run, golden:"verde"}   (plantilla en POLITICA_VERSION_Y_FIRMA_N1.1.md §B)
```

**2.3 Actualizar los DOS `versions.lock`** (deben moverse juntos, en paridad):

- [ ] `Estructurando 2.0/versions.lock` → poner los tags reales en el bloque `nucleo:`/`plugins:`.
- [ ] `Entorno/integracion/versions.lock` → los MISMOS tags.
- [ ] Reflejar en ambos el `built_from` (comentario) para trazar build↔release.

## 3. P5 — Sello de dos llaves (firma)

**Llave 1 (QA):** golden en verde con PyNite (P3) ✔ + informe de QA limpio.

**Llave 2 (release) — firma de JM.** En tu máquina, con tu clave GPG (NO en un entorno compartido):

```bash
# Opción S1 (ahora, sin git): firmar el manifiesto del release
gpg --armor --detach-sign release.manifest.json      # genera release.manifest.json.asc
# (verificación) gpg --verify release.manifest.json.asc release.manifest.json

# Opción S2 (cuando exista el monorepo git): tag firmado por componente
git tag -s motor-fem-v0.1.0 -m "N1.1 motor-fem 0.1.0 (built_from 0.x) · C5 v0 · golden verde"
git tag -s motor-calculo-v0.1.0 -m "N1.1 motor-calculo 0.1.0 (built_from 0.23.0) · C5 v0 · golden verde"
# git push --tags
```

- [ ] Firma GPG generada y verificada.
- [ ] Evidencia registrada (manifiesto + `.asc` + informe golden) junto al release.

## 4. Definición de "N1.1 cerrado" (DoD — marcar todo)

- [ ] Corpus golden poblado y atado a C5 v0 — **hecho** (7 fichas).
- [ ] DEC-A1 corregido y re-verificado APTO (P2).
- [ ] Golden en VERDE con PyNite (P3).
- [ ] Ambos `versions.lock` con el tag real que pasa la golden (P4).
- [ ] Manifiesto/tag firmado por JM + evidencia (P5).

→ Con todo marcado: **N1.1 CERRADO** y habilitado el salto de versión de los consumidores
(bump → golden → adoptar solo si verde).

## 5. Cómo montar el monorepo git (prerrequisito de S2, opcional para N1.1)

En tu máquina (la clave GPG es tuya y no debe vivir en entornos compartidos):

```bash
cd Estructurando
git init
# estructura: una carpeta por componente
#   motor-fem/  motor-calculo/  iso19650-openbim/  estructuras-eurocodigos/  visor-ifc/  ...
# .gitignore para artefactos pesados si procede (o usar git-lfs para los .plugin)
git add .
git commit -m "Monorepo del productor: estado N1.1"
# configurar la firma una vez:
git config user.signingkey <ID_de_tu_clave_GPG>
# a partir de aquí, publicar = tag firmado (-s) + .plugin + manifiesto (paso P5/S2)
```

> Mientras no exista el git, **S1 (manifiesto firmado) basta** para cerrar N1.1. El git es el objetivo del
> siguiente corte, no un bloqueo del piloto.

---

**Texto de arranque del próximo hilo:** "Ejecutar P3–P5 de N1.1 siguiendo `FOCO6_checklist_ejecucion_P4-P5.md`,
en entorno con PyNite. Empezar por corregir DEC-A1 (Opción A) y re-baseline de DEC-E2." Material: `contratos-golden/`,
`POLITICA_VERSION_Y_FIRMA_N1.1.md`, `FOCO6_avance_2026-06-26.md`.

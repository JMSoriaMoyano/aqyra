# Monorepo del productor (S2) — montaje y puerta de compatibilidad

> Cierra la migración **S1 → S2** de la política de versión y firma: de "manifiesto firmado" a
> **tags git firmados** + **puerta de compatibilidad (CI)**. La IA prepara; **JM ejecuta y firma** (clave en su máquina).

## Qué es

- **Repo del productor** = esta carpeta `Estructurando/`. Contiene los `.plugin` (artefactos de release, ~4 MB),
  el `release.manifest.json` (+ `.asc` firmado) y `N1.1.sha256`.
- **Gobierno/golden** vive aparte, en `../Estructurando 2.0/` (versions.lock, contratos, fichas golden, `qa/run_golden.py`).
- Regla de publicación: **publicar = tag git firmado + `.plugin` + manifiesto**. Un release sin tag firmado no es release.

## Paso único — montar el repo y firmar los tags

En **Git Bash**, dentro de `Estructurando/`:

```bash
cd "/c/Users/jmsor/Documents/Claude/Projects/Estructurando"
bash setup_monorepo.sh
```

El script hace `git init`, configura tu identidad y tu clave (`8FD1E413…0942`), hace el primer commit y crea
**tres tags firmados** del release N1.1 (te pedirá tu passphrase GPG):

| Tag | built_from | Contrato |
|---|---|---|
| `motor-fem-v0.1.0` | 0.1.0 | C5 v0 |
| `motor-calculo-v0.1.0` | 0.23.0 (DEC-A1 mixta + DEC-E2 DA-2 FS=3) | C5 v0 |
| `iso19650-openbim-v0.8.2` | 0.8.2 | C1 v0 |

Verás `git tag -v` confirmando "Good signature" en cada uno. Eso es el equivalente S2 del sello de dos llaves.

## Puerta de compatibilidad (CI) — la golden gobierna las adopciones

Antes de **adoptar cualquier bump** de versión, la golden C5 v0 debe estar VERDE. Tres formas:

- **Local manual:** `bash ci/gate_golden.sh`  → exit 0 = VERDE (adoptar) · 1 = ROJO (bloquear).
- **Hook git:** `cp hooks/pre-push.sample .git/hooks/pre-push && chmod +x .git/hooks/pre-push`
  → ningún push si la golden está roja.
- **GitHub Actions:** `.github/workflows/golden.yml` corre la golden en cada push/PR/tag (si publicas en GitHub).

El gate necesita PyNiteFEA en la máquina que lo corre: `pip install PyNiteFEA numpy scipy`.
Por defecto busca el runner en `../Estructurando 2.0/qa/run_golden.py` (configurable con `GOLDEN_RUNNER`).

## Flujo de adopción de aquí en adelante (productor → consumidor)

1. El productor empaqueta una versión nueva (build interno).
2. Se sube el tag de release candidato y se corre la **puerta** (`ci/gate_golden.sh`).
3. Si **VERDE** → se firma el tag (`git tag -s …`) y se actualizan los **dos `versions.lock`** en paridad.
4. Si **ROJO** → se corrige el build (NUNCA se afloja la tolerancia) y se repite.

## Estructura por componente (refinamiento futuro, opcional)

Hoy el repo se inicia tal cual (artefactos + roadmaps + fases). La política prevé, cuando convenga, reorganizar en
`motor-fem/ · motor-calculo/ · iso19650-openbim/ · …` (una carpeta por componente). No es bloqueante para N1.1:
los tags namespaced (`motor-fem-vX`) ya distinguen cada release. Los `.plugin` pueden migrarse a git-LFS si crecen.

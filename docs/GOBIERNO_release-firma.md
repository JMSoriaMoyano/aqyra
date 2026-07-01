# Gobierno & release — las dos llaves

> Cómo pasa un cambio de idea a release firmado. Resumen operativo; la fuente es
> `../../Aqyra-Raiz/FUNDACION_core_y_gobierno-CI.md`.

## Flujo de un cambio

```
rama → PR → CI (golden + esquema de lo AFECTADO, Llave 1) → revisión (CODEOWNERS) → merge
   → (si es release autoritativo) bump → anclar en versions.lock → firma GPG (Llave 2) → tag firmado
```

- **Llave 1 (automática):** `.github/workflows/ci.yml` corre la golden y la validación de
  esquemas en cada PR. **Rojo bloquea el merge.** Nadie toca `main` directamente.
- **CODEOWNERS (revisión humana):** `packages/contracts/`, `packages/golden/`, `versions.lock`
  y `.github/` requieren aprobación de JM en el PR.
- **Llave 2 (firma humana, insustituible):** el CI **nunca** certifica. La firma es un tag GPG
  de JM (ed25519). `.github/workflows/release.yml` solo **verifica** que el tag está firmado y
  la golden verde.

## Proteger `main` (una sola vez, en GitHub)

Settings → Branches → Add rule sobre `main`:
- Require a pull request before merging · Require review from Code Owners.
- Require status checks to pass → `gate` (y `visor-typecheck`).
- Include administrators · Require signed commits (opcional pero recomendado).

## Adoptar / firmar un release (lo hace JM en local)

Con la golden en verde:

```bat
git switch main && git pull
:: 1) bump del esquema/engine y anclaje
::    editar versions.lock (schema_version / engine_version)
:: 2) firmar el estado (Llave 2) — tag ANOTADO y FIRMADO
git tag -s vC1-0.1.0 -m "C1 schema 0.1.0 · golden C1-APERTURA-01 verde"
git push origin vC1-0.1.0
```

El workflow de release verifica ambas llaves. **Nada autoritativo sin las dos llaves.**

## Zona firmada — no se reescribe

Las firmas históricas de los 4 repos se **preservan**. La importación de historia (0.7) va
después del vertical, con estrategia que no reescribe lo firmado (subtree conserva hashes, o se
mantienen los repos originales como archivo de record). Ver
`../../Aqyra-Raiz/PLAN_reestructuracion_industrializacion.md §3`.

# P5 — Sello de dos llaves N1.1 (instrucciones de firma para JM)

> La IA ha preparado todo (Llave 1). **La Llave 2 la pones SOLO tú (JM), en tu máquina, con tu clave GPG.**
> La clave privada NO debe vivir en un entorno compartido. La IA NO crea ni maneja tu clave privada.

## Estado detectado en tu equipo (2026-06-26)

- **Git para Windows está instalado** (Git Bash) → trae el binario **gpg**. No necesitas instalar nada más.
- **NO tienes ninguna clave GPG todavía:** no existe el llavero en ninguna de las dos rutas estándar
  (`%APPDATA%\gnupg` de Gpg4win ni `%USERPROFILE%\.gnupg` del gpg de Git). → **Hay que crear la clave (Paso 0).**

> Por eso los comandos "rápidos" de abajo (firmar/verificar) **no funcionan aún**: primero el Paso 0.

## Paso 0 — Crear tu clave GPG (una sola vez) · en **Git Bash**

> Abre **Git Bash** (menú Inicio → "Git Bash"). Tú eliges una **contraseña** (passphrase) que protege la clave;
> no la compartas con nadie, tampoco conmigo.

```bash
# 1) confirmar que no hay clave
gpg --list-secret-keys

# 2) crear la clave (interactivo). Elige: tipo por defecto (RSA y RSA o ECC),
#    tamaño 4096, caducidad a tu gusto, nombre y email, y una passphrase.
gpg --full-generate-key
#    Nombre:  JM Soria
#    Email:   jmsoria@ciccp.es
#    (alternativa no interactiva equivalente)
#    gpg --quick-generate-key "JM Soria <jmsoria@ciccp.es>"

# 3) ver la clave creada (anota el ID o el email)
gpg --list-secret-keys --keyid-format LONG
```

## Llave 1 — QA (CUMPLIDA por la IA, preparación)

- Suite golden **C5 v0 VERDE 7/7** con **PyNite 2.0.2** (`../Estructurando 2.0/qa/run_golden.py`).
- DEC-A1 corregido (Opción A mixta, APTO) y DEC-E2 re-baseline DA-2 con **FS=3 ratificado** (u=0,33 D650 / 0,45 D450).
- Evidencia: `../Estructurando 2.0/qa/informes/golden_run_report.json` y `golden_run_consola.txt`.

> Pendiente antes de firmar: **ratificar** el re-baseline de DEC-A1 (δ=3,98 mm, f₁=10,57 Hz). DEC-E2 ya ratificado.

## Llave 2 — release (firma de JM) — Opción S1 · en **Git Bash**, dentro de `Estructurando/`

```bash
cd "/c/Users/jmsor/Documents/Claude/Projects/Estructurando"

# 1) (opcional) re-verificar los hashes del release
sha256sum -c N1.1.sha256

# 2) firmar el manifiesto del release con tu clave GPG (te pedirá tu passphrase)
gpg --armor --detach-sign release.manifest.json      # genera release.manifest.json.asc

# 3) verificar la firma
gpg --verify release.manifest.json.asc release.manifest.json
```

Con `release.manifest.json.asc` generado y verificado, **N1.1 queda CERRADO** (las dos llaves).

## Opción S2 (siguiente corte, cuando exista el monorepo git)

```bash
cd "/c/Users/jmsor/Documents/Claude/Projects/Estructurando"
git init && git add . && git commit -m "Monorepo del productor: estado N1.1"
git config user.signingkey <ID_de_tu_clave_GPG>
git tag -s motor-fem-v0.1.0     -m "N1.1 motor-fem 0.1.0 (built_from 0.1.0) · C5 v0 · golden verde"
git tag -s motor-calculo-v0.1.0 -m "N1.1 motor-calculo 0.1.0 (built_from 0.23.0) · C5 v0 · golden verde"
# git push --tags
```

## Evidencia registrada junto al release (P5)

- `release.manifest.json`  — manifiesto del release N1.1 (tags, built_from, sha256, golden=verde)
- `N1.1.sha256`            — hashes de los 3 artefactos del corte
- `../Estructurando 2.0/qa/run_golden.py`                       — runner de la suite (oráculo PyNite + analítico)
- `../Estructurando 2.0/qa/informes/golden_run_report.json`     — informe verde/rojo (7/7 verde)
- `../Estructurando 2.0/qa/informes/golden_run_consola.txt`     — traza de consola del run
- `release.manifest.json.asc`  — **FALTA: tu firma GPG (Llave 2), tras el Paso 0**

> Gobierno: la IA prepara y propone; **NO certifica**. El release sólo está CERTIFICADO con tu firma.

#!/usr/bin/env bash
# setup_monorepo.sh — Monta el monorepo git del productor (S2) y crea los tags FIRMADOS del release N1.1.
# Ejecutar en Git Bash, dentro de la carpeta Estructurando/.  Pedirá tu passphrase GPG al firmar.
set -euo pipefail

KEY="8FD1E413A02021DD3E7903CA7D59BA28515E0942"   # clave GPG de JM (JM Soria <jmsoria@ciccp.es>)
NAME="JM Soria"
EMAIL="jmsoria@ciccp.es"

echo ">> 1/5  git init (si hace falta)"
[ -d .git ] || git init

echo ">> 2/5  configurar identidad y clave de firma (local al repo)"
git config user.name  "$NAME"
git config user.email "$EMAIL"
git config user.signingkey "$KEY"
git config tag.gpgSign true        # los tags se firman por defecto

echo ">> 3/5  primer commit del estado N1.1"
git reset -q 2>/dev/null || true   # limpia el indice por si un intento previo quedo a medias
git add -A
git commit -m "Monorepo del productor: estado N1.1 (C5 v0, golden verde, release firmado S1)" || echo "   (nada que commitear)"

echo ">> 4/5  tags FIRMADOS del release N1.1 (te pedirá la passphrase)"
git tag -s motor-fem-v0.1.0        -m "N1.1 motor-fem 0.1.0 (built_from 0.1.0) · C5 v0 · golden verde"
git tag -s motor-calculo-v0.1.0    -m "N1.1 motor-calculo 0.1.0 (built_from 0.23.0) · C5 v0 · golden verde · DEC-A1 mixta, DEC-E2 DA-2 FS=3"
git tag -s iso19650-openbim-v0.8.2 -m "N1.1 iso19650-openbim 0.8.2 (built_from 0.8.2) · C1 v0 · golden verde"

echo ">> 5/5  verificación de los tags firmados"
for t in motor-fem-v0.1.0 motor-calculo-v0.1.0 iso19650-openbim-v0.8.2; do
  echo "--- $t ---"; git tag -v "$t" 2>&1 | grep -E "Good signature|object|tagger" || true
done
echo
echo "LISTO. Monorepo creado con 3 tags firmados. Para publicar en remoto (si lo hay):"
echo "   git remote add origin <URL>;  git push -u origin master --tags"

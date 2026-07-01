<!-- Plantilla de PR. La Llave 1 (golden + esquema) la comprueba el CI; la revisión de
     CODEOWNERS es obligatoria en packages/contracts y packages/golden. -->

## Qué cambia

<!-- una línea -->

## Tipo

- [ ] Contrato / esquema (`packages/contracts/`) — requiere CODEOWNERS
- [ ] Golden (`packages/golden/`) — requiere CODEOWNERS
- [ ] Engine / core / tooling
- [ ] Docs

## Checklist (definición de hecho)

- [ ] La golden pasa en local (`just check`) y en CI (Llave 1).
- [ ] Si toco un esquema: es *forward-open* (solo añadir claves, no cambiar semántica).
- [ ] **Un fallo se corrige en el código, NUNCA aflojando la golden.**
- [ ] Si es release autoritativo: bump → anclar en `versions.lock` → **firma GPG de JM** (Llave 2).
- [ ] No toco la zona firmada (historia/tags GPG existentes).

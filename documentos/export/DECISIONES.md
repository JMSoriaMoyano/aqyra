# documentos/export — DECISIONES (D-EX-1 … D-EX-5)

> La **capa TRANSVERSAL de export firmable** (el muro de cobro, E6.2): un nucleo generico
> (descriptor + manifiesto de procedencia + sellado + firma) que convierte cualquier **artefacto
> autoritativo** de Aqyra en un **bundle firmable** con las dos llaves, y su **primer consumidor**, la
> **proyeccion de valor**. Forward de E6.1/D-DV-5: «ver el valor en pantalla se siente gratis; el muro
> de cobro es el *export* firmable». **Ratificadas por JM 2026-07-12** (A/A/A/A + D-EX-4).
> Namespace propio D-EX (patron D-DV del dashboard). La IA propone; JM ratifica y firma (dos llaves).

> **REVISION 2026-07-12 (JM) — el primer consumidor son los DOCUMENTOS CONTRACTUALES.** El informe de
> proyeccion es una VISTA DE GESTION, no un entregable contractual. El entregable es el **presupuesto por
> partidas del banco de precios + los cuadros de precios n1/n2 + la justificacion de la medicion**, y junto
> al **pliego**, son los documentos con caracter CONTRACTUAL. El raIl firmable (Nivel 1, intacto) **envuelve
> los compositores que ya existen** (no re-renderiza): el consumidor PRIMARIO es `presupuesto-obra`; la
> proyeccion queda como export de GESTION (secundario); el pliego entra como slice siguiente. Ratificado:
> presupuesto contractual ahora; justificacion de medicion v0 = cantidad + criterio + origen + GUIDs.

## D-EX-1 · Casa y naturaleza de la capa — paquete NUEVO `documentos/export` (+ modulo comun)
Paquete **NUEVO** `documentos/export` (uv `aqyra-documento-export`), hermano de
`documentos/presupuesto`/`pliego`, con el **nucleo transversal** (descriptor + manifiesto + sellado +
firma). **NO es el operador C7**: C7 orquestara la ENTREGA; esto es la maquinaria de sellado+firma que
C7 usara.
API: `componer_export(artefacto, descriptor, parametros?) -> Path(bundle)`. Consume el artefacto ya
anclado; **no recalcula nada**.

**Formato del despacho — modulo COMPARTIDO (opcion A ratificada).** El compositor Word de la proyeccion
es el **3.er** consumidor del formato del despacho; se materializa la nota forward de la D1 del pliego
(«si aparece un tercer documento, extraer a un modulo comun»). Se crea **`documentos/comun`**
(`aqyra-documento-comun`, `formato.py`) y lo consume **solo el paquete nuevo**. `documentos/presupuesto`
y `documentos/pliego` **NO se tocan**: son paquetes firmados/anclados y mantienen su copia espejada
CONGELADA (no se re-ancla lo firmado). Duplicacion transitoria y honesta hasta su proximo bump.

## D-EX-2 · Consumidores y formatos de v0 — el entregable CONTRACTUAL (REVISADA 2026-07-12)
El raIl firmable tiene CONSUMIDORES por tipo de artefacto (`descriptor.artefacto.tipo`), no un formato
fijo. El consumidor **PRIMARIO** es **`presupuesto-obra`** (CONTRACTUAL), que **envuelve** los
compositores existentes y produce el bundle:
- **Word** = envuelve `documentos/presupuesto.componer_documento` (el .docx del despacho ya firmado):
  presupuesto por partidas + cuadros n1 (en letra) / n2 (descompuesto) + estado de mediciones + PEM->PEC.
- **PDF sellado** (el firmable) = mediciones + **justificacion de medicion** (criterio + origen + GUIDs) +
  cuadros + PEM->PEC + manifiesto embebido. VIA PURE-PYTHON (`fpdf2`), sin LibreOffice; anclado por
  **TEXTO extraido** (`pypdf`), NO por pixeles (coherente con las D2 de presupuesto/pliego).
- **BC3** = conecta `engines/bc3.emitir_bc3` (FIEBDC-3, LICITACION publica). Entra en v0 (sin coste: el
  emisor ya existe y traga el mismo `salida-presupuesto`, determinista por `--fecha`).
- **XLSX** = mediciones tabular (para tecnico/administracion).

El consumidor **`proyeccion-valor`** (Word/XLSX/PDF de la vista) queda como export de **GESTION**
(secundario, no contractual). El **pliego** entra como **slice siguiente** (mismo patron: envuelve
`componer_pliego`). El nucleo es agnostico: un consumidor nuevo se registra sin tocar el manifiesto/firma.

## D-EX-3 · Manifiesto y firma — integridad en el gate; firma GPG de JM en el release
**Manifiesto** = `{content_sha256 del artefacto autoritativo (huella canonica), modelo_md5 (== entradas
del artefacto), versiones_ancladas (que aporta el caller desde versions.lock), eje/corte, generador +
version, sello de tiempo DETERMINISTA (parametro, NUNCA now())}`.
Firma en **dos capas, con el reparto REAL de la infraestructura** (hallazgo del codigo: el GPG no vive
en el gate, solo en `release.yml`):
- **(a) Llave 1 / GATE (pure-python): INTEGRIDAD.** El manifiesto casa con el artefacto anclado
  (`content_sha256` recomputado + versiones + determinismo). Prueba que los numeros son los anclados,
  **no manipulados**. **NO usa GPG** (la clave privada de JM no entra en CI; `gnupg` romperia la
  hermeticidad).
- **(b) Llave 2 / RELEASE (humana): AUTORIA.** JM firma el manifiesto con su **GPG en local**
  (`firma.firmar_detached`, patron `release.yml`; tag `documento-export-v*`). El PDF queda
  **preparado para la firma cualificada/PAdES del destinatario** = integracion **forward** (Aqyra no
  aplica la firma legal del cliente en v0). **El gate prueba integridad; la firma de JM prueba autoria.**

## D-EX-4 · Contrato vertical-agnostico — esquemas del descriptor y del manifiesto (contract-first)
Se anclan `descriptor-export.schema.json` + `manifiesto-export.schema.json` (**forward-open**, patron
C4/C3/C5) **antes** del modulo. La entrada de la capa es «artefacto autoritativo + descriptor», de modo
que **cumplimiento/calculo/pliego/carbono** entren despues **sin tocar el nucleo**. Se **prueban con la
proyeccion**; se extrae mas con el **2.o consumidor** (regla de tres). A medio plazo esta capa unifica
los exports Word dispersos de las skills de calculo bajo un mismo sellado+firma.

## D-EX-5 · Muro de cobro / gobierno — CON release firmado `documento-export-v0.1.0`
La **vista sigue gratis** (no se toca E6.1; `isCertified` en `data-state.ts` intacto: solo
`verified-signed` es certificado). El **export es el firmable** con dos llaves. `estado_firmable` del
bundle SIN firmar = `computed` (**propone**); solo la firma verificada de JM acuna `verified-signed`.
Como este hilo **ES la monetizacion**, se cierra **CON release firmado** `documento-export-v0.1.0`
(Llave 2 natural), anadiendo `documento-export-v*` a `release.yml`. La IA deja **todo listo para
firmar**; **la firma la aplica JM** (insustituible).

## D-PL-1..3 · Pliego contractual firmable (Slice C, RATIFICADAS por JM 2026-07-12)
> Namespace **D-PL**. Tercera pieza del conjunto contractual firmable (junto al presupuesto, E6.2). Cierra
> coste + carbono + prescripcion por el MISMO rail de export. La IA propone; JM ratifica y firma (dos llaves).

**D-PL-1 · Consumidor `pliego-obra`.** Consumidor NUEVO en `documentos/export` (espejo de `presupuesto-obra`):
**Word** = ENVUELVE `documentos/pliego.componer_pliego` (no re-renderiza) + **PDF sellado** (por partida:
prescripcion + medicion trazable + coste + GUIDs + carbono forward-open + cuadro de trazabilidad + manifiesto
embebido) + **manifiesto**. **SIN BC3 ni XLSX** (el texto de prescripcion ya viaja en el `~T` del BC3 del
presupuesto). El artefacto autoritativo = el `salida-presupuesto` (C5); el **descriptor los porta**: la clave
**forward-open** `descriptor["pliego"] = {criterio, pack_textos}` (dicts resueltos por el caller —
`descriptor-export.schema.json` es abierto). El manifiesto ancla sus refs en `versiones_ancladas` (criterio +
pliego-textos). El nucleo (`componer_export`/manifiesto/firma/sellado) **NO se toca**: solo se registra
`"pliego-obra": PL.FORMATOS` en `_CONSUMIDORES`.

**D-PL-2 · Golden `GOL-EXP-03`.** Rama `modo=export`, `consumidor="pliego-obra"` (despacho en `_run_c5_export`
-> `_run_export_pliego`): bundle {Word, PDF sellado, manifiesto}; 8 partidas con prescripcion SIN fallback
(`criterio/AQ/v2` + `pliego-textos/AQ-DEMO/v1`, como `GOL-PLI-01`) + medicion (cantidad +-0,001) + coste
(importe +-0,01) + trazabilidad (GUIDs); carbono forward-open; manifiesto INTEGRO (Llave 1); `isCertified`
(sin firmar = `computed`); DETERMINISMO. **No-regresion de `GOL-PLI-01`** (el compositor de pliego no cambia
su comportamiento). Corre SIN ifcopenshell (LEE el `salida-presupuesto` anclado de GOL-PRE-01).

**D-PL-3 · Release.** El pliego firmable vive en `documento-export` (mismo paquete): **NO nuevo release**; lo
cubre `documento-export-v0.1.0` (o el bump si JM lo agrupa). Version del paquete SIN cambiar en el slice
(decision de JM en el cierre).

## Zona anclada (frontera dura)
Slice C solo **AÑADE** `documentos/export/pliego_doc.py` (consumidor `pliego-obra`) + su registro en
`export.py._CONSUMIDORES` (+ `__init__`) + el caso `GOL-EXP-03` + la rama `_run_export_pliego` (despacho por
consumidor en `_run_c5_export`) + `openspec/changes/c5-pliego-firmable/` + esta seccion (D-PL) + nota en
`versions.lock [documentos.export]`. **Nunca** toca `componer_pliego`/`GOL-PLI-01`, el nucleo de export
(descriptor/manifiesto/sellado/firma), `presupuesto_doc`/`GOL-EXP-01`, `proyeccion`/`GOL-EXP-02`,
`emitir_bc3`, el motor/esquema C5, los packs anclados (incl. `pliego-textos/AQ-DEMO/v1`) ni el dashboard.

### Zona anclada del nucleo (E6.2, frontera original)
Este paquete solo **AÑADE** `documentos/comun` + `documentos/export` (+ sus esquemas) + el caso
`GOL-EXP-01` (rama `modo=export` en `run_case_c5`) + edicion quirurgica de `versions.lock`
(`[documentos.comun]`, `[documentos.export]`), `[tool.uv.workspace]`, `ci.yml` (linea de pytest),
`release.yml` (tag) y `run_golden.py`. **Nunca** toca la proyeccion (`proyectar`/`GOL-PRE-03`), el
motor, el esquema C5, los packs, `documentos/presupuesto` (`GOL-DOC-01`), `documentos/pliego`
(`GOL-PLI-01`), `emitir_bc3`, ni el dashboard E6.1 (la vista, «propone»). **El export CONSUME el JSON
anclado; no recalcula.**

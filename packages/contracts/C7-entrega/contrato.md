# Contrato C7 — entrega (operador determinista del paquete firmable)

> **Ficha autoritativa** (6 campos). Fuente: `Aqyra-Raiz/C7_operador.md` (ficha C7) + la decisión de
> JM 2026-07-13 (C7 = operador DETERMINISTA de ENTREGA). El **esquema ejecutable** son los dos
> `*.schema.json` de esta carpeta. Decisiones ancladas en `DECISIONES.md` (D-C7-1..6, OK JM 2026-07-13).

## Reconciliación con la ficha de Aqyra-Raiz (LEER)

La ficha `Aqyra-Raiz/C7_operador.md` describe C7 como el **operador IA NO determinista** (interlocutor
en lenguaje natural que orquesta los engines y redacta el entregable como *propuesta* con cuatro
garantías). La decisión de JM del **2026-07-13** resuelve la tensión central de esa ficha **partiendo
C7 en dos capas**: el **cerebro** (interpretar la intención, orquestar, proponer) vive **FUERA**, en la
capa conversacional que ya existe (Cowork + skills + subagentes); y **C7 se convierte en las manos
deterministas** que reciben una `solicitud-entrega` ya conformada, la validan y la ejecutan
reproducible. Las cuatro garantías de la ficha se conservan y se **refuerzan**: *propuesta nunca
certificación* (dos llaves), *trazabilidad total* (el `manifiesto-entrega` **es** la traza), *cero
invención* (estructural: no hay LLM dentro), *conformidad* (pasa de un checklist a una **golden real
byte-a-byte**, `GOL-EN-01`). La API `solicitar_entregable(encargo, modelo, requisitos)` de la ficha es
la **frontera EXTERIOR** (el compañero IA); `componer_entrega(solicitud)` es la **frontera INTERIOR
determinista**. El foso —el entregable firmable con responsabilidad civil— vive **dentro** de C7-entrega.

## Ficha (6 campos)

**Propósito.** Orquestar la **ENTREGA** de un **paquete de entregables firmables**: tomar una
`solicitud-entrega` (proyecto/hito + lista de entregables, cada uno `{consumidor, artefacto,
descriptor}`), **envolver** `documentos/export.componer_export` sobre cada entregable, y emitir UN
`manifiesto-entrega` maestro que ata los N bundles al mismo paquete/Maestro por un **roll-up**. **La IA
prepara y propone la solicitud; C7 la ejecuta determinista; la firma es de JM.**

**Frontera.** Productor: `services/entrega` (`aqyra-entrega`). Consumidores: el producto/usuario y el
compañero IA (y, opcional y forward, el CDE vía **C8**). **Envuelve** el raíl de export
(`documentos/export`); **no** reimplementa el sellado/firma. Aguas arriba: los artefactos autoritativos
de C5 (`salida-presupuesto`), C3, C4, C9/C10 (forward).

**Entra.** Ver `solicitud-entrega.schema.json`: `{proyecto, hito?, entregables:[{consumidor,
artefacto|artefacto_ref, descriptor}], sello_tiempo, versiones_ancladas}`. El `descriptor` de cada
entregable es un `descriptor-export` **ya conformado por el caller** (para `pliego-obra` porta la clave
forward-open `pliego` con las refs/dicts de criterio + pack_textos). **C7 no lee el repo ni
`versions.lock`**: recibe descriptores pre-resueltos. El sello es DETERMINISTA (parámetro), nunca `now()`.

**Sale.** El **paquete** (una carpeta): N **bundles firmables** (cada uno = los formatos del consumidor
+ `manifiesto.json` del raíl de export) + UN `manifiesto-entrega` maestro. Ver
`manifiesto-entrega.schema.json`: `{esquema, generador, sello_tiempo, proyecto, maestro_ref?,
entregables:[{consumidor, nombre_bundle, content_sha256_manifiesto}], paquete_sha256,
versiones_ancladas}`.

**Garantía + oráculo.** **Determinista** (mismos artefactos + misma solicitud + mismo sello ⇒ paquete
byte a byte). Integridad en dos niveles: cada `manifiesto.json` individual íntegro
(`documentos/export.manifiesto.integridad`) y `paquete_sha256` == hash canónico de la lista **ordenada**
de los `content_sha256_manifiesto` (sha256 de cada `manifiesto.json`). **Nunca certifica** — dos llaves:
golden (Llave 1) + firma GPG de JM del `manifiesto-entrega` (Llave 2). Oráculo: golden `GOL-EN-01` (en
`packages/golden/C7/`), conformidad por ESTRUCTURA + INTEGRIDAD, SIN ifcopenshell.

**Versión.** SemVer; el consumidor ancla `entrega x.y.z` en `versions.lock` (`[contracts.C7]` +
`[services.entrega]`). **Estado: contract-first v0.1.0** (2 esquemas + operador `services/entrega` 0.1.0
+ `GOL-EN-01`; v0 = paquete contractual presupuesto + pliego).

## API abstracta

```
componer_entrega(solicitud, parametros?) → paquete   (N bundles firmables + manifiesto-entrega maestro)
```

Frontera exterior (compañero IA, fuera del operador): `solicitar_entregable(encargo, modelo,
requisitos) → solicitud-entrega`. El LLM **no** se invoca dentro de `componer_entrega`.

## Qué NO es (fronteras honestas)

- **No interpreta la intención** (eso es el compañero IA, fuera) ni invoca ningún LLM dentro del operador.
- **No recalcula** (no re-mide, no re-valora, no re-renderiza): LEE los artefactos ya anclados que la
  solicitud le entrega y ENVUELVE `componer_export`.
- **No lee el repo ni `versions.lock`**: recibe descriptores pre-resueltos (el caller resuelve las refs).
- **No certifica** (la firma es de JM, Llave 2) ni coloca en el CDE por estado ISO 19650 (C8, forward).

## Regla de evolución (heredada de C1/C3/C4/C5, sagrada)

*Añadir claves nuevas, nunca cambiar la semántica de las existentes.* Los dos esquemas son
*forward-open*. Consumidores nuevos (memoria de cumplimiento desde C3, memoria de cálculo desde C9/C10,
informe de coordinación desde C4, carbono), `maestro_ref` explícito, orquestación por matriz LOIN/hito,
re-entrega ante cambio de modelo y firma cualificada/PAdES del cliente = **forward**.

---
*La ficha es el diseño; los esquemas + la golden son el contrato ejecutable. La IA propone; C7 ejecuta
determinista; JM firma (dos llaves).*

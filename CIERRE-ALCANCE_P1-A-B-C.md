# Cierre de alcance — familias de P1 (A · B · C) + RFC C1

> **Para los hilos de desarrollo P1·A / P1·B / P1·C** · Aqyra-Raiz · 2026-06-28 · **ratificado por JM.**
> **Propósito:** fijar el alcance del **primer slice** de cada familia para que los hilos **no reabran** «¿qué hago primero / hasta dónde llego?». Cada decisión es la **recomendación del propio `INICIO-hilo`**, ratificada. Lo mismo está escrito en la cabecera de cada hilo (bloque «ALCANCE CERRADO»). **Si JM cambia alguna, manda este documento.**

## 0. Regla común a las tres familias (no negociable por hilo)

- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara/propone; **NO certifica**.
- **CEBO:** preview vivo, **sin export firmable, sin medidor**. El IFC autoritativo lo compila C1.
- **`alto.json` forward-open:** el cebo **emite por delante**; el contrato nunca bloquea el preview, solo gatea la salida autoritativa, additivamente (ver `RFC_C1-apertura_familias-P1.md`).
- **No reabrir el alcance:** construir el primer slice tal como queda abajo; **lo diferido es diferido** (no se adelanta sin nueva decisión de JM).

## 1. P1·A — geometría de EDIFICACIÓN

| Decisión (§5 del hilo) | CERRADA |
|---|---|
| Primer slice | **Envolvente POLIGONAL** (el salto), no el ascensor |
| Profundidad | Solo **envolvente** (fachada=aristas · forjado/cubierta=polígono · retícula **recortada** a nudos dentro). Subdivisión poligonal de espacios → **diferida** |
| Fuente del polígono | **Opt-in** (vértices del copiloto). Catastro como fuente → después |
| `W×D` | **Se mantiene como bbox/marco** (cámara/extent) |
| Frontera macro `edificio` | Emitir **todo explícito**; el macro ancho×largo queda solo informativo |
| Ascensor (A.1) | Clon de escalera con `ifcClass:"IfcTransportElement"` vía handler genérico `elementos[]` (frontera-cero); **calentamiento opcional**, no bloquea el salto |

## 2. P1·B — TRAZADO (alineaciones)

| Decisión (§5 del hilo) | CERRADA |
|---|---|
| Primer slice | **Directriz horizontal recta + arco.** Clotoide y alzado → clones siguientes |
| Representación | **Objeto propio** (`IfcAlignment` con su lista de segmentos), **no** una 4.ª variante de `Placement` |
| Definición | **Opt-in** (copiloto da puntos/segmentos). Derivación desde el parking → 2.º slice |
| Asistencia de radios | **En este slice**: mínimo **parametrizable + self-check**; consulta real a `obras-lineales` → después |
| Handoff | **Emitir ya** `alineaciones[]` en el `alto.json`, marcado «pendiente de adopción del compilador» |

> **Clave que abarata B:** C1 **ya parsea y genera `IfcAlignment`** (Ola 5). Esto **no es geometría nueva**: la salida autoritativa = cablear un handler `alineaciones[]` en `spec_to_ifc.py` reutilizando `iso19650-openbim/scripts/lineal/`. El cebo **arranca ya** sin esperar a C1.

## 3. P1·C — NORMATIVA / AUDITORÍA

| Decisión (§5 del hilo) | CERRADA |
|---|---|
| Primer slice | **AUDITORÍA** (lectura/reporte, hito 4), no la asistencia |
| Sobre qué corre | El **MODELO del cebo** (básica/inmediata). La auditoría del IFC autorado por C1 = **anzuelo** |
| **Reglas de la básica** *(la más reservada a JM)* | **Nomenclatura `AQ-*` + doble clasificación: bsDD + Uniclass** (JM 28-jun). bsDD ya vive en el modelo; **Uniclass se añade** como código determinista por `ifcClass` (igual que la URI bsDD) → pequeña dependencia: el modelo debe **emitir** el código Uniclass para que la auditoría lo compruebe |
| Salida | **Panel de auditoría** (no-conformidades), **sin certificar** |
| Cobertura | **Solo OpenBIM** ahora; regla CTE de muestra (DB-SUA escalera) → 2.º slice |
| Implementación | Reglas **codificadas en el cebo** (preview); conexión al plugin real (`iso19650-openbim`/`cte`) → después/anzuelo |

## 4. Contrato (transversal): RFC C1 de apertura

`RFC_C1-apertura_familias-P1.md` — **una sola evolución de C1, completa y diseñada (no parches):** huecos **generalizados** (cualquier anfitrión) + catálogo de **clases abierto** (`elementos[].ifcClass`, cubre ascensor y futuras sin re-bump) + **alineaciones completas** (planta+alzado+sección+peralte, reutilizando la maquinaria de Ola 5) + esquema **forward-open**. **Una golden** prueba la versión entera. Principio: cuando una capacidad entra en C1, entra **entera**, para no volver a tocar el contrato por cada variante.

## 5. Lo único que sigue abierto (reservado a JM)

- **Adoptar la RFC C1** (un bump o dos) y **firmarla** cuando su golden esté verde.
- **Vetar/ajustar** cualquier decisión de §1–§3 si discrepas (editar aquí; manda este documento).
- Si la RFC **pasa al `ROADMAP_cebo-anzuelo.md`** (decisión del hilo de estrategia).

*Procedencia: Aqyra-Raiz · hilo de coordinación · cierre de alcance de las familias de P1 para JM · 2026-06-28.*

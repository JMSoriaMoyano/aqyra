# Inicio de hilo — P1·C Visor/Editor · NORMATIVA + AUDITORÍA (transversal · hito 4)

Actúa como **ingeniero de software del Visor/Editor IFC de Aqyra** (cebo, contrato C1), bajo
supervisión de JM. Este hilo abre la familia **transversal**: la **maquinaria normativa** que **asiste
a la entrada** (generadores gobernados por la norma) y **audita a la salida** (verifica el modelo
contra reglas). Es el **hito 4 explícito** («auditoría IFC básica») y donde el cebo empieza a **oler a
valor profesional**. Sirve a las dos familias geométricas: **CTE** para edificación (hilo A),
**`obras-lineales`** para trazado (hilo B).

## ✅ ALCANCE CERRADO (JM · 2026-06-28) — no reabrir; sin parches, construir el primer slice
Decisiones de §5 ratificadas. **No re-preguntar el alcance.**
- **Primer slice = AUDITORÍA** (lectura/reporte, hito 4), no la asistencia.
- Sobre el **MODELO del cebo** (básica). La del IFC autorado por C1 = anzuelo.
- **Reglas básicas = nomenclatura `AQ-*` + doble clasificación bsDD + Uniclass** (JM 28-jun). bsDD ya vive en el modelo; **Uniclass se añade** como código determinista por `ifcClass` (como la URI bsDD) → el modelo debe emitirlo para auditarlo.
- **Panel de auditoría** (no-conformidades), **sin certificar**.
- **Solo OpenBIM** ahora; muestra CTE (DB-SUA escalera) → 2.º slice.
- Reglas **en el cebo** (preview); plugin real (`iso19650-openbim`/`cte`) → después.
- Frontera C1: **cero** (lectura). Dos llaves: golden + firma JM.

## 0. Encuadre — la misma maquinaria asiste y audita
- Una regla normativa tiene **dos caras**: **asistir** (la regla *gobierna* cómo se coloca algo) y
  **auditar** (la regla *verifica* lo colocado). Misma maquinaria, dos sentidos.
  - *Asistir:* el generador deja de usar *defaults* tontos y **pregunta al plugin** — DB-SUA da la
    geometría de peldaño y el ancho de la escalera; DB-SI da el ancho/nº de escaleras por evacuación;
    `obras-lineales` da el radio mínimo de un vial. (Puntos 1b y 3 del brainstorm.)
  - *Auditar:* sobre el modelo ya hecho, **comprobar** que cumple — nomenclatura/Psets/clasificación
    (OpenBIM/ISO 19650) y exigencias básicas (CTE / 3.1-IC). (Hito 4.)
- **Los plugins YA existen:** `iso19650-openbim` (validación de IFC: nomenclatura, Psets, clasificación,
  calidad), `cte-documentos-basicos` (DB-SI/SUA/HS/HR/HE/SE), `obras-lineales` (3.1-IC, drenaje, firmes).
  El visor **modela**; el plugin **asiste/audita**.

## 1. CEBO y frontera — básica en el cebo, firmable en el anzuelo
- Regla CEBO: el visor **se siente gratis** (sin medidor, **sin export firmable**); el muro de cobro
  vive en el anzuelo. La **auditoría BÁSICA** es un **teaser de valor** dentro del cebo: **reporta
  no-conformidades**, **no certifica**. Las **dos llaves** siguen: la IA prepara/propone; **JM firma**.
- **Reservado a JM (regla del proyecto):** *qué reglas entran en la auditoría básica*. La básica vive
  en el cebo; la auditoría **completa y firmable** (sobre el IFC autorado por C1, vía `iso19650-openbim`)
  es del **anzuelo**.
- Frontera C1: la auditoría es **lectura** — no añade primitivos al `alto.json`. Frontera-cero. (La
  asistencia tampoco cruza frontera: cambia *cómo* el generador coloca, no *qué* emite.)

## 2. Lo que YA existe (no se reescribe)
`Entorno/publico/demo/src`: `model.ts` (`BuildingModel` con todos los elementos — cada uno con su
**código `AQ-*`** y su **URI bsDD**), `diseno.ts` (árbol IFC, panel de detalle con **bsDD en vivo**,
`selfCheck` ya compara «lo pedido vs lo colocado» en el parking — semilla de auditoría), `c1-bridge.ts`
(`alto.json`), `fixture.ts` (golden), `vite.config.ts` (operador IA). Golden `columns.golden` **35/35**
+ `parking.golden` 7/7 verde. Plugins: `iso19650-openbim`, `cte-documentos-basicos`, `obras-lineales`.
(Historia detallada de la capa de elementos: en la memoria del proyecto.)

## 3. Reglas (no romper)
- **Determinismo verificable:** mismo input → misma salida; arnés + fixture golden por caso.
- **Dos llaves:** golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara y propone; **NO
  certifica** — la auditoría reporta, no firma.
- **CEBO:** sin export firmable, sin medidor. La auditoría **básica** es preview de valor; la firmable
  es del anzuelo.
- **Reservado a JM:** alcance de cada slice y **qué reglas entran en la auditoría básica**.

## 4. Alcance del primer slice (recomendado)
Abrir por la **AUDITORÍA** (es lectura, menor riesgo, y es el hito explícito); la **asistencia** (las
reglas gobernando la generación) entra después, reutilizando la misma maquinaria.

**Motor de auditoría básica + primer juego de reglas OpenBIM, sobre el MODELO del cebo** (inmediato,
sin round-trip a C1): recorre el `BuildingModel`, comprueba un set inicial y **reporta** las
no-conformidades en un **panel de auditoría** del visor (no certifica). Set inicial propuesto (lo que ya
vive en el modelo):
- **Nomenclatura:** todo elemento con código `AQ-*` válido y único.
- **Clasificación (doble):** todo elemento con **URI bsDD** + **código Uniclass 2015** coherentes con su `ifcClass` (C1 0.10.0 ya autora la doble clasificación determinista; el modelo del cebo debe emitir el código Uniclass).
- **Coherencia estructural:** cada hueco con su `host`/`container`, cada forjado con su nivel, etc.
- **SIN** conexión al plugin real todavía (las reglas básicas se codifican en el cebo como preview),
  **sin** reglas CTE aún (una de muestra — p. ej. DB-SUA: relación huella/contrahuella + ancho mínimo de
  la escalera — como **segundo** slice, para enseñar la conexión), **sin** la asistencia de generación.

## 5. Primer paso — el alcance YA ESTÁ CERRADO (ver bloque ✅ arriba)
**No re-preguntes el alcance**; construye directamente el primer slice (auditoría básica sobre el
modelo del cebo) según el bloque «ALCANCE CERRADO». Las decisiones de abajo quedan **solo como
registro** de por qué se decidió así (ya resueltas con la recomendación):

Auditoría:
1. ¿La auditoría corre sobre el **MODELO del cebo** (inmediata, teaser) o sobre el **IFC autorado por
   C1** (`iso19650-openbim`, completa)? (rec.: sobre el modelo en el cebo = básica; la del IFC = anzuelo.)
2. **Reglas de la «básica»** (decidido JM 28-jun): **nomenclatura `AQ-*` + doble clasificación bsDD + Uniclass**. (Psets por defecto y coherencia estructural → más adelante.)
3. ¿Reporte en un **panel de auditoría** del visor (no-conformidades), **sin certificar**? (rec.: sí —
   reporta, no certifica.)
4. ¿Una **regla CTE de muestra** (DB-SUA escalera) ya en este slice, o solo OpenBIM? (rec.: solo
   OpenBIM ahora; la muestra CTE como 2.º slice.)
5. ¿Conectamos ya con el **plugin real** (`iso19650-openbim`/`cte`) o codificamos las reglas básicas en
   el cebo como preview? (rec.: reglas básicas en el cebo; conexión al plugin real después / anzuelo.)

Si **asistencia**: confirmar el primer caso (rec.: la **escalera asistida por DB-SUA** — huella/
contrahuella/ancho desde la norma, sustituyendo los defaults) y a qué plugin se llama.

Con eso cerrado, construyo el slice, lo pruebo en tu pantalla y lo dejo con su arnés + fixture golden
para tu firma. La IA prepara; JM firma.

*Procedencia: P1 Visor/Editor · Aqyra · inicio de hilo de NORMATIVA + AUDITORÍA (transversal, hito 4) · para JM.*

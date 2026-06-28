# C5 — Contrato de interfaz: dominio de análisis ↔ motor-fem

**Tipo:** contrato de interfaz (SemVer) · **zona protegida** (`contratos-golden/contratos/`)
**Versión:** v0.1.0 (DRAFT, pre-1.0 → interfaz aún inestable) · **Fecha:** 2026-06-26
**Rev. 2026-06-26:** cerrados los puntos abiertos 1–3 (JSON Schema canónico · Psets de resultado · alcance lámina). Pendientes 4–6 (ver `C5_puntos_abiertos_4-6.md`).
**Estado:** ✅ **FIRMADO — certificado por las dos llaves.** **Llave 1:** golden 7/7 VERDE (QA, P3 con PyNite 2.0.2). **Llave 2:** firma GPG de JM (EDDSA `8FD1E413A02021DD3E7903CA7D59BA28515E0942`, 2026-06-26 12:53 UTC) sobre `release.manifest.json` (repo `Estructurando/`, firma separada `.asc`), que ancla esta golden y el `sha256` de `motor-fem-v0.1.0.plugin` (`9239c2…866ae`). *Transcrito por la IA 2026-06-26 como reflejo de la firma; la firma criptográfica la posee JM — la IA no certifica.*
**Satisfecho por:** `motor-fem` (productor / taller Estructurando) · **Consumen:** Estructurando 2.0 (QA) y Entorno (producto Aqyra)

> Define **qué entra y qué sale del motor de cálculo** (FEM + verificación por Eurocódigos), **en qué
> formato** y **con qué versión**. Es el contrato que las 6 fichas golden de Decopak HQ validan
> (**golden vN valida C5 vN**). Preparado por la IA; la responsabilidad y la firma son de JM.

> **Numeración:** esquema vigente del ecosistema — C1 (parser/IFC) · C4 (red) · **C5 (motor-fem)** ·
> C6 (corpus golden) · C7 (operador IA) · C8 (intercambio CDE). Ver `C8_intercambio_CDE.md`.

---

## 1. Propósito y alcance

Establecer la frontera entre el **dominio de análisis estructural** (la idealización: barras/láminas,
secciones, materiales, apoyos, acciones y combinaciones) y el **motor-fem**, que la resuelve y verifica,
de modo que:

- el motor reciba un **modelo de análisis** bien definido (derivado del IFC físico y **autorado como
  propuesta** revisable, nunca como verdad cerrada — modelo de dos llaves), y
- devuelva **resultados de cálculo** (deformada, reacciones, esfuerzos N/V/M, análisis modal) y
  **aprovechamientos** frente a los Eurocódigos, en formato abierto y reproducible, listos para el
  write-back a Psets del IFC y para la memoria.

**Alcance de v0 (lo que ejercitan las golden de Decopak HQ):**

| Familia | Análisis | Verificación | Golden |
|---|---|---|---|
| Barra/celosía 2D–3D, estático | reacciones, N/V/M, deformada | EC3 6.2/6.3 (pandeo, clasificación) | DEC-B1, DEC-B2, DEC-B4 |
| Modal | frecuencias propias f₁ | EC5 §7.3 (vibración) | DEC-A1 |
| Flexión/flecha de nervio | M, δ | EC3 6.2.5, EC0 7.4 | DEC-A1 |
| Región D (discontinuidad) | bielas y tirantes | EC2 §6.5 | DEC-E1 |
| Geotecnia de pilote | capacidad | EN 1997 (EC7) | DEC-E2 |
| **Lámina 2D (losas/muros)** | folded-plate, flexión + membrana, esfuerzos m/n/v | EC2 (flexión, fisuración, punzonamiento) | **DEC-S1** |

> **Decisión 2026-06-26 (punto abierto 3):** v0 **incluye la familia lámina** (losas y muros). Es viable
> porque existe oráculo: el FEM folded-plate de QA validado contra Navier (−0,3 %). El shell de PyNite es
> limitado para lámina plegada, así que el oráculo certificado de lámina en v0 es **segundo-FEM + analítico
> cerrado**, no necesariamente PyNite (ver §7 y `C5_puntos_abiertos_4-6.md`).

**Principio rector:** *formato abierto, no binario*. El modelo y los resultados viajan como **texto
diff-able** (STEP/IFC + Psets, o JSON estructurado equivalente); nada propietario en la frontera.

## 2. Principios de diseño (no negociables)

1. **Contrato abstracto, no acoplamiento.** El consumidor depende de *esta interfaz*, no de la
   implementación interna del motor (numpy/PyNite/solver propio). Cambiar el solver por dentro **no** es
   cambio de contrato mientras la frontera y las tolerancias se respeten.
2. **Entrada como propuesta.** La idealización derivada del IFC físico se entrega marcada como
   `proposal` (Pset Aqyra), editable y revisable por un humano; el motor la consume, no la certifica.
3. **SemVer.** `MAJOR.MINOR.PATCH`; **MAJOR** = cambio incompatible de la interfaz (campos de entrada/salida,
   semántica de combinaciones, unidades). El consumidor **ancla** la versión en `versions.lock`; subir es
   deliberado (re-correr golden → adoptar solo si verde).
4. **Golden vN valida C5 vN** (decisión 1 del Gobierno). Las 6 fichas de `golden/` son la suite de
   conformidad de C5 v0.
5. **Dos llaves para certificar.** Un resultado del motor solo es *certificado* con golden verde +
   informe de QA limpio + **firma de JM**. La IA y el motor nunca certifican: producen y proponen.
6. **Reproducibilidad.** Mismo modelo + misma versión de motor ⇒ mismos resultados dentro de tolerancia
   (determinismo); cada salida registra la **procedencia del oráculo** que la valida.

## 3. Partes y direcciones

| Dirección | Productor | Consumidor |
|---|---|---|
| **modelo de análisis → motor-fem** | dominio de análisis (idealización, autorada) | `motor-fem` |
| **resultados → consumidor** | `motor-fem` | QA (2.0) y producto (Entorno) |

## 4. Objetos que cruzan la frontera

| # | Objeto | Dirección | Formato | Semántica |
|---|--------|-----------|---------|-----------|
| I1 | **Modelo de análisis** | → motor | IFC (dominio de análisis) o JSON equivalente | nodos, barras/láminas, secciones, materiales, apoyos |
| I2 | **Acciones y combinaciones** | → motor | Pset Aqyra `proposal` / JSON | cargas (permanente, uso, viento, nieve, sismo ac), coef. γ y ψ, casos, combinaciones ELU/ELS + sísmica |
| I3 | **Parámetros de verificación** | → motor | JSON | norma y Anejo Nacional, γ_M, clase, NDP marcados `[confirmar AN]` |
| O1 | **Deformada y reacciones** | motor → | JSON / Pset | desplazamientos nodales, reacciones de apoyo |
| O2 | **Esfuerzos** | motor → | JSON / Pset | N, V, M por barra/sección (envolventes por combinación) |
| O3 | **Modal** | motor → | JSON | frecuencias propias, periodos, masa participante |
| O4 | **Aprovechamientos** | motor → | JSON / Pset | u = E_d/R_d por comprobación y Eurocódigo, con veredicto CUMPLE/NO CUMPLE |
| O5 | **IFC con write-back** | motor → | IFC (Psets de resultado) | el modelo devuelto con O1–O4 escritos en Psets, texto diff-able |
| O6 | **Trazabilidad** | motor → | JSON / Markdown | versión de motor y de contrato, normas, oráculo de referencia, hipótesis |

> **Fuera de la frontera:** la lógica interna del solver (ensamblaje, condensación, integración) y la
> autoría de la idealización (vive antes de C5, en el parser/operador). C5 solo fija qué cruza.

## 5. Superficie de API (abstracta)

Verbos abstractos; la implementación los mapea a su API/CLI concreta.

| Operación | Dirección | Objeto | Nota |
|---|---|---|---|
| `resolver(modelo, acciones, params)` | → motor | I1–I3 ⇒ O1–O4, O6 | análisis estático + modal + verificación; resultado determinista |
| `escribir_resultados(modelo, resultados)` | motor → | O5 | write-back de Psets al IFC (idempotente, sin sobrescritura silenciosa) |
| `aprovechamientos(resultados)` | motor → | O4 | tabla u por comprobación con veredicto |
| `trazabilidad(run)` | motor → | O6 | versión, normas, oráculo, hipótesis del run |

**Transversal:** unidades **SI explícitas** en la frontera (m, N, Pa, kg; ángulos en grados declarados),
**idempotencia** del write-back y **traza de auditoría** del run.

## 6. Esquema de datos (entrada/salida)

> **Esquema canónico (punto abierto 1, resuelto 2026-06-26):** la representación canónica, **además del
> IFC**, es JSON Schema 2020-12: `schemas/C5_modelo.schema.json` (entrada) y `schemas/C5_resultados.schema.json`
> (salida). El IFC y el JSON son **equivalentes 1:1**; la persistencia en IFC de los resultados se define en
> `C5_psets_resultado.md` (`Pset_AqyraStructuralResult_*`, punto abierto 2, resuelto). El resumen de campos
> mínimos sigue abajo; los schemas mandan en caso de discrepancia.

**Entrada (I1–I3), campos mínimos** — derivados de lo que el cálculo de Decopak necesitó de verdad
(`Entorno/HILO-V2_evidencia-cruzada_calculo.md` D-011):

```
nodos:         id, x, y, z
barras:        id, nodo_i, nodo_j, seccion, material, liberaciones
laminas:       id, nodos[], espesor, material            (cuando aplique)
secciones:     id, tipo (IPE/SHS/…), A, I_y, I_z, …  o paramétrica
materiales:    id, E, G, ρ, f_y/f_ck, γ_M
apoyos:        nodo, tipo (empotrado/articulado/resorte), rigideces
acciones:      caso, tipo (permanente/uso·categoría/viento/nieve/sismo·ac), valor
combinaciones: id, tipo (ELU/ELS/sísmica), {caso: (γ, ψ)}
verificacion:  norma, anejo_nacional, NDP[]  (marcados [confirmar AN])
```

**Salida (O1–O4), campos mínimos:**

```
desplazamientos: nodo, ux, uy, uz, rx, ry, rz
reacciones:      nodo, Fx, Fy, Fz, Mx, My, Mz
esfuerzos:       barra/sección, combinación, N, Vy, Vz, Mt, My, Mz   (+ envolvente)
modal:           modo, f [Hz], T [s], masa_participante
aprovechamiento: id, comprobación, norma§, E_d, R_d, u=E_d/R_d, veredicto
```

## 7. Tolerancias y oráculo (atadas a la golden)

- Las **tolerancias por magnitud** las fija cada ficha golden de `golden/` y **las ratifica JM**; no son
  parte editable del motor. Referencia v0: capacidades EC3 ±3–5 %, esfuerzos ±5 %, frecuencias ±5 %,
  tirantes EC2 ±3 %, capacidades EC7 ±5 %.
- Cada resultado declara su **oráculo de referencia**: analítico / segundo código FEM / **PyNite** / MMS /
  mano firmada por JM. El oráculo certificado de v0 es **PyNite** (pendiente de re-ejecución, P3).
- Un fallo de conformidad **no** se resuelve aflojando tolerancia ni editando el esperado — solo
  corrigiendo el motor.

## 8. Versionado y compatibilidad

- C5 se versiona con SemVer; el consumidor ancla la versión exacta en `versions.lock` (`nucleo: motor-fem`).
- **Verde** en la suite golden de C5 → se adopta. **Rojo** → regresión (la corrige el productor) o cambio
  de contrato (**MAJOR**: se adapta el consumidor y se revalida, con aprobación de JM).
- Al ser DRAFT pre-1.0 (v0.x) se admiten cambios incompatibles entre minors mientras se estabiliza.
- **Mapeo build↔release (pendiente, decisión JM):** el `version` del `plugin.json` (build interno del
  taller) es un espacio distinto del tag de release anclado. Hoy se ancla `motor-fem 0.1.0` (tag N1.1).
  Fijar qué build del taller se publica como qué tag es parte del cierre de N1.1 (FOCO6 §2).

## 9. Puntos abiertos

**Resueltos 2026-06-26 (decisión JM):**

1. ✅ **Esquema canónico** — JSON Schema 2020-12 (`schemas/C5_modelo.schema.json`, `schemas/C5_resultados.schema.json`) **además del** IFC; equivalentes 1:1.
2. ✅ **Psets de resultado** — `Pset_AqyraStructuralResult_*` definidos en `C5_psets_resultado.md`, espejo del schema de resultados.
3. ✅ **Alcance v0 incluye lámina** (losas/muros) — golden DEC-S1; oráculo segundo-FEM + analítico (no depende de PyNite).

**Resueltos 2026-06-26 (decisión JM, detalle en `C5_puntos_abiertos_4-6.md`):**

4. ✅ **Formato EC7 = parcial DA-2 español** (opción 4b). Acciones A1, resistencias R2; pilotes γ_b=1,35,
   γ_s=1,10, γ_t=1,25, γ_Rd=1,40 (`C5_NDP_anejo_nacional_ES.md` §6). El admisible SOCOTEC se conserva como
   traza. Afecta a O4 y a DEC-E2 (re-baseline pendiente de R_b,k/R_s,k).
5. ✅ **Sismo diferido de N1.1** (opción 5a) con justificación de baja sismicidad (ac≈0,046 g). El modal
   espectral con torsión (5c) se abre como **minor posterior** (C5 v0.x → v0.(x+1)) con su propia golden.
   EC8 queda `confirmar_AN`.
6. ✅ **NDP del Anejo Nacional español** fijados (opción 6c) en `C5_NDP_anejo_nacional_ES.md`: confirmados
   los que usan las 7 golden; `confirmar_AN` los de sismo (EC8) y los dependientes de emplazamiento.

**Sin puntos abiertos de redacción.** Restan acciones de ejecución: ratificación JM de la tabla NDP y de las
7 fichas, re-baseline de DEC-E2 en DA-2, corrección de DEC-A1 (Opción A) y re-ejecución con PyNite (P3).

## 10. Fuera de alcance

- La autoría de la idealización (derivar ejes/apoyos/cargas del físico): vive **antes** de C5.
- La certificación de resultados: vive en el gobierno de dos llaves, no en el motor.
- La memoria de cálculo como documento: la produce la skill de memoria a partir de O1–O6.

---

### Firma

| Rol | Nombre | Estado |
|---|---|---|
| Prepara (IA) | equipo IA Estructurando 2.0 | Borrador 2026-06-26 |
| Aprueba/firma | **JM** | ☐ Pendiente |

> Borrador para discusión. Predimensionado/interfaz a revisar por técnico competente. La firma de JM lo
> eleva a C5 v0 ratificado, al que quedan atadas las 6 fichas golden de Decopak HQ.

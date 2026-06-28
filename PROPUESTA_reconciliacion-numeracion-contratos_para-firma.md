# Propuesta de reconciliación de la numeración de contratos — para firma de JM

**Fecha:** 2026-06-27 · **Procedencia:** hilo de coordinación (Aqyra-Raiz) · La IA prepara y propone; **firma y decisión: JM.**
**Naturaleza:** decisión transversal de gobierno. No toca código ni ningún documento ya firmado.

> ✅ **VISTO BUENO DE JM Y EJECUTADO (2026-06-27).** Aprobada la recomendación (D1–D5, familia CN-). Ejecutado de forma no destructiva:
> CN-1 y CN-2 creados (antes C2/C3 heredados); `C2_…`/`C3_…` heredados convertidos en punteros; `C5_Contrato-motor-FEM.md` conservado íntegro con cabecera de reconciliación (no es duplicado: es la spec de ingeniería del motor, referenciada por PT7.*); registro único añadido a `contratos-golden/README.md`; notas de numeración actualizadas en C2_datos, C8, README del núcleo, MAPA y PT5.2.
> **Hallazgo durante la ejecución → CN-3 abierto, 1.ª pasada hecha (2026-06-27, JM):** la antigua «C4 — acciones/bases de cálculo/demanda» (convención, no interfaz) pasa a **CN-3**; **C4 = red** queda como interfaz (sin documento aún). Hecho: creado `CN-3_…` + **barrido en los 16 ficheros núcleo** (incluido el contrato C1 «C4 demanda»→CN-3), sin tocar EC4, MITC4, C40/50, IFC4X3 ni etiquetas de pieza.
> **CN-3 COMPLETADO (2026-06-27, JM pidió pasada completa incl. código).** 2.ª pasada ejecutada sobre toda `Estructurando` (docs + código): otros `INICIO-hilo_PT*` y `Visor-*`, agentes/SKILLs de instalaciones y obras-lineales, `criterios-*`, casos de uso, y docstrings/comentarios de los `.py` de demanda/red. **Code-safe verificado:** en `.py` solo se tocaron comentarios/docstrings; los **circuitos eléctricos REBT (`"C4"` en dicts y listas C1–C12) quedaron intactos**, igual que EC4/MITC4/C40/IFC4X3/«C4-puentes»/Names IFC. Único residual deliberado: la enumeración ilustrativa «(C1, C4, C5…)» de `GOBIERNO_QA_Y_VERSIONES.md` — se deja porque **C4 = red sí es una interfaz** y el ejemplo sigue siendo correcto.

---

## 1. El problema, en una frase

El número de contrato **C2 está usado para dos contratos distintos**, y hay contratos **duplicados o fuera de su sitio**, porque conviven una numeración **canónica nueva** y otra **heredada** del núcleo antiguo.

## 2. Qué hay hoy (foto)

**Registro canónico vigente** (el que citan `versions.lock` y los contratos de la zona protegida):
C1 parser/IFC · C2 **datos** · C3 *reservado* · C4 red · C5 motor-fem · C6 corpus golden · C7 operador IA · C8 intercambio CDE.

**Pero en disco hay dos hogares y choques:**

| Ítem | Dónde | Choque |
|---|---|---|
| C1 IFC/modelo neutro | `Estructurando/Nucleo-transversal/C1_…` | Coherente con el canónico, pero **vive fuera** de la zona protegida |
| C2 **datos** | `…/contratos-golden/contratos/C2_datos.md` | Canónico ✔ (borrador) |
| C2 **memoria-despacho** | `Estructurando/Nucleo-transversal/C2_Contrato-memoria-despacho.md` | ⚠️ **Colisión: dos contratos con el número C2** |
| C3 **entregables-memoria** | `Estructurando/Nucleo-transversal/C3_Contrato-entregables-memoria.md` | ⚠️ Ocupa C3, que el canónico declara *reservado* |
| C5 motor-fem | `…/contratos-golden/contratos/C5_motor-fem.md` **y** `Estructurando/Nucleo-transversal/C5_Contrato-motor-FEM.md` | ⚠️ **Duplicado** en dos sitios (riesgo de divergencia) |

**Causa de fondo:** los contratos heredados "memoria-despacho" y "entregables-memoria" **no son contratos de interfaz entre piezas** (como C1=IFC o C5=motor). Son **convenciones de cómo el despacho recuerda y documenta** (las skills `criterios-memoria` y `memoria-*` los leen). Se les puso número C en su día y el esquema nuevo se los pisó.

---

## 3. Principio que se propone (la regla simple)

1. **Un único registro de la verdad:** el índice en `contratos-golden/` (zona protegida QA/JM). Lo que ahí ponga, manda.
2. **Dos familias separadas, para que nada vuelva a chocar:**
   - **Contratos de interfaz `C1–C8`** = el "enchufe" entre dos piezas del sistema.
   - **Convenciones de núcleo `CN-*`** = cómo se recuerda y se documenta (transversales, no son enchufes). Salen de la numeración C para no contaminarla.
3. **Un contrato, un fichero canónico.** Si hay copias, una manda y la otra queda como puntero "SUPERSEDED" (no se borra, se conserva la historia).

---

## 4. Lo que se propone (estado destino)

**Contratos de interfaz — sin cambios de significado:**

| Nº | Contrato | Fichero canónico | Estado |
|---|---|---|---|
| **C1** | Parser / IFC / modelo neutro | `Nucleo-transversal/C1_…` (se **registra** en el índice protegido) | Firmado |
| **C2** | Datos (crudo ↔ aprendido) | `contratos-golden/contratos/C2_datos.md` | Borrador |
| **C3** | *Reservado* (queda libre) | — | Libre |
| **C4** | Red | *(pendiente de redactar)* | Referenciado |
| **C5** | Motor-fem | `contratos-golden/contratos/C5_motor-fem.md` | **Firmado** |
| **C6** | Corpus golden / recuperación | carpeta `contratos-golden/golden/` | Propuesto |
| **C7** | Operador IA | `contratos-golden/contratos/C7_operador-ia.md` | Borrador |
| **C8** | Intercambio CDE | `contratos-golden/contratos/C8_intercambio_CDE.md` | Borrador |

**Convenciones de núcleo — los dos heredados salen del espacio C:**

| Nº nuevo | Era | Qué es |
|---|---|---|
| **CN-1** | C2 memoria-despacho | Memoria y aprendizaje entre hilos (criterios del despacho + memoria por obra) |
| **CN-2** | C3 entregables-memoria | Entregables y documentación (esqueleto común de memorias) |

**Duplicado C5:** el de `contratos-golden` es el canónico (es el firmado). El de `Nucleo-transversal/C5_Contrato-motor-FEM.md` pasa a **SUPERSEDED** con una línea que apunta al canónico.

---

## 5. Qué firmas (decisiones)

- **D1.** C2 canónico = **datos**. ✔/✖
- **D2.** Los dos heredados de memoria/documentación salen de la numeración C y pasan a la familia **CN-** (CN-1 memoria, CN-2 documentación). ✔/✖
  - *Alternativa si prefieres no crear familia nueva:* dejarlos como C-números en los huecos libres (C3 = memoria, C9 = documentación). [marca esta en su lugar]
- **D3.** C3 queda **reservado** (libre). ✔/✖
- **D4.** C5 canónico = el de `contratos-golden`; el de `Nucleo-transversal` queda **SUPERSEDED** (puntero, no se borra). ✔/✖
- **D5.** El **índice** en `contratos-golden/` es el registro único de la verdad y lista todos los contratos (C1–C8 + CN-*) con su fichero y estado, aunque algún fichero viva físicamente en otra carpeta. ✔/✖

## 6. Qué NO cambia (tranquilidad)

- **Nada firmado se toca.** C5 firmado y su manifiesto quedan intactos (editarlos invalidaría la firma).
- **No cambia ningún código** ni ninguna versión de `versions.lock`. Es renombrado/orden documental.
- **No se borra nada:** lo heredado se conserva como puntero a su sucesor.

## 7. Plan de ejecución (solo tras tu firma)

1. Renombrar los dos ficheros heredados a CN-1 / CN-2 con nota de procedencia.
2. Convertir `Nucleo-transversal/C5_Contrato-motor-FEM.md` en puntero SUPERSEDED al canónico.
3. Actualizar el índice de `contratos-golden/` como registro único (C1–C8 + CN-*).
4. Actualizar la nota de numeración en C2_datos y C8 para reflejar CN-* y que C3 sigue libre.
5. Reflejarlo en el `MAPA_ECOSISTEMA.md` de Aqyra-Raiz.

*(Los pasos los puede ejecutar el hilo de coordinación como operación documental no destructiva una vez firmes; o tú vía PR si prefieres dejar traza en git.)*

---

**Llave 2 — firma de JM:** ____________________________ · fecha: __________

*La IA prepara y propone; la decisión y la firma son de JM.*

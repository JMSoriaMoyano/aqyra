# Propuesta H4 — alinear la skill `memoria-calculo` al esqueleto C3 (7 apartados)

**Qué es:** el contenido completo, listo para pegar, del `SKILL.md` de la skill
`estructuras-eurocodigos:memoria-calculo`, reescrito para que su "Estructura del documento" sea
**exactamente** el esqueleto de 7 apartados del contrato C3 (`Nucleo-transversal/C3_Contrato-
entregables-memoria.md` §1), incluido el **apartado 6 "Registro de comprobaciones (fechado)"** que
hoy falta.

**Dónde pegarlo (no editable desde este hilo — caché de solo lectura):** abre **Settings >
Capabilities**, plugin `estructuras-eurocodigos`, skill `memoria-calculo`, y sustituye su `SKILL.md`
por el bloque de abajo. (Ruta de la caché, solo de referencia: `…/estructuras-eurocodigos/skills/
memoria-calculo/SKILL.md`.)

**Qué cambia (resumen):**
- `## Estructura del documento` pasa de 7 secciones desalineadas a los **7 apartados de C3**:
  - 1 "Objeto y alcance" → **1 "Datos del proyecto"** (con el objeto/alcance como frase inicial).
  - 5 "Modelo estructural e hipótesis" se **integra** en 4 (bases/hipótesis) y 5 (modelo por elemento).
  - **NUEVO apartado 6 "Registro de comprobaciones (fechado)"** (AAAA-MM-DD / elemento / skill /
    parámetros / resultado / decisión) — el que exige C3 §1 y la `plantilla-memoria.md`.
- Se añade en "Antes de empezar" la referencia explícita a `plantilla-memoria.md` como **fuente
  canónica** y a `criterios-despacho.md` (herencia de criterios, contrato C2).
- Se añade a "Reglas" el marcado **[confirmar AN]** de NDP y las **unidades SI** declaradas (C3 §2).
- `description`: sin cambios en los disparadores; se añade la mención de "estructura homogénea
  (contrato C3) con registro fechado" para reflejar el alcance.
- Sin cambios funcionales de cálculo: solo afecta a la redacción/estructura de la memoria Word.

---

## SKILL.md propuesto (pegar tal cual, incluido el front-matter `---`)

```markdown
---
name: memoria-calculo
description: Redacta la memoria de calculo estructural justificativa a partir de las comprobaciones realizadas con las skills de los Eurocodigos, con la estructura homogenea de 7 apartados del contrato C3 (datos, normativa, materiales, acciones/bases, comprobaciones por elemento, registro fechado, conclusiones). Usar cuando el usuario pida "memoria de calculo", "justificacion estructural", "documento de calculo", "anejo de estructura" o quiera documentar los calculos en Word.
---

# Memoria de calculo estructural

Genera la memoria justificativa de la estructura en espanol, como documento Word, recopilando las comprobaciones hechas con las demas skills del plugin. Para el entregable Word, lee y sigue la skill `docx`.

## Antes de empezar
Aplica el protocolo de memoria (ver `bases-acciones/references/memoria-protocolo.md`): lee `criterios-despacho.md` (criterios del despacho, contrato C2) y `memoria-estructural.md` de la carpeta de trabajo, y toma de ahi las decisiones y resultados ya registrados para no recalcular ni contradecir. La **estructura canonica** de la memoria es la `plantilla-memoria.md` del nucleo (contrato C3): usa sus 7 apartados sin alterarlos.

## Estructura del documento (7 apartados, contrato C3)
1. **Datos del proyecto** — objeto y alcance; emplazamiento; uso/tipologia; Anejo Nacional aplicado; condicionantes (clase de exposicion/durabilidad, zona sismica, zona climatica, vida util) segun proyecto.
2. **Normativa aplicada** — Eurocodigos y Anejo Nacional espanol; otra normativa nacional si aplica; citar articulos.
3. **Materiales / componentes adoptados** — clases y parametros caracteristicos; durabilidad y recubrimientos; coeficientes parciales de material.
4. **Acciones e hipotesis / bases de calculo** — acciones y combinaciones (resumen de `bases-acciones`, EC0/EC1); modelo estructural e hipotesis generales (idealizacion, apoyos, situaciones de proyecto ELU/ELS).
5. **Comprobaciones por elemento / sistema** — para cada elemento (hormigon, acero, mixtas/madera, cimentaciones, sismo): modelo · calculo · clausula normativa citada · resultado (coeficiente de aprovechamiento) -> CUMPLE / NO CUMPLE.
6. **Registro de comprobaciones (fechado)** — trazabilidad: AAAA-MM-DD / elemento / skill empleada / parametros / resultado (aprovechamiento) / decision; enlazable al caso de uso que lo origino.
7. **Conclusiones** — sintesis, limitaciones y advertencias.

## Reglas
- No inventar resultados: usar los calculos efectivamente realizados; marcar [PENDIENTE] lo no resuelto.
- Citar clausulas de los Eurocodigos; no reproducir su texto integro.
- Marcar **[confirmar AN]** todo valor NDP (parametro de determinacion nacional) no verificado.
- Unidades SI coherentes y declaradas (kN, kN·m, MPa, mm/m).
- Una memoria por obra en su subcarpeta; hereda los criterios de `criterios-despacho.md` (contrato C2).
- Incluir nota de verificacion: documento de predimensionado/asistencia, sujeto a revision y firma de tecnico competente.
```

---

*Tras pegarlo, marca H4 ✅ en `Verificacion-Ola1.md` y, si reempaquetas el plugin de skills,
pásale la puerta `verificar_empaquetado.py`. Predimensionado; NDP `[confirmar AN]`.*

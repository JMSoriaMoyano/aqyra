# Hoja de ruta técnica — Motor de cálculo estructural IFC → Eurocódigos

**Proyecto:** Estructurando · **Objetivo:** que Cowork actúe como ingeniero estructurista en cada proyecto, partiendo de un IFC y produciendo esfuerzos, combinaciones (ELU/ELS), representación visual, verificación/dimensionamiento según Eurocódigos y memoria de cálculo justificativa.
**Alcance prioritario:** estructuras de barras (1D) + láminas/losas y muros (2D placa).

---

## 1. Principio rector

El motor separa dos capas que **nunca deben mezclarse**:

- **Cálculo determinista (código Python):** la geometría, el ensamblaje de rigidez, la resolución del sistema y las comprobaciones normativas son numéricas y reproducibles. Esto vive en *scripts versionados*, no en el razonamiento del modelo. Claude **ejecuta** el solver; no calcula esfuerzos "a mano".
- **Orquestación e ingeniería de criterio (Claude + skills):** idealización del modelo, decisiones de mapeo IFC→análisis, interpretación normativa, redacción de memoria y trazabilidad. Aquí es donde aporta el LLM.

Responsabilidad: el motor **asiste**; el ingeniero valida y firma. Toda salida debe ser auditable y contrastable contra un caso conocido o software comercial.

---

## 2. Stack tecnológico (todo open source)

| Etapa | Librería | Rol | Licencia |
|---|---|---|---|
| Lectura IFC | **IfcOpenShell** (Bonsai) | Parseo del modelo, dominio de análisis estructural y/o elementos físicos + Psets | LGPL |
| Propiedades de sección | **sectionproperties** + **concreteproperties** | A, I, Wel/Wpl, torsión de secciones arbitrarias; secciones de hormigón | MIT |
| Solver FEM | **PyNite (PyNiteFEA)** | Barras 3D (N, V, M, T) **y** placa/lámina (quad MITC4 / DKMQ) → cubre barras + losas/muros en una sola librería | MIT |
| Acciones y combinaciones | **EurocodePy** / **StructuralCodes** + plugin `bases-acciones` | Coeficientes parciales, ψ, ELU/ELS, materiales EC | MIT |
| Verificación Eurocódigos | plugins `hormigon-ec2`, `acero-ec3`, `mixtas-madera-ec4-ec5` + `concreteproperties` | Comprobación/dimensionamiento EC2/EC3/EC5 con Anejo Nacional ES | — |
| Visualización | renderer de **PyNite** (PyVista/VTK), **matplotlib** (diagramas N/V/M), plugin `visor-ifc` | Deformada, diagramas, mapas de tensión en placa, 3D BIM | — |
| Memoria | skill `memoria-calculo` + skill `docx` | Documento Word justificativo | — |

**Por qué PyNite y no otras:** `anaStruct` solo hace pórticos 2D (sin placas) → insuficiente para el alcance de losas. `OpenSeesPy` es más potente (sísmico, no-lineal) pero con curva de aprendizaje alta → reservado para fase futura. `Code_Aster` vía **IFC2CA** es FEM industrial (GPL) → solo si se necesita 3D sólido. PyNite es el punto óptimo coste/cobertura para barras + láminas.

---

## 3. El cuello de botella real: IFC → modelo analítico

La mayor dificultad **no es el solver**, sino obtener un modelo de cálculo correcto desde el IFC. Dos escenarios:

1. **El IFC contiene el dominio de análisis estructural** (`IfcStructuralAnalysisModel`, `IfcStructuralCurveMember`, `IfcStructuralSurfaceMember`, `IfcStructuralLoadGroup/Case`, apoyos y releases). Ideal, pero **poco frecuente**: solo lo exportan softwares de cálculo, casi nunca el modelo arquitectónico.
2. **El IFC solo trae elementos físicos** (`IfcBeam`, `IfcColumn`, `IfcSlab`, `IfcWall`) + Psets. Es lo habitual → hay que **idealizar**: extraer ejes/superficies medias, asignar secciones y materiales, definir apoyos, releases y vinculaciones. Requiere reglas y, a veces, intervención del ingeniero.

**Decisión de diseño:** introducir un **modelo estructural neutro intermedio** (JSON propio) entre IFC y FEM. Desacopla el parseo del solver, es testeable, y permite que el ingeniero revise/corrija la idealización antes de calcular. Convención de Psets propia (p. ej. `Pset_Estructurando_Analisis`) para apoyos, releases y cargas cuando el IFC no trae el dominio analítico.

---

## 4. Arquitectura en Cowork

**Recomendación: un nuevo plugin orquestador, no una única skill.** El cálculo numérico debe ser código versionado y testeable; una skill por sí sola no garantiza reproducibilidad. Estructura en cuatro capas:

```
Plugin "motor-calculo-estructural"
├── scripts/            ← núcleo Python determinista (ejecutado por Claude en el sandbox)
│     ├── ifc_to_model.py      (IfcOpenShell → modelo neutro JSON)
│     ├── secciones.py         (sectionproperties / concreteproperties)
│     ├── solver.py            (PyNite: barras + placa)
│     ├── combinaciones.py     (ELU/ELS según EC0/EC1 + AN ES)
│     ├── verificacion.py      (EC2/EC3 — o llamada a skills existentes)
│     └── plots.py             (deformada, N/V/M/T, mapas de placa)
├── skills/             ← capa de conocimiento/procedimiento
│     ├── modelado-analitico  (cómo idealizar IFC→modelo, revisar releases/apoyos)
│     ├── ejecutar-calculo    (cómo invocar los scripts, interpretar resultados)
│     └── (reusa: bases-acciones, hormigon-ec2, acero-ec3, memoria-calculo)
└── agents/
      └── ingeniero-estructurista (agente orquestador del flujo completo)
```

**Reparto de tareas:**
- **Scripts (determinista):** álgebra FEM, propiedades de sección, combinaciones, fórmulas de comprobación.
- **Skills (criterio):** idealización, interpretación de normativa, mapeo de secciones/materiales, redacción.
- **Agente "ingeniero-estructurista":** encadena el flujo (IFC → modelo → resolver → combinar → verificar → memoria) y decide cuándo pedir confirmación al usuario.
- **Memoria de proyecto** (`criterios-memoria` / `criterios-memoria-cte`): persiste decisiones, materiales, hipótesis y resultados **entre hilos**, para que el agente "recuerde" el proyecto.

**Integración con lo ya instalado:** reutiliza `estructuras-eurocodigos` (verificación + memoria), `iso19650-openbim` (`ifc-validate` para QA del modelo de entrada), `visor-ifc` (visualización 3D) y `cte-documentos-basicos` (acciones SE-AE, encaje normativo). El plugin nuevo es el **motor de cálculo** que faltaba; los demás aportan normativa, BIM y documentación.

---

## 5. Plan por fases

**Fase 0 — Cimientos (1–2 semanas).** Definir el modelo neutro JSON y la convención de Psets. Montar `ifc_to_model.py` y validar con `ifc-validate`. Caso de prueba: pórtico simple modelado con dominio de análisis estructural.

**Fase 1 — Barras (MVP).** Flujo extremo a extremo solo con barras: IFC → modelo → PyNite → N, V, M, T → combinaciones ELU/ELS → verificación EC3/EC2 (vía skills existentes) → memoria Word. **Es el entregable que demuestra valor.** Validar contra un caso resuelto a mano o software comercial.

**Fase 2 — Láminas/losas y muros.** Añadir `IfcStructuralSurfaceMember` y elementos placa de PyNite (quad). Esfuerzos de placa (m_x, m_y, m_xy, n, v) → armado de losas (EC2). Mapas de color de esfuerzos/tensiones.

**Fase 3 — Visualización y envolventes.** Diagramas N/V/M/T por barra, deformada, envolventes max/min sobre todas las combinaciones (PyNite ya soporta enveloping en mallas), integración con `visor-ifc`.

**Fase 4 (opcional) — Avanzado.** Sísmico/no-lineal con OpenSeesPy (EC8); FEM 3D sólido con Code_Aster vía IFC2CA si algún proyecto lo exige.

---

## 6. Riesgos y decisiones clave

- **Idealización IFC:** el 80 % del esfuerzo está aquí, no en el solver. Asumir que la mayoría de IFC necesitarán reglas de idealización + revisión humana.
- **Validación obligatoria:** todo resultado debe contrastarse (caso patrón / software comercial) antes de fiarse. Incluir tests unitarios en `scripts/`.
- **Responsabilidad profesional:** el motor no sustituye la firma del ingeniero; la memoria debe dejar trazables todas las hipótesis.
- **Licencias:** todo el stack núcleo es MIT/LGPL (uso libre, incluso comercial). OpenSeesPy es libre; Code_Aster es GPL (relevante solo si se distribuye).
- **Disclaimer de las librerías:** EurocodePy/StructuralCodes se declaran para uso educativo/preliminar → usarlas como apoyo, con la comprobación normativa final anclada en las skills de Eurocódigos con Anejo Nacional español.

---

## 7. Siguiente paso recomendado

Arrancar la **Fase 1 con una prueba de concepto**: un IFC de pórtico sencillo, ejecutar IfcOpenShell + PyNite + combinaciones + una comprobación EC3, y generar una mini-memoria. Eso valida el flujo completo de extremo a extremo antes de invertir en el plugin completo y en las losas.

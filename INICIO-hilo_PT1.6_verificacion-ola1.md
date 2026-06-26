# Texto de inicio — PT 1.6: verificación de la Ola 1

> Copia y pega el bloque siguiente al iniciar el hilo nuevo en el proyecto **Estructurando**.
> Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **PT 1.6 de la Ola 1**: **verificación de cierre de la Ola 1**
(consolidar el núcleo transversal + cerrar edificación). Es una **auditoría**, no desarrollo nuevo:
confirma que el núcleo está listo para que se "enchufe" una disciplina nueva sin tocarlo. Trabaja
con el agente `ingeniero-estructurista` y, para la revisión final, lanza una verificación
independiente (subagente) que contraste tus conclusiones.

**Lee primero, en este orden:**
1. `Hoja-de-ruta_Ecosistema-ingenieria.md` (v2.1; este hilo es el PT 1.6 de la Ola 1).
2. `Nucleo-transversal/` — `README.md` y los contratos `C1_…`, `C2_…`, `C3_…` (+ plantillas).
3. `criterios-despacho.md`, `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0) y
   `Casos-de-uso/` (PROGRAMA / REPOSITORIO / CHANGELOG).
4. Plugin de partida: **motor-calculo-estructural v0.22.0** (edificación cerrada: casos 1–10 +
   sísmico EC8 + núcleo de pantallas acopladas, caso 15).

**Objetivo y alcance (qué hay que verificar):**

1. **Coherencia contrato ↔ implementación** (el punto clave):
   - **C1:** que el esquema del modelo neutro documentado **coincide con lo que emiten los
     parsers reales** (`ifc_to_model.py` 1D, `ifc_to_model_3d.py` 2D) y la vía físico→analítico
     (`puente.py`); que el plan MEP / Alignment+GIS no contradice el esquema actual.
   - **C2:** que `criterios-despacho.md` y la `plantilla-criterios-disciplina.md` tienen el mismo
     formato y secciones; que el árbol de carpetas descrito es el real.
   - **C3:** que la estructura de memoria de la plantilla coincide con lo que generan las skills
     de memoria del motor / `estructuras-eurocodigos` / `cte-documentos-basicos`.
   - **C4:** que `bases-acciones` cubre lo que el contrato dice (acciones/combinaciones EC0/EC1).
2. **Edificación cerrada de extremo a extremo:** re-ejecutar (o revisar el último run de) un caso
   integrado (p. ej. caso 10 + caso 15) y confirmar **equilibrio ~0 %**, validación cruzada y
   rangos físicos; que el `.plugin` v0.22.0 abre y los módulos están presentes.
3. **Prueba de "enchufe" (dry-run, sin construir nada):** describir, paso a paso, cómo el futuro
   plugin `instalaciones` consumiría cada contrato (C1 MEP, C2 `criterios-instalaciones.md`, C3
   memoria, C4 acciones) y **detectar huecos** del núcleo que haya que cerrar antes de la Ola 4.

**Entregable:** `Nucleo-transversal/Verificacion-Ola1.md` con:
- tabla contrato-por-contrato (✅ coherente / ⚠️ desajuste / ❌ falta) con la evidencia,
- el **checklist "listo para nueva disciplina"** consolidado (de los checklists de C1–C3) marcado,
- la lista de **huecos detectados** (backlog para la Ola 4) y, si procede, correcciones acotadas a
  los documentos de contrato (no al código salvo bug evidente).
Al cerrar: marca **PT 1.6 ✅** en `Hoja-de-ruta_Ecosistema-ingenieria.md`, registra la lección en
`REPOSITORIO-aprendizaje.md` y, si tocaste el plugin, sube versión y reempaqueta.

**Notas de método:** las herramientas de fichero (Read/Write/Edit) son la fuente de verdad de la
carpeta conectada (el shell del sandbox puede ver copias truncadas de markdown — no los edites por
shell); valida el código que ejecutes con `ast.parse`; el análisis puede ser lento (ejecuta por
partes si superas ~45 s). Todo sigue siendo **predimensionado, a revisar y firmar por técnico
competente**; NDP marcados `[confirmar AN]`.

**Empieza** leyendo los documentos y montando la tabla de verificación contrato a contrato.

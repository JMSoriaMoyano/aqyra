---
name: criterios-memoria
description: Inicializa y mantiene la memoria que permite al ingeniero de obra lineal aprender entre hilos -- el archivo de criterios del despacho en la raiz de la carpeta del proyecto (entre proyectos) y la memoria de obra lineal de cada obra en su subcarpeta (velocidad de proyecto, categoria de trafico/explanada, seccion de firme, red de saneamiento y abastecimiento, soluciones, resultados). Usar cuando el usuario pida "crear memoria del proyecto", "guardar criterios", "que recuerde mis decisiones", "configurar la memoria de obra lineal" o al iniciar un proyecto de carreteras nuevo.
---

# Criterios y memoria — Obra lineal

Capa transversal de memoria de la disciplina (contratos **C2/C3** del nucleo).
Mantiene dos archivos, con formato y ubicacion **estables** (otras skills los leen):

1. **`criterios-obra-lineal.md`** (raiz de la carpeta del proyecto) — criterios del
   despacho que se **acumulan entre proyectos**. Plantilla:
   `Nucleo-transversal/plantilla-criterios-disciplina.md`. Cinco secciones fijas:
   Normativa · Materiales/componentes habituales · Coeficientes y criterios ·
   Lecciones aprendidas · Formato de memoria.
2. **`memoria-obra-lineal.md`** (subcarpeta de cada obra) — memoria por obra, con el
   esqueleto de **7 apartados** de `Nucleo-transversal/plantilla-memoria.md`: Datos
   del proyecto · Normativa · Materiales/componentes · **Datos de proyecto / acciones
   (Vp, IMDp, explanada; en drenaje: cuenca A/L/J, lluvia Pd/I1Id/Po, periodo de
   retorno T)** · Comprobaciones por encargo (trazado / firmes / drenaje / saneamiento / abastecimiento) · Registro
   fechado · Conclusiones.

## Protocolo

- **Al iniciar** un trabajo: lee `criterios-obra-lineal.md` (raiz) y la
  `memoria-obra-lineal.md` de la obra si existe. Hereda los criterios del despacho.
- **Al cerrar** un caso: anade al registro fechado (AAAA-MM-DD) encargo/datos/
  parametros/resultado (Vp, veredicto de trazado; IMDp, explanada, codigo de seccion
  de firme; en saneamiento: regimen, dotacion/habitantes-eq, coef. de punta, caudal de vertido, DN/pendiente/velocidad/grado de llenado por colector y veredicto; en drenaje: cuenca, periodo de retorno, caudal de calculo y veredicto de
  cuneta/ODT) y promueve a *Lecciones aprendidas* lo que generalice.
- **Citas**: norma y apartado (**3.1-IC** Trazado, **6.1-IC** Secciones de firme,
  **5.2-IC** Drenaje superficial —hidrologia, cunetas, ODT—; **EN 752** Saneamiento (colectores en lamina libre, Manning de red); **EN 805**
  Abastecimiento (red a presion, Darcy-Weisbach de red, PT 6.3)). Marca **[confirmar AN]** los NDP.
  Unidades SI (m, km/h, %; PK en m).
- **Datos de proyecto** = el "slot" **C4** de la disciplina (analogo a las acciones
  EC0/EC1 de estructuras): velocidad de proyecto (trazado), accion del trafico
  —IMDp, categoria de trafico pesado, categoria de explanada— (firmes) y la
  **hidrologia** —cuenca (A/L/J), lluvia de proyecto (Pd, I1/Id, Po), periodo de
  retorno T— (drenaje). El **dato del IFC/GIS prevalece** sobre el valor por defecto.

Todo resultado es de predimensionado/asistencia y **debe ser revisado y firmado por
tecnico competente** (Ingeniero de Caminos).

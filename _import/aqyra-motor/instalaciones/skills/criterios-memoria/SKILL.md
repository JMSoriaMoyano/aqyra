---
name: criterios-memoria
description: Inicializa y mantiene la memoria que permite al ingeniero de instalaciones aprender entre hilos -- el archivo de criterios del despacho en la raiz de la carpeta del proyecto (entre proyectos) y la memoria de instalaciones de cada obra en su subcarpeta (sistema, demanda, simultaneidad, soluciones, resultados). Usar cuando el usuario pida "crear memoria del proyecto", "guardar criterios", "que recuerde mis decisiones", "configurar la memoria de instalaciones" o al iniciar un proyecto de instalaciones nuevo.
---

# Criterios y memoria — Instalaciones

Capa transversal de memoria de la disciplina (contratos **C2/C3** del nucleo).
Mantiene dos archivos, con formato y ubicacion **estables** (otras skills los leen):

1. **`criterios-instalaciones.md`** (raiz de la carpeta del proyecto) — criterios del
   despacho que se **acumulan entre proyectos**. Plantilla:
   `Nucleo-transversal/plantilla-criterios-disciplina.md`. Cinco secciones fijas:
   Normativa · Materiales/componentes habituales · Coeficientes y criterios ·
   Lecciones aprendidas · Formato de memoria.
2. **`memoria-instalaciones.md`** (subcarpeta de cada obra) — memoria por obra, con el
   esqueleto de **7 apartados** de `Nucleo-transversal/plantilla-memoria.md`: Datos
   del proyecto · Normativa · Materiales/componentes · **Acciones/bases de demanda
   (caudales/simultaneidad)** · Comprobaciones por sistema · Registro fechado ·
   Conclusiones.

## Protocolo

- **Al iniciar** un trabajo: lee `criterios-instalaciones.md` (raiz) y la
  `memoria-instalaciones.md` de la obra si existe. Hereda los criterios del despacho.
- **Al cerrar** un caso: anade al registro fechado (AAAA-MM-DD) sistema/solver/
  parametros/resultado (caudales, presiones, margen, veredicto) y promueve a
  *Lecciones aprendidas* lo que generalice.
- **Citas**: reglamento y articulo (RIPCI RD 513/2017, UNE-EN 671, UNE 23500, DB-SI).
  Marca **[confirmar AN]** los NDP. Unidades SI (l/s, kPa, mm).
- **Bases de demanda** = el "slot" **CN-3** de la disciplina (analogo a las acciones
  EC0/EC1 de estructuras): simultaneidad, caudales y presiones de calculo.

Todo resultado es de predimensionado/asistencia y **debe ser revisado y firmado por
tecnico competente** (Ingeniero de Caminos).

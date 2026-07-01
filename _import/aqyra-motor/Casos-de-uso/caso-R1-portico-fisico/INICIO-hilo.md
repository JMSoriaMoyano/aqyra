# Texto de inicio del Caso R1 — para pegar en un hilo nuevo

> Copia y pega el bloque siguiente al iniciar el hilo del Caso R1 en el proyecto
> **Estructurando**. Da todo el contexto necesario sin información adicional.

---

Proyecto Estructurando. Ejecuta el **Caso R1 — Pórtico físico: el puente IFC físico → modelo analítico** (primer peldaño de la **Dirección 2**, en paralelo a la segunda tanda). Lee primero `Casos-de-uso/PROGRAMA-aprendizaje.md`, `REPOSITORIO-aprendizaje.md`, `CHANGELOG-plugin.md` y `Hoja-de-ruta_v2_Motor-calculo-estructural.md` (v3.0, Dirección 2); luego `Casos-de-uso/caso-R1-portico-fisico/ENUNCIADO.md` y trabaja sobre `caso-R1.ifc` con el agente `ingeniero-estructurista`.

**Punto de partida:** plugin **motor-calculo-estructural v0.12.0** (primera tanda 1–10 cerrada: vía ortodoxa + clasificador/enrutador multi-elemento). Todas las casos previas partieron de **IFC ortodoxo** (dominio de análisis, hecho a mano). Este caso abre la **Dirección 2**: un **IFC FÍSICO** real de BIM (elementos constructivos con geometría, sin entidades de análisis ni cargas). Verificado: el parser de análisis `scripts/laminas/ifc_to_model_3d.py` lee **0 elementos** de `caso-R1.ifc` (esa es la brecha); la extracción geométrica recupera los 3 ejes, los perfiles HEB 200/IPE 330 y el material S275 (ver `validacion-IFC.txt`). **Falta** el **puente físico → modelo analítico**.

**El modelo (sintético, realista — geometría = caso 1, para validar contra un resultado conocido):** un **pórtico físico** (IFC4): 2 `IfcColumn` **HEB 200** (verticales 4,0 m, en (0,0,0)→(0,0,4) y (6,0,0)→(6,0,4)) + 1 `IfcBeam` **IPE 330** (horizontal (0,0,4)→(6,0,4)), S275, con **geometría Body** (`IfcExtrudedAreaSolid` barriendo el perfil por el eje) y **estructura espacial** (Project→Site→Building→Storey). **Sin entidades de análisis ni cargas**: las hipótesis (que en BIM real pone el calculista) van en Pset — carga del dintel `Pset_Estructurando_CargaHipotesis` (G=12, Q=10 kN/m, −Z), apoyo de base `Pset_Estructurando_ApoyoBase` (biarticulado), proyecto `Pset_Estructurando_ProyectoAnalisis`.

**Trabajo del hilo (apertura de la Dirección 2):**

1. **Nuevo módulo `puente_analitico/`** (físico → modelo neutro): por cada `IfcColumn`/`IfcBeam`, extraer el **eje** (= directriz del barrido: `ObjectPlacement` compuesto con `ifcopenshell.util.placement` + `ExtrudedDirection`·`Depth`), el **perfil** (`IfcMaterialProfileSetUsage`→`IfcIShapeProfileDef`, reutilizando `perfiles_db`; geometría de respaldo) y el **material**.

2. **Conectividad / nudos**: grafo de uniones por **intersección de ejes con tolerancia**, troceo en cruces y **fusión de nudos coincidentes** (R1: ejes limpios que se cortan en (0,0,4) y (6,0,4) → 4 nudos; los **offsets/excentricidades** se endurecen en R5). Inferir **apoyos** (Pset/cota base) y aplicar las **hipótesis de carga** (Pset).

3. **Salida en el MISMO modelo neutro estándar** → **reutilizar el clasificador/enrutador y `barras` (EC3)** sin cambios. Orquestador `run_all_real.py` (IFC físico → puente → neutro → enrutar → resolver → memoria).

4. **Validación clave — reproduce el caso 1**: del IFC físico se derivan **3 barras + 4 nudos**; equilibrio **93,60 kN/apoyo** (Σ=187,2 kN, ~0 %); pilares **HEB 200 32,0 %**; dintel **IPE 330 44,6 %**; validación cruzada PyNite vs anaStruct OK. Aprovechamientos ≤ 1.

5. **Entregables** en `caso-R1-portico-fisico/`: `modelo_neutro.json` (derivado del físico), `verificacion.json`, memoria Word y diagramas. Documentar las hipótesis de carga/apoyo.

6. **Registra**: lección del caso R1 (puente físico→analítico: eje/sección/material desde geometría + generación de nudos) y fila de métricas en `REPOSITORIO-aprendizaje.md` (apertura de la Dirección 2), corrección en `CHANGELOG-plugin.md`, sube el plugin al **siguiente minor** (módulo `puente_analitico/`) y reempaqueta el `.plugin`. **Coordina la versión con la Dirección 1: si el caso 11 ya tomó 0.13.0, este será 0.14.0.**

**Notas de método (casos 1–11):** escribe el código del plugin por heredoc en el sandbox y valida con `ast.parse` (el editor trunca líneas largas, INC-04); empaqueta el `.plugin` con `zipfile` en carpeta escribible y copia con extensión `.plugin` (excluye `node_modules`/`__pycache__`, INC-05); instala `ifcopenshell`/`PyNiteFEA`/`anastruct`/`numpy`/`matplotlib` (pip `--break-system-packages`) y `docx` localmente; usa `ifcopenshell.util.placement.get_local_placement` para los ejes en coordenadas de mundo; el reto es el **grafo de nudos** (tolerancias), no el solver; cuidado con los módulos homónimos entre paquetes (ruta explícita / subproceso); **las herramientas de fichero (Read/Write/Edit) son la fuente de verdad de la carpeta conectada — el shell del sandbox puede ver copias truncadas de ficheros markdown preexistentes (no los edites por shell)**; resultado de **predimensionado**, a revisar y firmar por técnico competente, con los NDP marcados `[confirmar AN]`.

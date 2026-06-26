# Programa de aprendizaje incremental — Motor de cálculo estructural

Banco de **10 casos de uso sintéticos** (realistas pero fabricados) de complejidad
creciente que ejercitan, uno a uno, todos los módulos del plugin
`motor-calculo-estructural`. Cada caso parte de un **modelo IFC ortodoxo** (entidades IFC
estándar del dominio de análisis estructural) y se resuelve con el agente
`ingeniero-estructurista`. Lo aprendido y las correcciones de cada caso se consolidan en el
plugin y en el repositorio de aprendizaje, y alimentan el caso siguiente.

## 1. Objetivo

1. **Validar de extremo a extremo** la cadena IFC ortodoxo → modelo neutro → FEM →
   combinaciones → verificación EC → memoria, sobre modelos cada vez más completos.
2. **Endurecer** el plugin: cada caso descubre carencias (parser, solver, criterio) que se
   corrigen y quedan registradas, de forma que el motor mejora de forma acumulativa.
3. **Documentar el uso**: cada caso es, además, un tutorial reproducible del módulo que ejercita.

## 2. Regla de oro: un hilo = un caso

Cada caso de uso se desarrolla en **un hilo nuevo**. Al terminar un hilo, el estado del
proyecto (plugin corregido + repositorio actualizado + IFC y enunciado del caso siguiente)
queda listo para arrancar el hilo posterior sin contexto adicional.

## 3. La escalera de 10 casos

Crece de un elemento aislado a un edificio integrado. Cada caso reutiliza lo anterior y
añade 1–2 capacidades. Solo usa módulos **ya construidos** (EC2/EC3/EC4/EC7).

| # | Caso | Módulos ejercitados | Salto / aprendizaje principal |
|---|---|---|---|
| 1 | Pórtico de acero biarticulado | `barras` (EC3) | **Parser de IFC ortodoxo**: leer sección de `IfcMaterialProfileSet`/`IfcIShapeProfileDef` y cargas de `IfcStructuralCurveAction`/`IfcStructuralLoadGroup` |
| 2 | Forjado: losa sobre vigas de acero | `laminas` (losa, EC2) + `barras` (EC3) | IFC con **superficie + barras** juntos; reparto de carga losa→vigas |
| 3 | Losa plana sobre pilares | `laminas` (flat, EC2 + punzonamiento) | Punzonamiento con dimensionamiento desde IFC ortodoxo |
| 4 | Cubierta / forjado inclinado | `laminas` (incl, EC2 + membrana) | Plano inclinado; flexión + membrana |
| 5 | Soporte de hormigón + zapata aislada | `barras`/`cimentaciones` (EC2 + EC7) | Cadena pilar→cimiento; lecho elástico |
| 6 | Forjado colaborante / viga mixta | `mixtas` (EC4) | Sección mixta + conexión + fases construcción |
| 7 | Muro de carga + muro de contención (ménsula) | `laminas` (muro) + `muros-contencion` (EC7) | Esbeltez EC2 + estabilidad geotécnica |
| 8 | Losa de cimentación (raft) multipilar | `cimentaciones` (raft) | Placa Winkler multipilar; asiento diferencial |
| 9 | Cimentación profunda: pilote + encepado + pantalla anclada | `pilotes` + `bielas-tirantes` + `muros-contencion` | Geotecnia EC7 completa; varios módulos encadenados |
| 10 | **Edificio integrado** (pórtico + forjado mixto + núcleo/muro + cimentación) | **Todos** | **Un IFC multi-elemento**: el agente clasifica y enruta CADA elemento (corrige el "parse del primer elemento") |

> Una segunda tanda (casos 11+) abordaría módulos aún no construidos: pantallas a cortante
> + sísmico EC8, sismo en contención (Mononobe-Okabe), pretensado, no-lineal.

## 4. Protocolo por hilo (Definición de Hecho)

En cada hilo, el agente `ingeniero-estructurista`:

1. **Carga contexto**: lee este PROGRAMA, el `REPOSITORIO-aprendizaje.md` (lecciones +
   backlog), el `CHANGELOG-plugin.md` y el `ENUNCIADO.md` del caso del hilo.
2. **Ejecuta el caso** sobre el IFC aportado siguiendo la receta de 7 pasos (clasificar →
   enrutar → ejecutar `run_all*` → validar → memoria).
3. **Detecta y corrige**: si el parser/solver/criterio falla con el IFC ortodoxo o da
   resultados incoherentes, corrige el código del plugin (cambio acotado; ver §6).
4. **Valida** contra los **criterios de aceptación** del enunciado (equilibrio ~0 %,
   validación cruzada/analítica, rangos físicos esperados).
5. **Registra**: añade lecciones a `REPOSITORIO-aprendizaje.md`, correcciones a
   `CHANGELOG-plugin.md`, sube versión del plugin (SemVer) si se tocó y **reempaqueta** el
   `.plugin`.
6. **Prepara el siguiente**: redacta el `ENUNCIADO.md` del caso N+1 y genera su **IFC
   ortodoxo** (con su `generate_casoNN_ifc.py` y validación de que abre).
7. **Entrega**: memoria(s) Word, `verificacion.json`, diagramas, y los documentos
   actualizados.

## 5. Cómo se propaga el aprendizaje

- **`REPOSITORIO-aprendizaje.md`** es la única fuente de conocimiento que se arrastra entre
  hilos: lecciones, decisiones y backlog. Se lee al empezar y se amplía al terminar.
- **El plugin** es el portador ejecutable de las correcciones (versionado en
  `CHANGELOG-plugin.md`).
- **`criterios-despacho.md`** (raíz del proyecto) guarda los criterios del despacho
  (materiales por defecto, AN, límites de flecha, recubrimientos) y los va fijando.

## 6. Versionado y alcance de las correcciones

- SemVer del plugin: **patch** (corrección de parser/solver sin cambio de interfaz),
  **minor** (nueva capacidad/módulo o ampliación del parser), **major** (cambio de esquema
  de modelo neutro o de convenios).
- **Correcciones acotadas por hilo.** Si un caso exige una refactorización grande (p. ej.
  iterar todos los elementos de un IFC multi-elemento), se **registra en el backlog** y se
  planifica; no se fuerza en el mismo hilo salvo que sea el objetivo del caso (caso 10).

## 7. Riesgos e incoherencias del planteamiento (resueltas)

Detectados al definir el programa; se documentan para no repetirlos:

1. **"IFC ortodoxo" vs parsers con Psets propios.** El catálogo se desarrolló probando con
   IFC que llevan `Pset_Estructurando_*` (no ortodoxos). Un IFC ortodoxo usa entidades
   estándar (`IfcMaterialProfileSet`, `IfcIShapeProfileDef`, `IfcStructuralCurveAction`,
   `IfcStructuralLoadGroup`…). **Decisión:** los casos usan IFC ortodoxo y el programa
   adapta cada parser a leerlo, empezando por el caso 1 (sección y cargas). *Verificado:* el
   parser de `barras` sobre el IFC del caso 1 deja sección y cargas vacías → ese es el
   primer encargo.
2. **"Un caso que abarque todos los módulos" vs "incremental".** No cabe en el caso 1. Se
   resuelve con la escalera: cada caso añade poco; el **caso 10** los integra.
3. **Multi-elemento.** Los parsers actuales leen `by_type(...)[0]` (un solo elemento). Para
   IFC con varios elementos (del caso 2 en adelante y, a fondo, el 10) hay que **iterar
   todos los elementos** y que el agente **clasifique y enrute cada uno**. Es una corrección
   estructural; se introduce de forma gradual y culmina en el caso 10.
4. **"Sintético" + "real".** Son modelos realistas pero fabricados: parámetros verosímiles,
   no de un proyecto concreto. Todo resultado sigue siendo **predimensionado a validar y
   firmar por técnico competente**.
5. **Módulos inexistentes.** EC8, pretensado, no-lineal y fuego **no** están construidos;
   la escalera 1–10 se ciñe a lo existente. Cualquier caso que los necesite queda fuera de
   esta tanda (casos 11+).
6. **Reproducibilidad.** Dependencias: `ifcopenshell`, `PyNiteFEA`, `anastruct`,
   `matplotlib`, `numpy` (pip `--break-system-packages`) y `docx` (Node). Riesgo conocido:
   el editor/linter puede **truncar líneas largas** al guardar (evitar f-strings muy largas
   con comillas anidadas; preferir `%`-formato con variables). Registrado en el backlog.

## 8. Estructura de carpetas

```
Casos-de-uso/
  PROGRAMA-aprendizaje.md        (este documento)
  REPOSITORIO-aprendizaje.md     (lecciones + backlog, se arrastra entre hilos)
  CHANGELOG-plugin.md            (correcciones y versiones del plugin)
  caso-01-portico-acero/
    ENUNCIADO.md                 (encargo del hilo)
    generate_caso01_ifc.py       (generador del IFC ortodoxo)
    caso-01.ifc                  (modelo IFC aportado)
    validacion-IFC.txt           (prueba de que abre + recuento de entidades)
    (resultados del hilo: modelo_neutro.json, verificacion.json, memoria, diagramas)
  caso-02-.../  ...  caso-10-.../
```

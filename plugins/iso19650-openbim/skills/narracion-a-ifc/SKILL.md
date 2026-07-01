---
name: narracion-a-ifc
description: Crea modelos IFC con geometria real a partir de una descripcion en lenguaje natural (compilador narracion->IFC). Genera edificios, parkings, naves y estructuras describiendolos con palabras (plantas, dimensiones, pilares, muros, forjados, rampas, escaleras, huecos) y cualquier subtipo de IfcElement con sus atributos, Psets estandar y URI bsDD. Usar cuando el usuario pida "crea un edificio", "modela una nave/parking de NxM", "haz una estructura de N plantas", "genera el IFC de...", "levanta/dibuja el modelo", "pon una viga/zapata/puerta", o describa geometria con palabras para producir un IFC.
---

# Compilador narracion -> IFC -> Visor

Convierte la descripcion en prosa del usuario en un modelo IFC valido con geometria
real, sin autoria manual de IFC. Dos capas: la **semantica** (esta skill: prosa ->
spec de alto nivel) y la **determinista** (`scripts/compilar_spec.py` expande macros a
coordenadas; `scripts/spec_to_ifc.py` genera el IFC con IfcOpenShell).

```
 prosa  --(esta skill)-->  <m>.alto.json  --compilar_spec.py-->  <m>.spec.json
        --spec_to_ifc.py-->  <m>.ifc  --visor/pipeline.mjs-->  .frag+props  -->  Visor
```

## Entorno
IfcOpenShell se ejecuta con `PYTHONPATH=/tmp/pylibs` (o `/var/tmp/pylibs:/tmp/pylibs`
si /tmp se reinicio; reinstalar con `pip install --target /var/tmp/pylibs ifcopenshell
jsonschema --break-system-packages --no-cache-dir`). Esquema por defecto **IFC4X3**
(necesario para el catalogo bsDD, IfcGeotechnicalElement, etc.).

## Flujo
1. Extrae de la narracion: dimensiones, nº de plantas y altura, retícula/luz de pilares,
   secciones, espesores, material, y que elementos pide. Pregunta SOLO lo critico que falte.
2. Emite el **spec de alto nivel** (`<m>.alto.json`, formato abajo).
3. Ejecuta (todo con el PYTHONPATH del entorno):
   ```
   python3 scripts/compilar_spec.py  <m>.alto.json  <m>.spec.json
   python3 scripts/spec_to_ifc.py    <m>.spec.json  <m>.ifc            # valida en modo INFORME
   python3 scripts/spec_to_ifc.py    <m>.spec.json  <m>.ifc --estricto # validacion como PUERTA (falla si hay ERROR)
   ```
   La validacion del IFC generado va integrada (`scripts/validar.py`): por defecto **informe
   no bloqueante** (lista ERROR/AVISO/INFO y continua); con `--estricto` actua de **puerta**
   (exit!=0 si hay ERROR duro: esquema, unidades SI, contexto geometrico, GlobalId duplicado,
   RelVoids/RelFills huerfanos, representacion vacia). `--no-validar` la omite. Para auditoria
   profunda de dominio (MEP/lineal) encadena la skill `ifc-validate`.
4. Convierte y abre en el Visor (plugin `visor-ifc`): `node <visor>/pipeline.mjs <m>.ifc
   <visor>/models <m>` y registra el modelo en `<visor>/models/manifest.json` con
   `"load": true` (USA herramientas de fichero para editar el manifest, NO el shell: el
   mount puede truncarlo).
5. Valida con la skill `ifc-validate` y, si procede, enriquece con `bsdd-clasificacion`.

## Convenciones (fijalas)
- **Unidades: metros.** X = ancho, Y = largo/fondo, Z = altura.
- `plantas: N` = nº de niveles (planos de suelo); i=0 -> "Planta Baja"; el superior es cubierta.
- **Defaults**: pilar 0,40x0,40; muro 0,25; forjado 0,30; material HA-30. Dilo en el resumen.
- Con `luz_max` (o `luz_max_x`/`luz_max_y`) se genera reticula de pilares (incluye interiores);
  sin ella, 4 esquinas. Muros perimetrales y forjados activos por defecto en el macro `edificios`.

## Spec de alto nivel (entrada del compilador)
```jsonc
{
  "proyecto": "...", "esquema": "IFC4X3",
  "niveles": { "plantas": 4, "altura": 3.0, "base": 0.0 },   // o lista [{nombre,cota}]
  "edificios": [
    { "nombre": "Pk", "origen": [0,0], "ancho": 25, "largo": 150,
      "luz_max_x": 8.5, "luz_max_y": 7.5,              // o "luz_max" unico; omitir -> esquinas
      "seccion_pilar": [0.45,0.45], "espesor_muro": 0.25, "espesor_forjado": 0.30,
      "material": "HA-30", "muros_perimetrales": false, "forjados": true } ],
  "reticulas_pilares": [ { "nombre":"R","origen":[0,0],"nx":4,"ny":3,"sep_x":6,"sep_y":6 } ],
  // primitivas canonicas explicitas (pasan tal cual):
  "muros":  [ { "nombre":"M1","nivel":"Planta Baja","inicio":[0,0],"fin":[8,0],"espesor":0.25,"altura":3.0,
                "huecos":[ {"tipo":"puerta","pos":2.0,"ancho":1.0,"alto":2.1,"alfeizar":0.0},
                           {"tipo":"ventana","pos":5.5,"ancho":1.5,"alto":1.2,"alfeizar":1.0} ] } ],
  "losas":  [ { "nombre":"F1","nivel":"P1","contorno":[[0,0],[8,0],[8,6],[0,6]],"espesor":0.30,
                "tipo":"macizo|nervado|reticular|unidireccional",
                "capa":0.05,"canto":0.30,"sep":0.8,"intereje":0.72,"b_nervio":0.12,"direccion":"x" } ],
  "rampas": [ { "nombre":"R1","inicio":[x,y,z],"fin":[x,y,z],"ancho":6.0,"espesor":0.30,
                "peldaneada":false,"paso_peldano":0.35,"alto_peldano":0.05 } ],
  "escaleras":[ { "nombre":"E1","nivel":"Planta Baja","pos":[10,0],"ancho":1.2,"n_escalones":20,
                  "huella":0.28,"contrahuella":0.175,"meseta":true,"giro":180,"zanca":true } ],
  "elementos":[ { "clase":"IfcBeam","nivel":"P1","pos":[0,0],"perfil":"IPE400","longitud":6.0 },
                { "clase":"IfcColumn","pos":[8,0],"forma":"circular","d":0.5,"altura":3.5 },
                { "clase":"IfcFooting","pos":[12,0],"dims":[2,2,0.5] } ]
}
```

## Geometria realista (familias)
- **viga/miembro** (IfcBeam/IfcMember): perfil en I, tabla IPE/HEB (`perfil`, `longitud`).
- **pilar** (IfcColumn): `forma:"rect"`(seccion) o `"circular"`(`d`), `altura`.
- **zapata** (IfcFooting): pad + pedestal (`dims`, `pedestal`).
- **puerta/ventana** (IfcDoor/IfcWindow): marco + hoja/vidrio (`ancho`,`alto`,`espesor_muro`).
- **hueco real**: `muros[].huecos` -> IfcOpeningElement + IfcRelVoidsElement (RESTA del muro) +
  relleno puerta/ventana con IfcRelFillsElement.
- **forjados**: `nervado` (1 dir), `reticular` (waffle), `unidireccional` (viguetas + bovedillas
  como IfcBuildingElementPart).
- **escalera**: peldaños; `meseta` (rellano), `giro` (0 recta / 180 en U), `zanca` (zancas).
- **rampa**: losa inclinada; `peldaneada` anade resaltos.

## Catalogo bsDD (objetivos: representacion grafica + atributos/Psets + URI)
`scripts/catalogo_ifc.py` deriva del esquema IFC4X3 las ~150 clases concretas de IfcElement
(11 grupos + IfcVehicle). Cada `elementos[].clase` se instancia con: arquetipo geometrico,
PredefinedType del esquema, Psets `Pset_*Common` estandar (plantillas IfcOpenShell) y la URI
del diccionario IFC de bsDD (`.../buildingsmart/ifc/4.3/class/<Clase>`) como IfcClassificationReference.
- `scripts/construir_catalogo.py catalogo-ifc4x3.json` -> vuelca la tabla completa.
- `scripts/generar_galeria.py galeria.ifc` -> IFC con una instancia de cada clase (catalogo navegable).

## Reglas
- No inventes geometria no pedida; si solo piden pilares, pon `muros_perimetrales:false`,`forjados:false`.
- Si la narracion es ambigua en algo critico (dimensiones, nº de plantas), pregunta.
- Edita el `manifest.json` del visor SOLO con herramientas de fichero (el shell trunca el mount).
- NO uses `geom.settings().set("use-world-coords",True)` para verificar (bug del kernel: coords
  basura en extrusiones rectangulares); verifica con verts locales + `sh.transformation.matrix`.
- Tras generar, valida con `ifc-validate` y ofrece el Visor.

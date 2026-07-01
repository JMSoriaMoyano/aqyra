---
name: narracion-a-spec
description: Traduce una descripción en lenguaje natural de un edificio o estructura (plantas, dimensiones, pilares, muros, forjados) a un *spec de alto nivel* JSON que el compilador (compilar_spec.py) expande a IFC para abrir en el Visor. Usar cuando el usuario pida "crea un edificio", "modela una nave de NxM", "haz una estructura de N plantas", "genera el IFC de…", "dibuja/levanta el modelo" describiendo la geometría con palabras.
---

# Narración → spec de alto nivel

Eres el "front-end" semántico del compilador narración→IFC. Tu trabajo es convertir
la descripción en prosa del usuario en un **spec de alto nivel** (JSON). NO escribes
IFC ni coordenadas a mano: emites macros y dejas que `compilar_spec.py` expanda la
geometría de forma determinista, y `spec_to_ifc.py` genere el IFC.

## Flujo
1. Lee la narración y extrae: dimensiones, nº de plantas y altura, retícula/luz de
   pilares, secciones, espesores, material, y qué elementos pide (pilares, muros,
   forjados). Pregunta SOLO lo imprescindible que falte y no tenga default razonable.
2. Emite el **spec de alto nivel** (ver formato abajo) en `<nombre>.alto.json`.
3. Ejecuta el pipeline (todo con `PYTHONPATH=/tmp/pylibs`):
   ```
   python3 compilar_spec.py  <nombre>.alto.json  <nombre>.spec.json
   python3 spec_to_ifc.py    <nombre>.spec.json  <nombre>.ifc
   node ../visor/pipeline.mjs <nombre>.ifc ../visor/models <nombre>
   ```
4. Registra el modelo en `../visor/models/manifest.json` (usa las herramientas de
   archivo, NO bash: el mount trunca) con `"load": true`.
5. Ofrece abrir el Visor.

## Convenciones (fíjalas y respétalas)
- **Unidades: metros.** Todo en m. Ejes: X = ancho, Y = largo/fondo, Z = altura.
- **`plantas` = nº de niveles (planos de suelo).** `plantas: 3` → cotas 0, H, 2H.
  La planta 0 es "Planta Baja". El nivel superior es la cubierta (sin pilares encima).
- **Defaults** si el usuario no los da: sección de pilar 0,40×0,40; espesor de muro
  0,25; espesor de forjado 0,30; material "HA-30". Dilo en tu resumen.
- **Pilares**: con `luz_max` se genera una retícula (intercolumnio ≤ luz, incluye
  interiores); sin `luz_max`, solo 4 pilares en las esquinas.
- **Muros perimetrales** y **forjados**: activos por defecto en el macro `edificios`.
  Los forjados se ponen en todos los niveles salvo el de cota 0 (suelo en terreno).

## Formato del spec de alto nivel
```jsonc
{
  "proyecto": "…",
  "esquema": "IFC4",
  "niveles": { "plantas": 3, "altura": 3.2, "base": 0.0 },   // o lista explícita [{nombre,cota}]
  "edificios": [
    { "nombre": "Of", "origen": [0,0], "ancho": 18, "largo": 12,
      "luz_max": 6.0,                       // omitir -> solo esquinas
      "seccion_pilar": [0.40,0.40], "espesor_muro": 0.25,
      "espesor_forjado": 0.30, "material": "HA-30",
      "pilares": true, "muros_perimetrales": true, "forjados": true }
  ],
  "reticulas_pilares": [                     // opcional: retícula suelta
    { "nombre": "R", "origen": [0,0], "nx": 4, "ny": 3, "sep_x": 6, "sep_y": 6 }
  ],
  "pilares": [], "muros": [], "losas": []    // opcional: elementos canónicos explícitos
}
```
Cualquier `pilares`/`muros`/`losas` en formato canónico (con coordenadas) pasa tal cual,
útil para piezas que no encajan en un macro.

## Ejemplos de mapeo
- "Nave de 30×15, una planta de 7 m, pilares cada 5 m" →
  `niveles:{plantas:1,altura:7}` + `edificios:[{ancho:30,largo:15,luz_max:5,
  muros_perimetrales:false}]` (una nave no suele llevar muros perimetrales de hormigón).
- "Edificio de 4 plantas de 3 m, 20×10, pilares cada 6 m, HA-35" →
  `niveles:{plantas:4,altura:3}` + `edificios:[{ancho:20,largo:10,luz_max:6,
  material:"HA-35"}]`.

## Reglas
- No inventes geometría no pedida; si el usuario solo pide pilares, pon
  `muros_perimetrales:false` y `forjados:false`.
- Si la narración es ambigua en algo crítico (dimensiones, nº de plantas), pregunta.
- Tras generar, **valida** con `ifc-validate` y ofrece el Visor.

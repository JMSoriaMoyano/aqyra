# Propuesta de parche C1 — huecos de forjado (`losas[].huecos`)

> **Para JM (cruce de frontera).** El cebo ya modela el hueco de forjado (`IfcOpeningElement`
> con `host` = el forjado) y el puente lo emite en `losas[].huecos`. Falta que C1 lo **autore**.
> La IA prepara este parche; **el bump + golden + adopción + ancla en `versions.lock` los firma JM.**

## Qué cambia y por qué es el cruce más barato posible

- **El mecanismo ya existe en C1.** `spec_to_ifc.py` ya crea `IfcOpeningElement` + `IfcRelVoidsElement`
  (`_voids`) para los **muros** (`for h in w.get("huecos",[])`). Solo hay que **replicarlo en el bucle
  de losas**, reutilizando `_voids`, `_box`, `_lp`, `_shape`.
- **El esquema NO se toca.** `spec.schema.json` → `losas[].items` no fija `additionalProperties:false`,
  así que un campo `huecos` en la losa **valida tal cual** (igual que ya pasa con los muros).
- **El cebo ya tomó autoridad del forjado**: emite `losas[]` explícitas con `huecos` y pone
  `edificios[].forjados:false` (patrón idéntico a `pilares:false` con la retícula). Así C1 no duplica.

## El parche (un solo punto, `spec_to_ifc.py`)

Dentro del bucle `for s in spec.get("losas",[]):`, **al final del cuerpo**, justo después de:

```python
        mat(slab,s.get("material")); c["losas"]+=1
```

añadir:

```python
        # --- NUEVO: huecos de forjado (IfcOpeningElement + IfcRelVoidsElement) ---
        for h in s.get("huecos",[]):
            hc=h["contorno"]; hx=[p[0] for p in hc]; hy=[p[1] for p in hc]
            hxmin,hxmax,hymin,hymax=min(hx),max(hx),min(hy),max(hy)
            aw=hxmax-hxmin; ad=hymax-hymin; e=float(s.get("espesor",0.30))
            op=run("root.create_entity",m,ifc_class="IfcOpeningElement",name=f"{s['nombre']}_Hueco")
            try: op.PredefinedType="OPENING"
            except Exception: pass
            op.ObjectPlacement=_lp(m,slab.ObjectPlacement,(0.,0.,0.))
            op.Representation=_shape(m,bctx,_box(m,"hueco_losa",aw,ad,e+0.10,
                              c=((hxmin+hxmax)/2.,(hymin+hymax)/2.,-e/2.)))
            _voids(m,slab,op); c["huecos"]+=1
```

Qué hace: por cada hueco (contorno en planta), crea un `IfcOpeningElement` con una caja del tamaño del
hueco (bbox) que atraviesa el espesor de la losa (con 10 cm de margen para un corte limpio) y lo
relaciona con la losa por `_voids` (`IfcRelVoidsElement`). El `IfcSlab` queda **vaciado** ahí.

> Nota: para huecos rectangulares (núcleos) la bbox = el hueco exacto. Huecos poligonales no
> rectangulares quedarían como su bbox; el void poligonal fino es una mejora posterior si hace falta.

## Formato que emite el cebo (lo que C1 recibe)

```jsonc
"losas": [
  { "nombre": "AQ-FOR-P01", "nivel": "Planta 1", "contorno": [[0,0],[31,0],[31,15.6],[0,15.6]],
    "espesor": 0.3, "material": "HA-30",
    "huecos": [ { "contorno": [[0,7.8],[5.27,7.8],[5.27,15.6],[0,15.6]] } ] } 
]
```

(El cebo: `c1-bridge.ts` → `AltoLosa`/`AltoHueco`. Ver `aqyraToC1()` en la consola del navegador.)

## Checklist de adopción (Llave 1 + Llave 2 — JM)

1. Aplicar el parche en `spec_to_ifc.py` (rama de C1, con traza/PR).
2. **Bump** de C1 (iso19650-openbim) por cambio de frontera.
3. **Golden de C1:** un `alto.json` con `losas[].huecos` compila un IFC con `IfcOpeningElement` +
   `IfcRelVoidsElement` y el `IfcSlab` vaciado (recuento `huecos=N`). Verde = adoptar.
4. Anclar la versión en `Entorno/integracion/versions.lock` (`narracion-a-ifc`/`visor-ifc`).
5. Firma de JM.

*Procedencia: P1 Visor/Editor · Aqyra · slice "hueco de forjado" · propuesta de extensión C1 para firma de JM.*

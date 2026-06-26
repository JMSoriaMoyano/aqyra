# PUE-15 — Puente completo integrado (modo acoplado)

Caso **insignia** IFC-driven (PT 7.3.1): un unico IFC4X3 con **tablero de 2 vanos
(vigas pretensadas) + pila central + 2 estribos**. El lector lo clasifica como
`puente_completo`, separa los subsistemas y los calcula **en modo acoplado**: el
tablero se resuelve primero y sus **reacciones reales** alimentan la pila (reaccion
total) y los estribos (reaccion por metro de ancho). **Predim.; revisar y firmar (ICCP).**

## Cadena de calculo
`PUE-15.ifc` → lector C1 (puente_completo) → tablero (`run_all_viga_pretensada`) →
reacciones de apoyo (2 vanos continuos) → pila central acoplada (`run_all_pila`,
zapata) + estribos acoplados (`run_all_estribo`) → veredicto global + write-back.

## Resultado
- Tablero: **CUMPLE** (aprov 0.836, f1=2.57 Hz).
- Pila central: **CUMPLE** (aprov 0.769, cim zapata).
- Estribos: **CUMPLE** (aprov 0.498).
- **VEREDICTO GLOBAL: CUMPLE** · aprov maximo **0.836**.

## Archivos
`PUE-15.ifc` (modelo integrado) · `resultado.json` · `PUE-15-resultados.ifc` (write-back).

# Caso golden DEC-S1 — Cubierta del depósito-cajón monolítico (lámina, EC2)

> **Ficha golden** del corpus C6, **valida el contrato C5 v0** (motor-fem, **familia lámina**).
> Golden vN valida C5 vN. **Solo JM** cambia valores esperados o tolerancias (vía PR con traza).
> Sembrada de `qa/informes/QA_cajon_Rev02_decopak_2026-06-24.md` (oráculo lámina 2D completa).

```
id:           DEC-S1
contrato:     C5 v0  (familia LÁMINA — incorporada al alcance v0 el 2026-06-26, decisión JM)
proyecto:     Depósito enterrado Decopak (Rubí) — cajón monolítico HA, Rev.02
estado:       SEMILLA — pendiente de ratificación JM y de oráculo certificado (ver §oráculo)
```

## Entrada

```
elemento:     Cubierta de HA del cajón monolítico, placa bidireccional CONTINUA con los muros
              (unión rígida muro-losa); luz larga ≈11,37 m. Solera sobre lecho elástico (Winkler).
modelo:       lámina plegada 3D — 5 paneles (cubierta + 4 muros + solera) acoplados monolíticamente
              en aristas; solera sobre Winkler k_s = 80.000 kN/m³.
acciones:     cubierta = permanente mayorada + UDL LM1 + tándem 600 kN (huella 3,1×2,3 m, parche);
              muros = empuje neto ELU (1,35·tierras_reposo − 1,5·agua); solera = p.p. + columna de agua.
materiales:   HA-30; B500S; γ_s=1,15.
norma:        EC2 (flexión, fisuración EN 1992-3, punzonamiento §6.4)
```

## Esperado (valores de referencia del oráculo)

| Magnitud | Esperado (oráculo lámina) | Tolerancia | ¿Cumple? |
|---|---|---|---|
| Validación elemento: placa SS uniforme vs Navier | M_x, M_y a −0,3 % | ±2 % | ☑ elemento validado |
| Cubierta · M_vano m_x (total ELU) | **440 kN·m/m** (banda 410–461) | ±10 % | u=0,51 (φ25/150) → cumple |
| Cubierta · M_vano m_y (dir. larga) | 261 kN·m/m (banda 231–285) | ±10 % | u=0,60 → cumple |
| Cubierta · M_esquina/apoyo | **249 kN·m/m** (banda 218–250) | ±10 % | u=0,56 → cumple |
| **Equilibrio esquina = momento de cabeza de muro** | coincidencia exacta (cierre del nudo) | — | ☑ (auto-consistencia de la caja) |
| Suma invariante vano+esquina ("balancín") | ≈ 650–711 | — | ☑ confirma física |
| Cubierta · punzonamiento v_Ed | 0,036 MPa (η≈0,08) | ±10 % | cumple holgado |
| Cubierta vano · fisuración w_k (M_serv 307) | 0,169 mm | ≤ 0,20 mm | cumple (resuelve R-2 de Rev.01) |

## Oráculo

```
oraculo:      segundo_fem — lámina plegada 2D completa (quad 24 GdL: placa Kirchhoff ACM 12 +
              membrana Q4 8 + drilling), nodos de arista fusionados (unión monolítica real, sin muelle),
              solera sobre Winkler. Validado contra serie de Navier (placa SS) a −0,3 % y por
              auto-consistencia del nudo de esquina (convergencia <0,5 % en 3 mallas).
fuente:       qa/informes/QA_cajon_Rev02_decopak_2026-06-24.md (2026-06-24)
pendiente:    CAVEAT PyNite — el shell de PyNite es limitado para lámina plegada con acoplamiento
              membrana+flexión; el oráculo certificado de lámina en v0 es el FEM folded-plate de QA
              + el analítico cerrado (Navier/Timoshenko), NO necesariamente PyNite. (Ver C5 §7 y brief 4–6.)
```

## Tolerancia

```
momentos de lámina:  ±10 %  (la sensibilidad de malla del pico bajo el tándem justifica banda más amplia
                     que en barra; el vano puede llegar a ~461 → u sube a 0,53, sigue holgado)
validación elemento: ±2 %
fisuración w_k:      límite normativo ≤ 0,20 mm
Tolerancias RATIFICADAS por JM 2026-06-26.
```

## Veredicto de referencia y gates abiertos

> **Verde con observaciones (Rev.02).** La cubierta como lámina continua cierra el nudo de esquina
> por sí sola; el par (vano 440 / esquina 249) del build cae dentro de la banda del oráculo en las 3 mallas.
> **Gates que dependen de JM (no son error de cálculo):**
> - O-2 flotación del vaso vacío (gate de proyecto, freático).
> - O-4/O-5 sismo hidrodinámico + térmica → **DIFERIDOS de N1.1** (decisión JM 5a, baja sismicidad ac≈0,046 g); el sismo se reabre en minor posterior de C5 con su golden.
> - O-6 versionado (ligado a P4 de N1.1).
> - estanqueidad de la cubierta (cubierta por φ25/150).

```
responsable:  JM
veredicto:    APTO con observaciones (gates de proyecto pendientes de JM)
```

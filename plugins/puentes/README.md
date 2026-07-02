# puentes — Disciplina de puentes de carretera (Ola 7)

Plugin de la disciplina **puentes** del ecosistema *Estructurando*. **Consume** el
nucleo `motor-fem` (contrato **C5**, peldano **FEM-1**) y la geometria **Alignment**
(contrato **C1**, Ola 5); **no recalcula** la mecanica ni reescribe el pretensado.

> Todo es **predimensionado/asistencia** y debe ser **revisado y firmado por
> tecnico competente (Ingeniero de Caminos, Canales y Puertos)**. NDP: `[confirmar AN]`.

## Verticales (PT 7.2 grupo lineal + PT 7.3 subestructura)

| Tipologia | Idealizacion | Acciones / transversales | Comprobacion | run_all |
|---|---|---|---|---|
| **Vigas pretensadas** | emparrillado barra+barra | IAP-11 + pretensado (cargas eq.) | EC2 | `run_all_viga_pretensada.py` |
| **Losa postesada** | lamina **DKMQ** (+ vigas de borde) | IAP-11 + postesado biaxial (balance 2D) + LM1 por **objetivo `esfuerzo_lamina`** | EC2 (tensiones, flexion por franja, punzonamiento) | `run_all_losa_postesada.py` |
| **Portico/marco** | barras + **resortes Winkler** | IAP-11 + **empuje K0** + 2.o orden aprox. | EC2 (dintel/pilas) + **EC7** (cimentacion) | `run_all_portico.py` |
| **Celosia** | barras **articuladas** (Pratt) | IAP-11 (axiles) | EC3 (traccion/pandeo, uniones); **fatiga diferida** | `run_all_celosia.py` |
| **Pila + apoyo + cimentacion** | columna (barra 3D) + **resorte Winkler** en base + **aparato de apoyo** (resorte 6 GdL) en cabeza | IAP-11 (reacciones del tablero + **frenado** + viento + termica); EC8-2 diferida | EC2 fuste **M-N** + 2.o orden + cortante bielas; **EC7** cimentacion **enrutada** (zapata/pilotes/encepado) | `run_all_pila.py` |
| **Estribo** | **muro** con cargas de tablero en coronacion; fuste por motor-fem | empuje **Ka activo** / **K0 reposo** + sobrecarga + reacciones del tablero | **reusa `verificacion_muro`**: EC7 (vuelco/desl/hund) + EC2 (alzado/puntera/talon) | `run_all_estribo.py` |
| **Cajón postesado** (PT 7.4) | **lámina pura** MITC4 + diafragmas-rigidizadores | IAP-11 + postesado por fases + LM1 | EC2 (fases, descompresión, flexión, **cortante+torsión Bredt**, shear lag) | `run_all_cajon.py` |
| **Mixto acero-hormigón** (PT 7.5) | **lámina rigidizada**: losa de láminas + viga de acero como **rigidizador offset** (interacción completa) | IAP-11 + LM1 + **FLM3** (fatiga) | **EC3** (clase 1-4, **abolladura EN 1993-1-5** ancho eficaz) + **EC4** (M_pl mixto, conexión) + **fatiga EN 1993-1-9** | `run_all_mixto.py` |
| **Oblicuo (esviado)** (PT 7.5) | **malla romboidal** sobre la línea de apoyo esviada | IAP-11 + LM1 | EC2 (armado losa) / EC3; **reparto 2D + esquina obtusa** | `run_all_oblicuo.py` |
| **Curvo en planta** (PT 7.5) | **malla sobre la directriz** (Alignment / arco R) | IAP-11 + LM1 | EC2/EC3 con **torsión de Bredt** acoplada (`dT/ds=M/R`) | `run_all_curvo.py` |

Casos e2e: `caso-PUE-01..06`. En **PT 7.3** el motor **NO se toca** (sigue FEM-1):
la subestructura solo usa columna + resortes + modal/movil ya existentes, y reutiliza
las cimentaciones (`zapata`/`pilotes`/`encepado`) y el muro (`verificacion_muro`) de
`motor-calculo` por PYTHONPATH (formulas puras; PyNite no se usa).

## Primer vertical: VIGAS PRETENSADAS (emparrillado)

Flujo e2e (`scripts/run_all_viga_pretensada.py`):

1. **Idealizacion** (`scripts/idealizacion/emparrillado.py`): tablero -> malla C5
   barra+barra (vigas longitudinales + riostras/losa transversal) sobre el eje
   (Alignment o recto). Apoyos isostaticos en estribos.
2. **Acciones IAP-11** (`scripts/acciones/iap11.py`): permanentes (g1+g2), **LM1**
   (tandem 2 ejes + UDL por carril -> `cargas_moviles`), termica (uniforme +
   gradiente), viento, y combinaciones de puente (ELU/ELS).
3. **Pretensado** (`scripts/pretensado/inyeccion_pretensado.py`): perdidas
   (instantaneas + diferidas simplificadas, EC2 5.46) + caso `P` con la carga
   equivalente `w_p = 8·P·e/L²`. Reutiliza `ec2_pretensado` (motor-calculo).
4. **Motor-fem (C5, FEM-1)**: estatico (G/P/T/V), **movil** (envolventes LM1 por
   lineas de influencia), **modal** (frecuencia fundamental, masa participante).
5. **Comprobacion EC2** (`scripts/comprobacion/ec2_tablero.py`): tensiones en
   vacio y servicio, flexion ELU, cortante por bielas (cercos), fisuracion.
6. **Memoria + write-back** (`scripts/comun/resultado_ifc_puente.py`): mapping
   `Pset_Estructurando_ResultadoPuente` para el escritor generico de iso19650-openbim.

## Frontera (contratos del nucleo)
- **C1** (`iso19650-openbim`): IFC + Alignment. No se toca.
- **C5** (`motor-fem`): mallado + ensamblaje + solver (estatico/modal/movil).
- **`puentes`**: idealizacion + IAP-11 + EC2/EC3/EC7 + memoria + write-back.

## Agentes
- `agents/ingeniero-de-puentes.md` — orquestador (clasifica tipologia y enruta).
- `agents/proyectista-vigas-pretensadas.md` — vigas pretensadas (emparrillado).
- `agents/proyectista-losa-postesada.md` — losa postesada (lamina DKMQ).
- `agents/proyectista-portico.md` — portico (barras + resortes + empuje).
- `agents/proyectista-celosia.md` — celosia (barras articuladas + EC3).

## Nucleo transversal espejado
`scripts/nucleo/` (`ifc_utils.py`, `grafo_red.py`, …) es **byte a byte** del
canonico (puerta `verificar_espejo_nucleo.py` -> ESPEJOS IDENTICOS).

## Ejecucion
El motor-fem y el pretensado viven en otros plugins (aislamiento de runtime): se
proveen por `PYTHONPATH`: motor-fem (`scripts/` + `scripts/elementos`) y
motor-calculo (`scripts/pretensado/`, `scripts/muros-contencion/`).

# Caso PCI-01 — Red de BIE a presión · primer vertical de la disciplina `instalaciones` (PT 4.3, Ola 4)

Primer caso **de cálculo** del dominio de instalaciones: cierra la cadena de extremo a
extremo **IFC MEP → modelo neutro de red → demanda → solver hidráulico → verificación →
memoria**, reutilizando el **parser MEP** del PT 4.2 (`iso19650-openbim`) y el **núcleo
transversal** (`ifc_utils` + `grafo_red`, PT 4.1) **sin tocarlos**. Es el nacimiento del
**motor hidráulico de red** (capacidad transversal del ecosistema).

> Reutiliza la red del `caso-MEP-01-red-pci` (que solo validaba topología, sin cálculo) y
> le añade el **cálculo hidráulico**.

## Red

Grupo de presión (fuente, N1) → T1 (DN100, 10 m) → Te (N2) → tres ramales DN65:
T2→BIE-1 (N3, 5 m), T3→BIE-2 (N4, 10 m), T4→BIE-3 (N5, 5 m).
Sistema `IfcDistributionSystem` PredefinedType **FIREPROTECTION**.

## Tubería de extremo a extremo

1. `ifc_to_model_mep.py red-pci.ifc modelo_neutro_mep.json` (plugin `iso19650-openbim`,
   **C1 lectura**) → modelo neutro de red (5 nodos, 4 tramos, 3 terminales, 1 fuente).
2. `run_all_pci.py modelo_neutro_mep.json` (plugin `instalaciones`):
   - **bases_demanda** (H3, **CN-3**): rellena `demanda` por BIE y sistema (RIPCI/UNE/DB-SI).
   - **solver_red** (Darcy-Weisbach): reparto de caudales, pérdida de carga, presiones.
   - **verificacion_red**: balance de caudales y presiones.

## Bases de demanda (NDP [confirmar AN])

- **2 BIE hidráulicamente más desfavorables simultáneas** (RIPCI RD 513/2017 Anexo I;
  UNE-EN 671), autonomía 60 min, presión máxima 500 kPa.
- Caudal y presión dinámica mínima **tomados del dato del proyecto** (IFC): **3,3 l/s** y
  **350 kPa** por BIE (prevalecen sobre el valor por defecto BIE-25 1,6 l/s / 200 kPa).
- Simultáneas seleccionadas: **BIE-1 + BIE-2** (las de mayor longitud de camino desde la
  fuente; BIE-2 gobierna, camino T1+T3 = 20 m).

## Resultado (`resultado.json` / `verificacion.json`) — **VEREDICTO: CUMPLE**

| Tramo | DN | Caudal | Velocidad | f | Δp (Darcy-W., +20 % acc.) |
|---|---|---|---|---|---|
| T1 (montante) | 100 | 6,60 l/s | 0,840 m/s | 0,0207 | 0,876 kPa |
| T2 (→BIE-1) | 65 | 3,30 l/s | 0,995 m/s | 0,0224 | 1,022 kPa |
| T3 (→BIE-2) | 65 | 3,30 l/s | 0,995 m/s | 0,0224 | 2,043 kPa |
| T4 (→BIE-3, inactiva) | 65 | 0,00 | — | — | 0 |

- **Terminal gobernante: BIE-2** — presión disponible **597,1 kPa** ≥ mínima 350 kPa
  (margen **247,1 kPa**). BIE-1: 598,1 kPa (margen 248,1).
- **Fuente:** presión disponible 600 kPa ≥ **requerida 352,9 kPa** (margen 247,1 kPa).
- **Velocidad pico 0,995 m/s** ≤ v_max 6 m/s.
- **Balance de caudales: 0,0000 %** (cabecera 6,60 l/s = demanda 2×3,30; residuo en la
  te 0,0000 %) — cierre análogo al equilibrio estructural.

## Verificación

- Micro-test del solver: `instalaciones/scripts/red/test_solver_red.py` (tramo recto vs
  analítico, balance en la te, fricción laminar/turbulenta) → **0 fallos**.
- Núcleo espejado **idéntico** al canónico (gate `verificar_espejo_nucleo.py`).

*Predimensionado/asistencia; a revisar y firmar por técnico competente (Ingeniero de
Caminos). NDP `[confirmar AN]`.*

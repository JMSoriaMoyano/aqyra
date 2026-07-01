# Memoria Instalaciones - Caso PCI-01 (Red de BIE a presión)

> Memoria por obra (no mezclar con otros proyectos).
> Leída por las skills del plugin `instalaciones` al iniciar.
> Documento de trabajo: **todo resultado debe ser revisado y firmado por técnico competente** (Ingeniero de Caminos).
> Criterios transversales heredados de `../../criterios-instalaciones.md`.

## 1. Datos del proyecto
- Proyecto / emplazamiento: caso de demostración — red de BIE (PCI).
- Tipología y uso: instalación de protección contra incendios por agua (BIE).
- Anejo Nacional / reglamento aplicado: **España** (RIPCI RD 513/2017).
- Condicionantes: sistema `IfcDistributionSystem` FIREPROTECTION; abastecimiento por grupo de presión.

## 2. Normativa aplicada
- **RIPCI** (RD 513/2017), Anexo I — diseño y mantenimiento de BIE.
- **UNE-EN 671-1/-2** — bocas de incendio equipadas (BIE-25 / BIE-45).
- **UNE 23500** — sistemas de abastecimiento de agua contra incendios.
- **DB-SI SI4** (CTE) — dotación de instalaciones de protección contra incendios.

## 3. Materiales / componentes adoptados
- Tubería de **acero galvanizado**, rugosidad absoluta 0,045 mm [confirmar AN].
- Montante DN100; ramales a BIE DN65.
- Grupo de presión (fuente): presión disponible 600 kPa, caudal 25 l/s.

## 4. Acciones / bases de cálculo (DEMANDA)
- **Simultaneidad**: 2 BIE hidráulicamente más desfavorables funcionando a la vez (RIPCI Anexo I) [confirmar AN].
- **Caudal de cálculo** por BIE: **3,3 l/s** (dato del proyecto, IFC; prevalece sobre el defecto BIE-25 de 1,6 l/s).
- **Presión dinámica mínima** en BIE: **350 kPa** (dato del proyecto; defecto normativo 200 kPa). Máxima 500 kPa.
- **Método hidráulico**: Darcy-Weisbach, fricción Swamee-Jain; agua 20 °C (ρ=998, ν=1,01·10⁻⁶); accesorios +20 %; v_max 6 m/s [confirmar AN].
- BIE simultáneas seleccionadas: **BIE-1 + BIE-2** (mayor longitud de camino; **BIE-2 gobierna**).

## 5. Comprobaciones por elemento / sistema
> Para cada elemento: modelo · cálculo · cláusula normativa · resultado (aprovechamiento/margen).

### Red de tramos (pérdida de carga)
- Modelo / hipótesis: red en árbol, raíz = fuente; caudales por continuidad.
- Cálculo: T1 (DN100, 6,60 l/s, v=0,840 m/s, Δp=0,876 kPa); T2 (DN65, 3,30 l/s, v=0,995 m/s, Δp=1,022 kPa); T3 (DN65, 3,30 l/s, v=0,995 m/s, Δp=2,043 kPa); T4 inactiva.
- Cláusula: Darcy-Weisbach (UNE 23500 / criterio del despacho).
- Resultado: **velocidad pico 0,995 m/s ≤ 6 m/s → CUMPLE**.

### BIE-2 (terminal gobernante)
- Modelo / hipótesis: presión propagada desde la fuente por el camino T1+T3 (20 m).
- Cálculo: presión disponible 597,1 kPa; mínima 350 kPa.
- Cláusula: RIPCI Anexo I / UNE-EN 671.
- Resultado: **margen 247,1 kPa → CUMPLE** (BIE-1: 598,1 kPa, margen 248,1).

### Fuente (grupo de presión)
- Presión disponible 600 kPa ≥ **requerida 352,9 kPa** (margen 247,1 kPa) → **CUMPLE**.

### Balance de caudales (arnés)
- Cabecera T1 6,60 l/s = demanda 2×3,30 l/s; **residuo 0,0000 %** → continuidad cerrada.

## 6. Registro de comprobaciones (fechado)
- **[2026-06-22] Red PCI-01 / run_all_pci (bases_demanda + solver_red Darcy-Weisbach + verificacion_red)**
  - Parámetros: 2 BIE simultáneas, 3,3 l/s y 350 kPa por BIE, accesorios +20 %, v_max 6 m/s.
  - Resultado: VEREDICTO **CUMPLE**; fuente req 352,9 / disp 600 kPa; v_pico 0,995 m/s; balance 0,0000 %.
  - Decisión / próximo paso: red holgada (gran margen por la presión alta de fuente); escribir Psets de resultado al IFC (diferido a mini-PT).

## 7. Conclusiones
- La red de BIE **CUMPLE** con amplio margen: la presión de fuente (600 kPa) supera holgadamente la requerida (352,9 kPa) y todas las BIE simultáneas superan su presión dinámica mínima. Velocidades bajas (≤1 m/s).
- Resultado de **predimensionado/asistencia**; debe ser **revisado y firmado por técnico competente** (Ingeniero de Caminos). NDP marcados **[confirmar AN]**.

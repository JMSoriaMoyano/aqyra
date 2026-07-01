# Caso 15 — Núcleo de pantallas acopladas + sísmico EC8 integrado en el edificio

> **PT 1.5 de la Ola 1: cierra la estabilización lateral de edificación.** Segundo
> peldaño de la familia sísmica (extiende el caso 11, pantalla aislada). Plugin de
> partida: **motor-calculo-estructural v0.21.0** (módulo `sismico/` + biblioteca EC8).

## 1. Contexto y objetivo

Se calcula el **sistema de estabilización lateral** de una torre compacta de 6 plantas:
un **núcleo en U abierto** de hormigón armado (escalera/ascensor) con los **machones de
alma acoplados por dinteles** y dos **alas**. Doble objetivo:

1. **Extender el módulo sísmico** de la pantalla aislada (voladizo, 1 GdL/planta) al
   **núcleo**: varias pantallas en planta con **diafragma rígido y 3 GdL/planta**
   (ux, uy, θz), rigidez a torsión, reparto de cortante por **rigidez + excentricidad**
   (CR vs CM), **torsión accidental** (§4.3.2) y **vigas de acoplamiento DCM** (§5.5.3.5).
2. **Integrar el sísmico en el orquestador de edificio** (`run_all_edificio`): derivar
   masas de planta, montar el modelo lateral, distribuir el cortante sísmico y verificar
   derivas globales, con combinación sísmica **EC0 §6.4.3.4**.

## 2. Modelo (lo que contiene el IFC, ortodoxo, IFC4, SI)

- **Núcleo en U**, C30/37, tw=0,30 m, 6 plantas × 3,0 = 18 m:
  - 2 **machones de alma** `IfcStructuralSurfaceMember` (plano YZ, Lw=2,0 m), separados por
    una **puerta** de 1,40 m y **acoplados** por un **dintel** (b=0,30, h=0,70) en cada planta.
  - 2 **alas** `IfcStructuralSurfaceMember` (plano XZ, Lw=4,0 m).
- **Masas de planta** como `IfcStructuralPointAction` (ForceZ=−W) en los **nodos de diafragma**
  (centro de masa CM): W=1.400 kN plantas 1–5 y 1.000 kN cubierta (ΣW=4.000 kN, m=408 t).
- **Bases empotradas** `IfcBoundaryNodeCondition` (6 GDL) en cada pantalla.
- **Parámetros EC8** en `Pset_Estructurando_Sismo` (ag=0,20 g; suelo C; espectro tipo 1;
  **q=3,6** DCM muros acoplados; λ=0,85) y datos del núcleo en `Pset_Estructurando_Nucleo`
  (dintel, abertura, plano de edificio 8×8, CM) y por pantalla en `Pset_Estructurando_Pantalla`
  (rol, dirección que resiste, par acoplado). NDP **[confirmar AN]** (NCSE-02 / EC8).

## 3. Criterios de aceptación

1. **Espectro/modal**: Sd(meseta)=ag·S·2,5/q≈0,16 g; T1 en meseta; ΣM_eff ≥ 90 % en X e Y.
2. **Equilibrio**: cortante basal Fb=ΣF_i (~0 %); reparto por pantalla Σ=Fb por dirección;
   contraste modal espectral vs fuerzas laterales.
3. **CR vs CM y torsión**: excentricidad estática e0 + torsión accidental ±0,05·L.
4. **Acoplamiento**: grado de acoplamiento DoC, cortante del dintel, armadura del dintel (DCM).
5. **Verificación** (aprov. ≤ 1): cortante de alma, elementos de borde, N-M por pantalla,
   viga de acoplamiento, **deriva** entre plantas (≤ límite de daño).
6. **Integración**: `run_all_edificio` aplica el caso sísmico y verifica derivas globales.

## 4. Resultado (resumen)

CUMPLE (predimensionado). Sd(meseta)=0,1597 g; T1x=0,305 / T1y=0,390 s; ΣM_eff=100 %;
e0x=0,60 m; Fb_X=Fb_Y=543 kN (equilibrio 0,000 %); **DoC=0,72** (dintel diagonal);
machón a barlovento en **tracción neta −775 kN**; deriva máx 0,225 %·h; **aprov. máx 0,72**.
Plugin **v0.22.0**. Resultado de **predimensionado, a revisar y firmar por técnico competente**.

## 5. Cómo ejecutar

```bash
# generar el IFC del caso:  python3 generate_caso15_ifc.py
cd <plugin>/scripts && python3 sismico/run_all_nucleo.py <proj> <ruta>/caso-15.ifc
python3 sismico/generate_memoria_nucleo.py <proj>
# sísmico integrado en el edificio:
python3 run_all_edificio.py <proj> <ifc> --sismo
```

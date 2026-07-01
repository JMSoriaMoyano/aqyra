# Ficha de golden de record — C1-APERTURA-01 (Llave 1 en VERDE)

> **Para JM** · entrega del hilo de `Estructurando` (motor / contrato C1) · 2026-06-28.
> **La IA prepara/propone; JM registra y firma** (regla de dos llaves). Esta ficha y los
> ficheros adjuntos son el artefacto para el **PASO-JM** (`Aqyra-Raiz/PASO-JM_C1_registro-
> golden-y-firma.md`). **No** se ha escrito en `Estructurando 2.0` ni se ha firmado/anclado.

## Ficha (para `Estructurando 2.0/contratos-golden/golden/`)

```
id:           C1-APERTURA-01
contrato:     C1 v0 (apertura de familias P1, aditivo) · iso19650-openbim 0.10.0  [propuesta de bump]
entrada:      golden_C1-APERTURA-01.alto.json
              (huecos en LOSA + MURO · IfcTransportElement=ELEVATOR · alineacion
               clotoide + acuerdo vertical · doble clasificacion bsDD+Uniclass)
esperado:     IFC IFC4X3 valido en el que:
                - la LOSA queda VACIADA (1 IfcRelVoidsElement sobre IfcSlab) y el MURO vaciado (1)
                - el ASCENSOR esta PRESENTE (IfcTransportElement, PredefinedType=ELEVATOR)
                - el IfcAlignment es LEGIBLE por ifc_to_model_lineal.py:
                    planta = LINE · CLOTHOID · CIRCULARARC · CLOTHOID · LINE
                    L = 400.000 m ; A_clotoide = 134.164 (= sqrt(300*60)) ; validacion = CUMPLE
                - cada elemento lleva bsDD (URI) + Uniclass 2015 (EF): 7/7 (4 pilares, 1 muro,
                  1 losa, 1 ascensor)  [losa -> EF_30_20 Floors ; ascensor -> EF_80_50 Lifts]
oraculo:      compilar_spec.py -> spec_to_ifc.py -> { ifc_to_model_lineal.py + validacion_alineacion.py }
              + validar.py (interno, ERROR=0 AVISO=0)            [run: 2026-06-28]
tolerancia:   conteos EXACTOS (huecos losa=1, muro=1; ascensor=1; planta=5 segmentos; clasif 7/7).
              geometrico: L=400.000 m (exacto a 1e-6) ; A_clotoide=134.164 (±0.1) ; secuencia de
              planta exacta. Regla de oro: un fallo se arregla en el codigo, NO aflojando la golden.
responsable:  JM
```

## Resultado del oráculo (run 2026-06-28, ficheros desplegados)

```
compile:  esquema=IFC4X3  pilares=4 muros=1(huecos=2) losas=1 elementos=1 alineaciones=1
alineacion planta: ['LINE','CLOTHOID','CIRCULARARC','CLOTHOID','LINE'] | L=400.0 | validacion: CUMPLE
huecos losa=1 muro=1 | IfcTransportElement=1 (['ELEVATOR'])
doble clasificacion: 7 elementos, sin clasif=0
VEREDICTO GOLDEN (Llave 1): VERDE
validar.py interno: ERROR=0 AVISO=0
regresion: test_lineal.py (Ola 5) TODOS OK ; edificio-oficinas (consumidor existente) ERROR=0
```

## Ficheros adjuntos

- `golden_C1-APERTURA-01.alto.json` — entrada patrón (lo que emitiría el cebo).
- `golden_C1-APERTURA-01.spec.json` — spec canónico (salida de `compilar_spec.py`).
- `golden_C1-APERTURA-01.ifc` — resultado IFC4X3 (la verdad compilada).
- `RESULTADO_oraculo.txt` — log del oráculo.

## Lo que queda a JM (Llave 2)

1. Registrar esta ficha en `Estructurando 2.0/contratos-golden/golden/`.
2. Fila C1 del registro → estado **Firmado**, versión y capacidades (huecos generalizados ·
   catálogo abierto · alineaciones completas · doble clasificación · esquema forward-open).
3. Firmar (tags GPG) en `aqyra-motor` (código + texto de C1) y `aqyra-contratos-golden`
   (golden + registro); **anclar** `iso19650-openbim: "0.10.0"` en
   `Entorno/integracion/versions.lock` **solo si la golden está verde**.
4. Reconciliar el número de versión (skew: lock 0.8.2 / paquete 0.9.2 / dev 0.7.0 → propuesta 0.10.0).

*Predimensionado/asistencia; a revisar y firmar por técnico competente.*

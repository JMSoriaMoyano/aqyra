# Paso de JM — registrar la golden de C1 y firmar (zona protegida)

> **Para JM** · Aqyra-Raiz · 2026-06-28 · **tu 2ª llave sobre la evolución de C1.**
> Se ejecuta **cuando el hilo de `Estructurando` te entregue** los artefactos (código probado, texto de C1, número de versión y la **golden candidata en verde**). Hasta entonces, esto es la plantilla; los `‹…›` se rellenan con lo que devuelva ese hilo. **Yo (panel) preparo; tú registras y firmas.**

---

## 1. Qué recibes del hilo de `Estructurando`

- Código en `aqyra-motor` (`spec_to_ifc.py` + `iso19650-openbim`) con las 5 capacidades de la RFC.
- `Nucleo-transversal/C1_Contrato-IFC-modelo-neutro.md` actualizado.
- Versión nueva propuesta: **`iso19650-openbim ‹X.Y.Z›`**.
- **Golden candidata en verde** (el `alto.json` patrón + el resultado).

## 2. Registrar la golden de record en `Estructurando 2.0` (tu zona protegida)

Coloca la ficha en `Estructurando 2.0/contratos-golden/golden/` (es el registro de la verdad; solo tú lo tocas). Plantilla:

```
id:           C1-APERTURA-01
contrato:     C1 v‹N›
entrada:      alto.json patron (huecos en losa+muro · IfcTransportElement · alineacion clotoide+acuerdo vertical · doble clasificacion bsDD+Uniclass)
esperado:     IFC valido — losa vaciada ‹n› huecos · ascensor presente · IfcAlignment legible por ifc_to_model_lineal · clasificacion bsDD+Uniclass en cada elemento
oraculo:      compilacion + parser lineal (ifc_to_model_lineal) + ifc-validate   [+ fuente: ‹run-id/fecha›]
tolerancia:   ‹exacta para conteos; geometrica segun el run›
responsable:  JM
```

## 3. Anotar el bump de C1 en el registro único

En `Estructurando 2.0/contratos-golden/README.md`, fila **C1**: estado → **Firmado**, versión → **v‹N›** (capacidades: huecos generalizados · catálogo de clases abierto · alineaciones completas · doble clasificación · esquema forward-open).

## 4. Firmar (dos repos) y anclar

El sello de 2ª llave (tag GPG firmado, como en el cebo) va en **los dos repos** que cambian:

- **`aqyra-motor`** (`Estructurando`): commit del código + texto de C1 → tag firmado `c1-evolucion-‹fecha›`.
- **`aqyra-contratos-golden`** (`Estructurando 2.0`): commit de la golden + registro → tag firmado `c1-golden-‹fecha›`.
- **Anclar** en `Entorno/integracion/versions.lock`: `iso19650-openbim: "‹X.Y.Z›"` — **solo si la golden está verde**.

> **El `.bat` runnable (`FIRMA_C1.bat`) lo materializo yo** cuando el hilo de `Estructurando` devuelva los valores reales (paths, versión, nombre de la golden), igual que `FIRMA_cebo.bat` — para no dejarte un `.bat` con rutas adivinadas. Estructura prevista (limpia `index.lock`, puerta de secretos, `git tag -s` clave por defecto 8FD1E413…0942, push `--follow-tags`, `git tag -v`).

## 5. Después (queda desbloqueado, sin volver a tocar C1)

- El **lado cebo** (P1·A/B/C en `Entorno`) emite `huecos`/`ifcClass`/`alineaciones[]`/Uniclass contra el contrato ya completo; cada slice se sella con el ritual ligero de siempre (VERIFICAR + `.bat` de firma).
- Clases nuevas, clotoide/alzado y reglas de auditoría **no** reabren el contrato.

*Procedencia: Aqyra-Raiz · hilo de coordinación · paso de JM para registrar/firmar la evolución de C1 · 2026-06-28.*

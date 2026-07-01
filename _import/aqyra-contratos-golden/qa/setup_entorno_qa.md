# Puesta en marcha del entorno de QA — Decopak HQ

Entorno donde el **FEM sí se ejecuta** (a diferencia del sandbox de build). Requiere disco libre y sin límite de 45 s por comando: la máquina del despacho, un contenedor, o cualquier entorno con permiso de instalación.

## 1. Crear el entorno

```bash
cd <repo>/Estructurando 2.0
python3 -m venv .venv-qa
source .venv-qa/bin/activate        # Windows: .venv-qa\Scripts\activate
pip install -r qa/requirements.txt
python -c "import numpy,scipy,ifcopenshell; from Pynite import FEModel3D; print('entorno QA OK')"
```

## 2. Localizar el motor

El motor de cálculo (FEM + librerías EC) está en el plugin `motor-calculo-estructural` (`scripts/`). El orquestador del edificio es `scripts/run_all_edificio.py`; por subsistema, los `run_all*` de cada grupo (ver catálogo en el README del plugin):

| Caso golden | Grupo del motor | Orquestador | Oráculo de QA |
|---|---|---|---|
| DEC-A1 (CLT/nervio) | `laminas/` o analítico | run_all*.py | analítico cerrado + EC5 |
| DEC-B1 / B2 (diagonal/cordón) | `barras/` | run_all.py (+ cross_validate anaStruct) | **PyNite** celosía nudos reales |
| DEC-B4 (montante) | `barras/` | run_all.py | EC3 6.3.1 (L_cr 3,08 vs 9,25) |
| DEC-E1 (encepado) | `bielas-tirantes/` | run_all_encepado.py | analítico bielas + EC2 §6.5 |
| DEC-E2 (pilote) | `pilotes/` | run_all_pilote.py | analítico EC7 (datos SOCOTEC) |

> El motor avisa de un **límite de 45 s en sandbox** y ofrece `--solo <subsistema>` en `run_all_edificio.py`. En el entorno de QA (sin ese límite) no hace falta, pero el flag sirve para aislar un subsistema.

## 3. Flujo de verificación (resumen; detalle en `ENCARGO_QA_decopak-hq.md`)

1. Idealizar desde el IFC con **nudos reales** (no áreas tributarias).
2. Resolver con el **oráculo** de la tabla → comparar con el valor build dentro de la tolerancia.
3. Capa **normativa** (aprovechamiento ≤ 1, cuantías, flechas, fisuración, EC7).
4. Verificaciones sin oráculo: **equilibrio**, **sólido rígido**, **convergencia** (y patch test en lámina).
5. Emitir **Informe de QA por cálculo** (`qa/informes/`, plantilla incluida) → veredicto APTO/NO APTO → **a firma de JM**.

## 4. Trazabilidad obligatoria

Registrar en cada informe la **versión/commit real** del motor y plugins (no «0.0.0»). Si `versions.lock` sigue sin anclar, marcar **«verificado sobre versión no anclada»**.

## 5. Reglas anti-gaming (Gobierno §B.5)

- Golden y tolerancias en **zona protegida** (`contratos-golden/`); cambiarlas exige PR aprobado por JM.
- Un NO APTO **no** se resuelve aflojando tolerancia ni editando el esperado — **solo arreglando el cálculo**.
- QA **no firma**: certificado = golden verde + informe limpio + **firma de JM**.

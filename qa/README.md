# qa/ — arnés de QA independiente

Quien produce **no** aprueba. El agente de QA corre en **ejecución separada**, con su propio oráculo. Prepara evidencia; **JM firma**.

## Tres capas

1. **Numérica (oráculo)** — contraste contra referencia independiente del motor. Jerarquía: analítico → segundo código FEM → MMS (Gobierno §B.3). PyNite es el espejo por defecto.
2. **Normativa** — comprobador de reglas separado (cuantías, flechas, aprovechamiento ≤ 1, EC2/EC3/CTE/IC).
3. **Regresión** — la suite golden corre en CI en cada cambio; desviación = puerta roja.

## Certificación de dos llaves

Un resultado se «certifica» solo con: (a) golden verde · (b) informe de QA limpio · (c) **firma de JM**.

## informes/

Un **Informe de QA por cálculo** por verificación relevante. Trazabilidad mínima:

```
input → versión de código (SemVer) → norma aplicada → resultado →
comparación con oráculo → veredicto (APTO/NO APTO) → firma JM
```

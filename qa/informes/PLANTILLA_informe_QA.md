# Informe de QA por cálculo — [CASO: DEC-xx]

- **Caso golden:** DEC-xx — [elemento]
- **Contrato / golden:** Cx vN (golden vN valida contrato vN)
- **Fecha de verificación:** [AAAA-MM-DD]
- **Ejecutado por:** agente de QA (ejecución separada del build) · **Oráculo:** [analítico | PyNite | anaStruct | MMS]
- **Versión verificada:** motor [tag/commit] · plugins [tag] — *(si versions.lock=0.0.0 → «versión no anclada»)*

> QA prepara la evidencia y emite el veredicto técnico. **La certificación requiere la firma de JM** (segunda llave). La IA no firma.

---

## 1. Trazabilidad

```
input:       [parámetros del caso + ref. IFC (#id, perfil, L, cargas)]
version:     [motor/plugins SemVer o «no anclada»]
norma:       [EC0/EC1/EC2/EC3/EC5/EC7 art. aplicados + AN España]
metodo QA:   [idealización con nudos reales + oráculo usado]
resultado:   [valores QA recalculados]
oraculo:     [referencia independiente + fuente]
comparacion: [valor build vs valor QA vs tolerancia]
```

## 2. Capa 1 — Numérica (oráculo)

| Magnitud | Valor build | Valor QA (oráculo) | Δ | Tolerancia | ¿Dentro? |
|---|---|---|---|---|---|
| [N_Ed / M / δ / f₁ / R_adm …] | | | | | ☐ |
| [aprovechamiento u] | | | | | ☐ |

**Verificaciones sin oráculo:** equilibrio ΣF/ΣM ☐ · sólido rígido ☐ · convergencia ☐ · patch test (lámina) ☐.

## 3. Capa 2 — Normativa

| Comprobación | Límite | Valor QA | ¿Cumple? |
|---|---|---|---|
| Clasificación de sección | — | | ☐ |
| Aprovechamiento ≤ 1,0 | ≤ 1,0 | | ☐ |
| [pandeo / cuantía / flecha / fisuración / EC7] | | | ☐ |

## 4. Capa 3 — Regresión

- ¿Promovido a golden congelado en `contratos-golden/golden/`? ☐ Sí ☐ No
- ¿Corre en CI sin desviación? ☐

## 5. Observaciones / supuestos del build puestos a prueba

[p. ej. S-B1 arriostramiento del montante: longitud de pandeo efectiva obtenida del FEM nodal = … ; S-A2 luz real de la costilla = … ; reacciones reales sobre muros/encepados = …]

## 6. Veredicto de QA

> **[ APTO / NO APTO ]** — [justificación en una línea]

- Si **NO APTO**: causa y devolución a build (no se ajusta tolerancia ni esperado; se corrige el cálculo).

## 7. Firma (segunda llave — JM)

```
Verificado por QA:   [agente/run]            fecha: [   ]
Tolerancias fijadas por JM:  ☐
FIRMA JM (técnico competente): ______________  fecha: [   ]   → CERTIFICADO ☐
```

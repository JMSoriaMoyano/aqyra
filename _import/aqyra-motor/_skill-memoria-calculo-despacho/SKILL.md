---
name: memoria-calculo-despacho
description: Redacta memorias de calculo (estructuras, instalaciones, obras lineales, puentes) con el FORMATO DEL DESPACHO en Word -- A4 Arial 11 (tablas 9,5), caratula con VEREDICTO en verde (favorable) o rojo (desfavorable), tablas SIN cebra con cabecera azul que SE REPITE en saltos de pagina, parrafos justificados, ESQUEMAS de carga en pastel SOLIDO y DIAGRAMAS de esfuerzos N/V/M con TRANSPARENCIA, y los coeficientes de mayoracion (gamma) y combinacion (psi) escritos en las hipotesis. Usar cuando se pida "memoria de calculo", "memoria con el formato del despacho", "documento/anejo de calculo", "maquetar resultados en Word con el estilo del despacho" o pasar una memoria .md a Word del despacho.
---

# Memoria de calculo del despacho

Genera la memoria de calculo justificativa en espanol como documento **Word A4**, con la
identidad visual y las reglas del despacho. Esta skill aporta el **motor de maquetacion**
(modulo `scripts/docx_despacho.py`) y la **libreria de figuras** (`scripts/figuras_despacho.py`),
para que el documento salga siempre con el mismo formato.

> Todo entregable es de **predimensionado/asistencia** y debe ser **revisado y firmado por
> tecnico competente** (ICCP). Lo no resuelto se marca `[PENDIENTE]`; los parametros sujetos
> al Anejo Nacional, `[confirmar AN]`.

## Orden de trabajo (estricto)
1. **Primero los resultados.** Reunir datos, esfuerzos, comprobaciones y veredicto del
   calculo (de los `resultado_*.json`, de las skills de calculo o de la memoria `.md`). No
   inventar valores; cada cifra debe rastrearse a un calculo, norma o anexo.
2. **Luego maquetar.** Construir el `.docx` con `scripts/docx_despacho.py` y las figuras con
   `scripts/figuras_despacho.py`, siguiendo la estructura y el estilo de abajo.

## Estructura del documento (esqueleto)
Caratula (titulo, proyecto, disciplina/elemento, autor ICCP, fecha/rev, **veredicto global**,
descargo) -> Indice -> 1. Objeto y alcance -> 2. Normativa -> 3. Datos de partida ->
4. Hipotesis: acciones y combinaciones (**con coeficientes gamma y psi**) -> 5. Modelo e
idealizacion -> 6. Calculo y resultados (**priorizar diagramas de esfuerzos**) ->
7. Comprobaciones (clausula, E_d, R_d, aprovechamiento, veredicto) -> 8. Conclusiones y
limitaciones -> 9. Anexos (write-back IFC, listados). Detalle por disciplina en
`references/formato-memoria-calculo.md`.

## Reglas de estilo (las aplica el motor)
- **Tipografia** Arial 11 pt; **dentro de tablas Arial 9,5 pt**. **Parrafos justificados**;
  titulos a la izquierda.
- **Tablas**: sin cebreado, **cabecera con fondo azul claro** `#D9E2F3` que **se repite al
  cortarse la tabla por salto de pagina**; **sin lineas verticales** salvo en la cabecera.
- **Veredicto** en la caratula (y en conclusiones): **CUMPLE en verde** `#2E7D32` si es
  favorable, **NO CUMPLE en rojo** `#B00000` si es desfavorable; aprovechamiento eta=E_d/R_d.
- **Graficos**: **tonos pastel**. **Transparencias SOLO en los diagramas de esfuerzos**; los
  **esquemas de carga y secciones van en pastel SOLIDO**.
- **Priorizar la representacion grafica**: diagramas de esfuerzos (N, V, M) y esquemas de
  cargas frente a su descripcion numerica; la tabla acompana a la figura.
- **Coeficientes explicitos**: en las hipotesis, tabla con la combinacion escrita
  (p. ej. 1,35*G + 1,50*Q), los coeficientes gamma/psi y su clausula (EC0 6.10 / IAP-11).
- Citar la clausula, no reproducir el texto de la norma. Descargo en caratula y cierre.

## Como construir el documento
Ejecutar con Python (requiere `python-docx` y `matplotlib`). Anteponer la ruta de la skill al
`PYTHONPATH` o importar desde `scripts/`.

```python
import sys; sys.path.insert(0, "<ruta_skill>/scripts")
from docx_despacho import (nuevo_doc, portada, indice, H1, P, fig, tabla, leyenda,
                           cierre, cabecera_pie)
import figuras_despacho as F

doc, sec = nuevo_doc()
portada(doc, "MEMORIA DE CALCULO", "Estribo de puente - PUE-06",
        campos=[("Proyecto","..."),("Disciplina","Estructuras . puentes"),
                ("Autor","[Nombre] ICCP . Col. [____]"),("Fecha / Revision","23/06/2026 . Rev. 00")],
        verdict="CUMPLE (aprov. max. 0,971)", favorable=True)
indice(doc)
H1(doc, "4. Hipotesis: acciones y combinaciones")
tabla(doc, ["Combinacion","Expresion","Coef. gamma/psi","Clausula"],
      [["ELU","1,35*G + 1,50*Q","gamma_G=1,35 . gamma_Q=1,50","EC0 6.10"]])
leyenda(doc, "Tabla. Coeficientes de mayoracion y combinacion.")
# Figuras: esquema SOLIDO, diagrama TRANSPARENTE
F.esquema_columna("/tmp/esq.png", H=8.0, N_cabeza="5.700 kN", H_horiz="630 kN", viento="3 kN/m")
fig(doc, "/tmp/esq.png", w=105); leyenda(doc, "Figura 1. Esquema de cargas (ELU).")
F.diagrama_columna("/tmp/dia.png", H=8.0, N_base=8291, V_base=750.6, M_base=5918)
fig(doc, "/tmp/dia.png", w=160); leyenda(doc, "Figura 2. Diagramas N/V/M (ELU).")
cabecera_pie(sec, "Proyecto . Disciplina - Memoria de calculo", "[Autor] ICCP")
cierre(doc, "Documento sujeto a revision y firma. Trazabilidad: resultado_*.json.")
doc.save("Memoria.docx")
```

Funciones de figuras disponibles en `figuras_despacho.py`:
- `esquema_portico(...)`, `esquema_columna(...)` -> esquemas de carga en **pastel solido**.
- `diagrama_portico(...)`, `diagrama_columna(...)` -> diagramas N/V/M con **transparencia**.
- `grafico_aprovechamientos(items)` -> barras de eta con limite 1,0.
- `diag_member(...)` y la paleta pastel para diagramas a medida.

## Notas
- Para el detalle del entregable Word (campos, validacion) seguir tambien la skill `docx`.
- Esta skill complementa a las skills de calculo (Eurocodigos, CTE, instalaciones, obras
  lineales): aquellas producen los resultados; esta los **maqueta** con el formato del despacho.
- `references/formato-memoria-calculo.md` es la especificacion completa y mandatoria del formato.

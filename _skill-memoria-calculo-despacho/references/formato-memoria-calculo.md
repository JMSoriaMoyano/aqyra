# Formato de despacho — Memoria de cálculo

> **Capa transversal de formato.** Define la estructura, el estilo y el descargo de
> responsabilidad comunes a TODAS las memorias de cálculo del despacho, sea cual sea la
> disciplina (estructuras, instalaciones, obras lineales, CTE/cumplimiento).
>
> Las skills de memoria (`estructuras-eurocodigos:memoria-calculo`,
> `instalaciones:*`, `obras-lineales:*`, `cte-documentos-basicos:memoria-cte`) y los
> agentes deben **leer este archivo y aplicarlo** al redactar cualquier memoria.
> Plantilla Word maestra asociada: **`Plantilla_Memoria_Calculo.docx`** (misma carpeta).
>
> Mantener formato y ubicación estables (raíz del proyecto). Última revisión: 2026-06-23.

---

## 1. Principios

- **Idioma:** español técnico **preciso**, sin ambigüedad ni florituras. Frases cortas,
  afirmativas y cuantificadas. Sistema de unidades SI (kN, m, MPa, mm).
- **Prioridad de la información gráfica:** cuando exista y sea posible, **anteponer el
  recurso gráfico** (esquema, sección, diagrama de esfuerzos, gráfico de aprovechamientos,
  vista/coloreado del visor IFC) al texto y a la tabla. La tabla acompaña a la figura, no
  la sustituye. En particular:
  - **Priorizar los diagramas de esfuerzos** (N, V, M y, si procede, deformada) frente a
    su descripción numérica.
  - **Representar esquemas de cargas** (cargas, apoyos, empujes, reacciones) siempre que
    sea razonable, como apoyo de las hipótesis.
  - **Estilo gráfico:** **tonos pastel** en diagramas y esquemas. Las **transparencias
    (opacidad reducida) se usan SOLO en los diagramas de esfuerzos**, no en los esquemas
    (los esquemas de cargas y secciones van en pastel **sólido**).
- **Coeficientes explícitos en las hipótesis:** indicar en el apartado de acciones los
  **coeficientes de mayoración (γ)** y de **combinación/simultaneidad (ψ)** adoptados, con
  la combinación escrita (p. ej. 1,35·G + 1,50·Q) y su cláusula (EC0 §6.4.3 / IAP-11).
- **Trazabilidad total:** **toda afirmación importante debe poder rastrearse** a un
  cálculo (con su valor), a una cláusula de norma o a un anexo. Nada se afirma sin origen.
- **Toda memoria es predimensionado/asistencia** y debe ser **revisada y firmada por
  técnico competente** (Ingeniero de Caminos, Canales y Puertos / técnico colegiado).
  Este descargo va siempre en portada y en la primera página de contenido.
- **No inventar resultados:** usar únicamente los cálculos efectivamente realizados.
  Lo no resuelto se marca `[PENDIENTE]`; los parámetros no normalizados o sujetos al
  Anejo Nacional, `[confirmar AN]`.
- **Citar, no reproducir:** referenciar la cláusula (p. ej. EC2 §6.4.4, IAP-11 §4.1,
  CTE DB-SE-AE Tabla 3.1) sin copiar el texto íntegro de la norma.
- **Trazabilidad:** cada resultado relevante indica de dónde sale (modelo, IFC, skill,
  versión del plugin/motor) para poder reproducirlo.
- **Coherencia con la memoria del proyecto:** tomar datos y decisiones ya registrados en
  `criterios-despacho.md` (raíz) y en la memoria del proyecto (subcarpeta) para no
  recalcular ni contradecir.

---

## 2. Identidad y estilo (Word)

| Elemento | Criterio |
|---|---|
| Tamaño de página | A4 vertical (210 × 297 mm); márgenes 25 mm |
| Tipografía | **Arial 11 pt** cuerpo; **Arial 9,5 pt dentro de tablas**; títulos en Arial negrita |
| Párrafos | **Justificados a ambos lados** (los títulos, alineados a la izquierda) |
| Color corporativo | Azul `#1F4E79` (títulos H1/H2 y filetes); rojo `#B00000` para el descargo |
| Encabezado | Proyecto · Disciplina · Documento (a la izquierda) |
| Pie | Despacho/autor · "Predimensionado" · **Pág. X de Y** |
| Índice | Tabla de contenidos automática tras la portada |
| Numeración | Secciones decimales (1, 1.1, 1.2…); tablas y figuras numeradas con leyenda |
| Tablas | **Sin cebreado**; **cabecera con fondo azul claro** `#D9E2F3` que **se repite al cortarse la tabla por un salto de página**; **sin líneas verticales** salvo en la cabecera; texto Arial 9,5. Resultados con **veredicto y aprovechamiento** |
| Figuras | Numeradas con leyenda; **se priorizan** frente a descripciones largas (ver §1) |
| Veredicto | En la **carátula** y en conclusiones. **CUMPLE en verde** `#2E7D32` si es favorable, **NO CUMPLE en rojo** `#B00000` si es desfavorable; aprovechamiento η = E_d/R_d con 3 cifras |

---

## 3. Estructura común (esqueleto obligatorio)

Toda memoria sigue este orden. Las secciones marcadas (D) se particularizan por
disciplina según el anexo del §4.

**Portada** — Título de la memoria · proyecto · emplazamiento · disciplina/elemento ·
autor y nº de colegiado · fecha y revisión · **descargo** (predimensionado, revisar y
firmar por técnico competente).

**Índice** — automático.

1. **Objeto y alcance** — qué se calcula, qué queda fuera (ganchos diferidos).
2. **Normativa aplicada** — marco normativo y Anejo Nacional (ver §4 por disciplina).
3. **Datos de partida** (D) — geometría, materiales, terreno/medio, origen del modelo
   (IFC + parser/versión), hipótesis.
4. **Bases de cálculo / acciones / demanda** (D) — acciones y combinaciones (estructuras),
   bases de demanda y simultaneidad (instalaciones), hidrología/tráfico (obras lineales).
5. **Modelo e idealización** (D) — esquema de cálculo, software/motor y versión,
   discretización, condiciones de contorno.
6. **Cálculo y resultados** (D) — esfuerzos/caudales/presiones; tablas de resultados.
7. **Comprobaciones** (D) — por elemento/tramo, con cláusula citada, valor de cálculo,
   resistencia/límite, **aprovechamiento** y **veredicto**.
8. **Conclusiones y limitaciones** — veredicto global, aprovechamiento gobernante,
   pendientes `[PENDIENTE]` y `[confirmar AN]`.
9. **Anexos** (opcional) — listados, gráficas, planos de armado/esquemas, salidas del
   visor/IFC, write-back de resultados.

**Pie de cierre** — nota de verificación: *documento sujeto a revisión y firma de
técnico competente*.

---

## 4. Anexos por disciplina (particularización de las secciones D)

### 4.1 Estructuras (Eurocódigos + AN España)
- **Normativa:** EC0 (EN 1990), EC1 (EN 1991), EC2/EC3/EC4/EC5 según material, EC7
  (cimentaciones), EC8 (sismo); IAP-11 en puentes de carretera; CTE DB-SE para
  edificación. Sismo: NCSE-02 `[confirmar AN]`.
- **Datos:** materiales (hormigón C__/__, B500S, acero S___), clase de exposición,
  recubrimientos, categoría de uso.
- **Acciones:** permanentes, sobrecargas de uso, viento, nieve, térmicas; combinaciones
  ELU/ELS (γ_G=1,35, γ_Q=1,50 `[confirmar AN]`); sísmica (E + ΣG_k + Σψ2·Q_k).
- **Modelo:** motor (`motor-calculo` / `motor-fem`, contrato y versión), tipo de
  idealización (barra/lámina/emparrillado/Winkler).
- **Comprobaciones:** ELU (flexión, cortante, punzonamiento, pandeo, M-N), ELS (flecha
  L/300 total y L/500 activa, fisuración, descompresión en pretensado), EC7 (vuelco,
  deslizamiento, hundimiento).

### 4.2 Instalaciones (red a presión / eléctrica)
- **Normativa:** RIPCI, UNE-EN 671 / UNE-EN 12845 (PCI); REBT e ITC-BT (eléctrica);
  RITE (térmicas); CTE DB-HS4/HS5 cuando aplique.
- **Bases de demanda:** caudales y simultaneidad (PCI: BIE/rociadores por clase de
  riesgo); previsión de cargas y grado de electrificación (eléctrica).
- **Modelo:** grafo de red (parser `iso19650-openbim` + versión), solver
  (Darcy-Weisbach / Hardy-Cross en mal
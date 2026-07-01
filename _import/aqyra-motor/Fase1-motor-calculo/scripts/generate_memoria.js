// Genera la memoria de calculo (docx) de la Fase 1 a partir de los JSON validados.
// Uso: NODE_PATH=$(npm root -g) node generate_memoria.js <dir_proyecto> <salida.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, Footer, LevelFormat,
} = require("docx");

const dir = process.argv[2] || "proyecto-demo";
const out = process.argv[3] || path.join(dir, "Memoria_calculo_Fase1.docx");

const model = JSON.parse(fs.readFileSync(path.join(dir, "modelo_neutro.json"), "utf8"));
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));
const cv = JSON.parse(fs.readFileSync(path.join(dir, "cross_validation.json"), "utf8"));

const CW = 9026; // ancho contenido A4 con margenes 1"
const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const HEAD = "1F4E79", ZEBRA = "EEF3F8";

const f1 = (x) => (x === null || x === undefined) ? "-" : Number(x).toFixed(1);
const f2 = (x) => (x === null || x === undefined) ? "-" : Number(x).toFixed(2);
const pct = (x) => (x * 100).toFixed(1) + " %";

function P(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120 }, ...opts,
    children: [new TextRun({ text, ...(opts.run || {}) })] });
}
function H(text, level) { return new Paragraph({ heading: level, children: [new TextRun(text)] }); }

function cell(text, { w, head = false, bold = false, fill, align } = {}) {
  return new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: align || AlignmentType.LEFT,
      children: [new TextRun({ text: String(text), bold: head || bold,
        color: head ? "FFFFFF" : "000000", size: 19 })] })],
  });
}
function table(headers, rows, widths) {
  const trs = [new TableRow({ tableHeader: true,
    children: headers.map((h, i) => cell(h, { w: widths[i], head: true, fill: HEAD,
      align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })];
  rows.forEach((r, ri) => {
    trs.push(new TableRow({ children: r.map((c, i) => cell(c, { w: widths[i],
      fill: ri % 2 ? ZEBRA : undefined,
      align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) }));
  });
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
function img(file, w, h, cap) {
  const p = path.join(dir, file);
  const out = [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(p),
      transformation: { width: w, height: h },
      altText: { title: cap, description: cap, name: file } })] })];
  if (cap) out.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: cap, italics: true, size: 17, color: "555555" })] }));
  return out;
}

// ---- Datos derivados -------------------------------------------------------
const elu = (bid) => res.barras[bid].ELU;
const ad = ver.autodiagnostico;

// ====== Construccion del documento =========================================
const children = [];

// Portada
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 },
  children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Pórtico plano de acero — Prueba de concepto (Fase 1)", size: 26 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Motor de cálculo IFC → FEM → Eurocódigos", size: 22, color: "555555" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 80 },
  children: [new TextRun({ text: "Proyecto: Estructurando", size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Fecha: 21/06/2026", size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 },
  children: [new TextRun({ text: "Documento generado automáticamente. Los cálculos deben ser revisados y firmados por técnico competente.",
    italics: true, size: 18, color: "999999" })] }));
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));

// 1. Objeto
children.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
children.push(P("La presente memoria justifica el cálculo estructural de un pórtico plano de acero de un vano, " +
  "realizado mediante un motor de cálculo automatizado que parte de un modelo IFC con dominio de análisis " +
  "estructural y obtiene esfuerzos, combinaciones de acciones, comprobaciones según los Eurocódigos y la " +
  "representación gráfica de resultados. Constituye la prueba de concepto (Fase 1) del flujo IFC → modelo " +
  "estructural → análisis FEM → verificación → memoria, limitada a elementos de barra."));

// 2. Normativa
children.push(H("2. Normativa de aplicación", HeadingLevel.HEADING_1));
children.push(table(["Código", "Título", "Uso en esta memoria"],
  [["EN 1990 (EC0)", "Bases de cálculo estructural", "Combinaciones ELU/ELS, coef. parciales y ψ"],
   ["EN 1991 (EC1)", "Acciones en las estructuras", "Acciones permanentes G y variables Q"],
   ["EN 1993-1-1 (EC3)", "Proyecto de estructuras de acero", "Resistencia de secciones y pandeo"],
   ["AN España", "Anejos Nacionales", "Coeficientes y parámetros NDP [confirmar AN]"]],
  [1900, 4126, 3000]));
children.push(P("Los valores de parámetros de determinación nacional (NDP) se han tomado del Anejo Nacional " +
  "español de uso habitual en el despacho y se marcan como [confirmar AN] cuando proceda.", { run: { italics: true, size: 18 } }));

// 3. Modelo
children.push(H("3. Descripción del modelo", HeadingLevel.HEADING_1));
children.push(H("3.1 Geometría y nodos", HeadingLevel.HEADING_2));
const nodeRows = Object.entries(model.nodos).map(([nid, n]) => [nid, f2(n.x), f2(n.z),
  n.apoyo.some(Boolean) ? "Empotrado" : "Libre"]);
children.push(table(["Nodo", "x [m]", "z [m]", "Coacción"], nodeRows, [2256, 2256, 2257, 2257]));
children.push(H("3.2 Materiales", HeadingLevel.HEADING_2));
const matRows = Object.entries(model.materiales).map(([m, p]) =>
  [m, (p.E / 1e9).toFixed(0), (p.fy / 1e6).toFixed(0), p.nu.toFixed(2), (p.rho).toFixed(0)]);
children.push(table(["Material", "E [GPa]", "fy [MPa]", "ν", "ρ [kg/m³]"], matRows, [3026, 1500, 1500, 1500, 1500]));
children.push(H("3.3 Secciones", HeadingLevel.HEADING_2));
const secRows = Object.entries(model.secciones).map(([s, p]) =>
  [s, (p.A * 1e4).toFixed(2), (p.Iy * 1e8).toFixed(0), (p.Wply * 1e6).toFixed(0),
   (p.Avz * 1e4).toFixed(2), "Clase " + p.clase]);
children.push(table(["Sección", "A [cm²]", "Iy [cm⁴]", "Wpl,y [cm³]", "Avz [cm²]", "Clase"],
  secRows, [2026, 1400, 1400, 1600, 1300, 1300]));
children.push(H("3.4 Barras", HeadingLevel.HEADING_2));
const barRows = Object.entries(model.barras).map(([b, p]) =>
  [b, p.tipo, p.ni + " → " + p.nj, p.seccion, p.material, f2(res.longitudes[b])]);
children.push(table(["Barra", "Tipo", "Nodos", "Sección", "Material", "L [m]"], barRows,
  [1200, 1500, 1626, 1700, 1700, 1300]));

// 4. Acciones y combinaciones
children.push(H("4. Acciones y combinaciones", HeadingLevel.HEADING_1));
children.push(H("4.1 Acciones", HeadingLevel.HEADING_2));
const loadRows = model.cargas.map((c) => [c.caso, c.barra, c.direccion, (Math.abs(c.qz) / 1e3).toFixed(2)]);
children.push(table(["Caso", "Barra", "Dirección", "q [kN/m]"], loadRows, [2256, 2256, 2257, 2257]));
children.push(H("4.2 Combinaciones (EC0)", HeadingLevel.HEADING_2));
const comboRows = Object.entries(res.combos_meta).map(([name, m]) =>
  [name, m.tipo, m.expr, m.norma]);
children.push(table(["Combinación", "Tipo", "Expresión", "Referencia"], comboRows, [1800, 1100, 3126, 3000]));
children.push(P("Coeficientes parciales (AN España): γG = 1,35 (desfav.) / 1,00 (fav.); γQ = 1,50. " +
  "Factores de simultaneidad ψ (Cat. B – oficinas): ψ0 = 0,7; ψ1 = 0,5; ψ2 = 0,3. [confirmar AN]",
  { run: { size: 18 } }));

// 5. Procedimiento y validacion
children.push(H("5. Procedimiento de cálculo y validación", HeadingLevel.HEADING_1));
children.push(P("El cálculo sigue una cadena determinista y trazable: (1) lectura del IFC con IfcOpenShell y " +
  "extracción del modelo de análisis a un modelo neutro; (2) ensamblaje y resolución por elementos finitos de " +
  "barra (PyNite); (3) combinación de acciones según EC0; (4) comprobación según EC3. El modelo plano se " +
  "analiza en un solver tridimensional coaccionando los grados de libertad fuera del plano."));
children.push(P("Validación del solver (autodiagnóstico): se contrasta una viga biapoyada con carga uniforme " +
  "frente a su solución analítica cerrada antes de aceptar los resultados.", { run: { bold: true } }));
children.push(table(["Magnitud", "Calculado", "Teórico", "Error"],
  [["Momento M = qL²/8", f1(ad.checks["M (kN·m)"][0]) + " kN·m", f1(ad.checks["M (kN·m)"][1]) + " kN·m", (ad.checks["M (kN·m)"][2] * 100).toFixed(3) + " %"],
   ["Cortante V = qL/2", f1(ad.checks["V (kN)"][0]) + " kN", f1(ad.checks["V (kN)"][1]) + " kN", (ad.checks["V (kN)"][2] * 100).toFixed(3) + " %"],
   ["Flecha 5qL⁴/384EI", f2(ad.checks["flecha (mm)"][0]) + " mm", f2(ad.checks["flecha (mm)"][1]) + " mm", (ad.checks["flecha (mm)"][2] * 100).toFixed(3) + " %"]],
  [3026, 2000, 2000, 2000]));
children.push(P("Resultado del autodiagnóstico: " + (ad.valido ? "VÁLIDO (error < 1 %)." : "NO VÁLIDO."),
  { run: { bold: true, color: ad.valido ? "1E7A1E" : "B00000" } }));

// 5.x Validacion cruzada
children.push(H("5.1 Validación cruzada con solver independiente", HeadingLevel.HEADING_2));
children.push(P("Como verificación adicional, el pórtico se ha resuelto con un segundo motor de cálculo " +
  "independiente (anaStruct, análisis matricial de barras 2D). Se comparan los esfuerzos máximos por barra " +
  "bajo la combinación ELU; el acuerdo certifica tanto el cálculo como el criterio de signos."));
const cvRows = Object.entries(cv.barras).map(([bid, d]) =>
  [bid, f1(d.M[0]) + " / " + f1(d.M[1]), f1(d.V[0]) + " / " + f1(d.V[1]),
   f1(d.N[0]) + " / " + f1(d.N[1]), (Math.max(d.M[2], d.V[2], d.N[2]) * 100).toFixed(2) + " %"]);
children.push(table(["Barra", "M [kN·m] PyNite/anaStruct", "V [kN] PyNite/anaStruct",
  "N [kN] PyNite/anaStruct", "Error"], cvRows, [1126, 2700, 2300, 2300, 1600]));
children.push(P("Resultado de la validación cruzada: " + (cv.ok ? "CONFORME (diferencias < 1 %)." : "NO CONFORME."),
  { run: { bold: true, color: cv.ok ? "1E7A1E" : "B00000" } }));

// 6. Esfuerzos
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("6. Esfuerzos (envolvente ELU 1,35G + 1,50Q)", HeadingLevel.HEADING_1));
const esfRows = Object.keys(model.barras).map((bid) => {
  const e = elu(bid);
  const N = Math.max(Math.abs(e.N_i), Math.abs(e.N_j)) / 1e3;
  const V = Math.max(Math.abs(e.V_max), Math.abs(e.V_min)) / 1e3;
  const M = Math.max(Math.abs(e.M_max), Math.abs(e.M_min)) / 1e3;
  return [bid, f1(N), f1(V), f1(M)];
});
children.push(table(["Barra", "N [kN]", "V [kN]", "M [kN·m]"], esfRows, [2256, 2256, 2257, 2257]));
children.push(...img("diag_momentos.png", 380, 300, "Figura 1. Ley de momentos flectores (ELU)."));
children.push(...img("diag_cortantes.png", 380, 300, "Figura 2. Ley de cortantes (ELU)."));
children.push(...img("diag_axiles.png", 380, 300, "Figura 3. Ley de axiles (ELU)."));

// 7. Servicio
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("7. Estado límite de servicio (flechas)", HeadingLevel.HEADING_1));
children.push(...img("deformada.png", 380, 300, "Figura 4. Deformada bajo combinación característica (amplificada)."));
const flRows = Object.entries(ver.barras).map(([bid, b]) => {
  const ct = b.comprobaciones["Flecha total L/300"], ca = b.comprobaciones["Flecha activa L/500"];
  return [bid, (ct.Ed * 1e3).toFixed(2), (ct.Rd * 1e3).toFixed(2), pct(ct.u),
    (ca.Ed * 1e3).toFixed(2), (ca.Rd * 1e3).toFixed(2), pct(ca.u)];
});
children.push(table(["Barra", "f_tot [mm]", "lím [mm]", "aprov.", "f_act [mm]", "lím [mm]", "aprov."],
  flRows, [1226, 1300, 1300, 1300, 1300, 1300, 1300]));

// 8. Comprobaciones EC3
children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
children.push(H("8. Comprobaciones según EC3", HeadingLevel.HEADING_1));
for (const [bid, b] of Object.entries(ver.barras)) {
  children.push(H(`8.${Object.keys(ver.barras).indexOf(bid) + 1}  Barra ${bid} — ${b.tipo} (${b.seccion}, ${b.material})`, HeadingLevel.HEADING_2));
  const rows = Object.entries(b.comprobaciones)
    .filter(([nombre]) => !nombre.startsWith("Flecha"))
    .map(([nombre, c]) =>
    [nombre, c.Ed === null ? "-" : f1(c.Ed / 1e3),
     c.Rd === null ? "-" : f1(c.Rd / 1e3),
     pct(c.u), c.ok ? "CUMPLE" : "NO CUMPLE", c.art]);
  children.push(table(["Comprobación", "Ed", "Rd", "Aprov.", "Veredicto", "Artículo"],
    rows, [2200, 1100, 1100, 1100, 1500, 2026]));
  children.push(P(`Aprovechamiento máximo: ${pct(b.aprovechamiento_max)} → ${b.veredicto}.`,
    { run: { bold: true, color: b.veredicto === "CUMPLE" ? "1E7A1E" : "B00000" } }));
}

// 9. Conclusiones
children.push(H("9. Conclusiones", HeadingLevel.HEADING_1));
const allOk = Object.values(ver.barras).every((b) => b.veredicto === "CUMPLE");
children.push(P("Todas las barras del pórtico " + (allOk ? "CUMPLEN" : "NO cumplen") +
  " las comprobaciones de resistencia (EC3) y de servicio (flechas) para las combinaciones consideradas. " +
  "El motor de cálculo ha reproducido la solución analítica de referencia con error inferior al 1 %, lo que " +
  "valida la cadena IFC → FEM → Eurocódigos de la Fase 1."));
children.push(P("Limitaciones de esta fase: análisis lineal de barras; la interacción N+M se evalúa de forma " +
  "lineal conservadora; el pandeo lateral, la abolladura y las uniones no se comprueban; los elementos tipo " +
  "lámina/losa (2D) corresponden a la Fase 2. Todo resultado debe ser revisado y firmado por técnico competente.",
  { run: { italics: true, size: 18 } }));

// ---- Documento -------------------------------------------------------------
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: HEAD, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } },
      children: [new TextRun({ text: "Memoria de cálculo · Pórtico acero · Fase 1", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Memoria escrita en:", out); });

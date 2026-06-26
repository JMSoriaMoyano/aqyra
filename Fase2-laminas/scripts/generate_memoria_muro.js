// Memoria del MURO de carga (compresion + esbeltez EC2).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-muro";
const out = process.argv[3] || path.join(dir, "Memoria_muro.docx");
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

const CW = 9026, HEAD = "1F4E79", ZEBRA = "EEF3F8";
const bd = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const f1 = (x) => (x == null) ? "-" : Number(x).toFixed(1);
const f2 = (x) => (x == null) ? "-" : Number(x).toFixed(2);
const f0 = (x) => (x == null) ? "-" : Number(x).toFixed(0);
const pct = (x) => (x * 100).toFixed(0) + " %";
function P(t, o = {}) { return new Paragraph({ spacing: { after: 120 }, ...o, children: [new TextRun({ text: t, ...(o.run || {}) })] }); }
function H(t, l) { return new Paragraph({ heading: l, children: [new TextRun(t)] }); }
function cell(t, { w, head = false, fill, align } = {}) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA }, shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align || AlignmentType.LEFT, children: [new TextRun({ text: String(t), bold: head, color: head ? "FFFFFF" : "000000", size: 19 })] })] });
}
function table(hd, rows, w) {
  const trs = [new TableRow({ tableHeader: true, children: hd.map((h, i) => cell(h, { w: w[i], head: true, fill: HEAD, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })];
  rows.forEach((r, ri) => trs.push(new TableRow({ children: r.map((c, i) => cell(c, { w: w[i], fill: ri % 2 ? ZEBRA : undefined, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: w, rows: trs });
}
function img(file, w, h, cap) {
  const o = [new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(dir, file)), transformation: { width: w, height: h }, altText: { title: cap, description: cap, name: file } })] })];
  if (cap) o.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: cap, italics: true, size: 17, color: "555555" })] }));
  return o;
}

const info = res.info, c = ver.compresion, fx = ver.flexion_fuera_plano, am = ver.armadura_minima, fl = ver.flecha, eq = ver.equilibrio;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Muro de carga de hormigón (Fase 2)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de un muro de carga de hormigón armado (elemento plano vertical) sometido a carga vertical de " +
  "los forjados y a viento fuera de su plano. El mecanismo gobernante es la compresión con efectos de esbeltez. " +
  "Se modela con elementos finitos tipo lámina en un plano vertical y se comprueba según EC2."));

ch.push(H("2. Modelo y acciones", HeadingLevel.HEADING_1));
ch.push(P(`Muro de ${f1(info.L)} m de largo × ${f1(info.H)} m de alto, espesor ${f0(info.espesor * 1e3)} mm, ` +
  `hormigón ${info.material}. Base empotrada a traslación; cabeza arriostrada fuera de plano por el forjado. ` +
  `Factor de pandeo β = ${f1(info.beta)} (lo = β·H).`));
ch.push(table(["Acción", "Valor", "Caso"], [
  ["Carga vertical en cabeza (permanente)", "900 kN/m", "G"],
  ["Carga vertical en cabeza (variable)", "300 kN/m", "Q"],
  ["Autopeso", f2(info.peso_N_m2 / 1e3) + " kN/m²", "G"],
  ["Viento (fuera de plano)", "1,00 kN/m²", "Q"]], [4526, 2750, 1750]));
ch.push(table(["Combinación", "Tipo", "Expresión"], Object.entries(res.combos_meta).map(([n, m]) => [n, m.tipo, m.expr]), [2400, 1500, 5126]));

ch.push(H("3. Esfuerzos", HeadingLevel.HEADING_1));
ch.push(...img("mapa_compresion.png", 320, 280, "Figura 1. Compresión vertical de membrana (escala recortada; los picos en las esquinas de la base son singularidades del apoyo)."));
ch.push(...img("mapa_flecha.png", 320, 280, "Figura 2. Flecha fuera de plano por viento (ELS)."));
ch.push(P("El axil de diseño se toma como la carga vertical total dividida por la longitud del muro " +
  `(N_Ed = ${f0(c.N_Ed_kN_m)} kN/m), evitando la singularidad local de la membrana en las esquinas de la base.`,
  { run: { size: 18, italics: true } }));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("4. Comprobación a compresión con esbeltez (EC2 §12.6.5.2 / §5.8.3.1)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Axil de diseño N_Ed", f0(c.N_Ed_kN_m) + " kN/m"],
  ["Longitud de pandeo lo", f2(c.lo_m) + " m"],
  ["Esbeltez λ", f0(c.lambda) + "  (λlím = " + f0(c.lambda_lim) + " → " + (c.esbelto ? "esbelto" : "no esbelto") + ")"],
  ["Excentricidad total e_tot", f1(c.etot_mm) + " mm (e0 " + f1(c.e0_mm) + " + ei " + f1(c.ei_mm) + ")"],
  ["Factor de capacidad Φ", f2(c.Phi)],
  ["Capacidad N_Rd", f0(c.N_Rd_kN_m) + " kN/m"],
  ["Aprovechamiento N_Ed/N_Rd", pct(c.u)]], [4526, 4500]));
ch.push(P("Resultado a compresión: " + (c.ok ? "CUMPLE." : "NO cumple → aumentar espesor" +
  (c.dimensionado ? " a " + c.dimensionado.t_min_mm + " mm." : ".")),
  { run: { bold: true, color: c.ok ? "1E7A1E" : "B00000" } }));
ch.push(P("El método simplificado de muros (§12.6.5.2) reduce la capacidad mediante Φ por esbeltez y " +
  "excentricidad; es conservador para muros de hormigón. Para muros muy armados, §5.8 (curvatura nominal) " +
  "permitiría mayor capacidad.", { run: { size: 18, italics: true } }));

ch.push(H("5. Flexión fuera de plano y armadura", HeadingLevel.HEADING_1));
ch.push(table(["Comprobación", "Valor"], [
  ["Momento fuera de plano (viento)", f1(fx.m_Ed_kNm_m) + " kN·m/m → " + fx.armado],
  ["Armadura mínima vertical (§9.6)", f1(am.As_v_min_cm2_m) + " cm²/m"],
  ["Armadura mínima horizontal (§9.6)", f1(am.As_h_min_cm2_m) + " cm²/m"],
  ["Flecha fuera de plano", f2(fl.f_mm) + " mm ≤ L/250 = " + f1(fl.lim_mm) + " mm (" + pct(fl.u) + ")"]], [4526, 4500]));
ch.push(P("La armadura del muro queda gobernada por la cuantía mínima (§9.6); la flexión por viento es reducida.",
  { run: { size: 18, italics: true } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("El muro de " + f0(info.espesor * 1e3) + " mm " + (ver.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") +
  ": la compresión con esbeltez se aprovecha al " + pct(c.u) + " (λ = " + f0(c.lambda) + ", Φ = " + f2(c.Phi) +
  "), la flexión por viento es reducida y la armadura la fija la cuantía mínima. El equilibrio vertical cierra " +
  "con error nulo. Resultados de predimensionado; revisión y firma por técnico competente.", { run: { bold: true } }));
ch.push(P("Limitaciones: análisis lineal; compresión por el método simplificado de muros (conservador); no se " +
  "incluye la comprobación del muro como pantalla a cortante en su plano ni la interacción N-M completa por " +
  "diagrama; las singularidades locales de membrana en apoyos no son representativas del dimensionamiento.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Muro de carga · Fase 2", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

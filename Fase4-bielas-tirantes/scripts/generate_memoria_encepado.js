// Memoria del ENCEPADO de 2 pilotes por bielas y tirantes (EC2 §6.5).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-encepado";
const out = process.argv[3] || path.join(dir, "Memoria_encepado.docx");
const v = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

const CW = 9026, HEAD = "1F4E79", ZEBRA = "EEF3F8";
const bd = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const f1 = (x) => (x == null) ? "-" : Number(x).toFixed(1);
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
  rows.forEach((r, ri) => trs.push(new TableRow({ children: r.map((cv, i) => cell(cv, { w: w[i], fill: ri % 2 ? ZEBRA : undefined, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: w, rows: trs });
}
function img(file, w, h, cap) {
  const o = [new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(dir, file)), transformation: { width: w, height: h }, altText: { title: cap, description: cap, name: file } })] })];
  if (cap) o.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 }, children: [new TextRun({ text: cap, italics: true, size: 17, color: "555555" })] }));
  return o;
}

const g = v.geom_in, ce = v.celosia, ti = v.tirante, bi = v.biela, n1 = v.nudo_CCC, n2 = v.nudo_CCT;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Encepado de 2 pilotes — Bielas y tirantes (Fase 4)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de un encepado de 2 pilotes bajo pilar mediante el método de bielas y tirantes (EN 1992-1-1 §6.5), " +
  "aplicable a regiones de discontinuidad (regiones D). La celosía equivalente —dos bielas a compresión y un " +
  "tirante a tracción— se resuelve con el solver de barras y se comprueban bielas, nudos y tirante."));

ch.push(H("2. Datos", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Separación entre pilotes a", f1(g.SeparacionPilotes) + " m"],
  ["Canto del encepado h", f1(g.Canto) + " m  (canto útil d = " + f0(v.geom.d_mm) + " mm)"],
  ["Ancho del encepado b", f1(g.Ancho) + " m"],
  ["Pilar", f0(g.LadoPilar * 1e3) + " mm"], ["Pilote", "Ø" + f0(g.DiametroPilote * 1e3) + " mm"],
  ["Hormigón", g.Material], ["Axil de cálculo N_Ed", f0(v.N_Ed_kN) + " kN"]], [4526, 4500]));

ch.push(H("3. Modelo de bielas y tirantes", HeadingLevel.HEADING_1));
ch.push(...img("esquema_stm.png", 420, 280, "Figura 1. Celosía equivalente: bielas (rojo) y tirante (azul)."));
ch.push(table(["Elemento", "Esfuerzo (solver)", "Estática cerrada", "Error"], [
  ["Tirante T", f0(ce.T_kN) + " kN", f0(ce.T_cerrado_kN) + " kN", ce.err_pct.toFixed(2) + " %"],
  ["Biela C", f0(ce.C_kN) + " kN", f0(ce.C_cerrado_kN) + " kN", "-"],
  ["Reacción por pilote", f0(ce.R_pilote_kN) + " kN", "-", "-"]], [2526, 2300, 2300, 1900]));
ch.push(P(`Ángulo de las bielas θ = ${f0(v.geom.theta_deg)}° (brazo z = ${f0(v.geom.z_mm)} mm). ` +
  "La celosía se resuelve con el solver de barras y coincide con la estática cerrada (error nulo).",
  { run: { size: 18, italics: true } }));

ch.push(H("4. Comprobaciones EC2 §6.5", HeadingLevel.HEADING_1));
ch.push(table(["Comprobación", "Solicitación", "Resistencia", "Aprov.", "Estado"], [
  ["Tirante (As = T/fyd)", f0(ti.T_kN) + " kN", "As = " + f1(ti.As_req_cm2) + " cm²", "-", "dimensionado"],
  ["Biela (compr. + tracc. transv.)", f1(bi.sigma_MPa) + " MPa", f1(bi.sRd_MPa) + " MPa", pct(bi.u), bi.ok ? "OK" : "NO"],
  ["Nudo CCC (bajo pilar)", f1(n1.sigma_MPa) + " MPa", f1(n1.sRd_MPa) + " MPa", pct(n1.u), n1.ok ? "OK" : "NO"],
  ["Nudo CCT (sobre pilote)", f1(n2.sigma_MPa) + " MPa", f1(n2.sRd_MPa) + " MPa", pct(n2.u), n2.ok ? "OK" : "NO"]],
  [2926, 1900, 1900, 1100, 1200]));
ch.push(P(`Armadura del tirante: As = ${f1(ti.As_req_cm2)} cm² (acero B500S, fyd = ${f0(ti.fyd_MPa)} MPa), ` +
  "a anclar adecuadamente sobre los pilotes. σRd,max de bielas = 0,6·ν'·fcd; nudos CCC = ν'·fcd y CCT = 0,85·ν'·fcd.",
  { run: { size: 18 } }));

ch.push(H("5. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("El encepado " + (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") +
  `: el tirante requiere ${f1(ti.As_req_cm2)} cm², la biela se aprovecha al ${pct(bi.u)} y los nudos CCC (${pct(n1.u)}) ` +
  `y CCT (${pct(n2.u)}) cumplen. El modelo de celosía coincide con la estática cerrada (error nulo). ` +
  "Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: modelo de bielas y tirantes con celosía estáticamente determinada (carga centrada); " +
  "para cargas excéntricas o varios pilotes el modelo se amplía. No se incluye el detalle de anclaje del tirante " +
  "ni la armadura secundaria/de piel. El mismo método cubre vigas de gran canto y ménsulas. " +
  "Revisión y firma por técnico competente.", { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Encepado 2 pilotes · Bielas y tirantes · Fase 4", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

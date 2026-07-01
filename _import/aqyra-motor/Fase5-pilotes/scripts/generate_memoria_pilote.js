// Memoria del PILOTE (EC7 axil + lateral viga-muelles + EC2 seccion).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-pilote";
const out = process.argv[3] || path.join(dir, "Memoria_pilote.docx");
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

const info = v.info, a = v.axil_ec7, lt = v.lateral, s = v.seccion_ec2;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Pilote de cimentación profunda (Fase 5)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de un pilote de hormigón armado bajo carga vertical y horizontal en cabeza. Se comprueban la " +
  "capacidad axil geotécnica (EC7), el comportamiento lateral mediante el modelo de viga sobre muelles " +
  "horizontales (módulo de balasto) y la sección de hormigón a flexo-compresión (EC2)."));

ch.push(H("2. Datos", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Pilote", "Ø" + f0(info.D * 1e3) + " mm, L = " + f1(info.L) + " m, " + info.material],
  ["Módulo de balasto horizontal kh", f1(info.kh / 1e6) + " MN/m³"],
  ["Resistencias unitarias del terreno", "fuste y punta según estudio geotécnico [confirmar]"]], [3526, 5500]));

ch.push(H("3. Capacidad axil (EC7)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Resistencia por fuste R_s,k", f0(a.Rs_k_kN) + " kN"],
  ["Resistencia por punta R_b,k", f0(a.Rb_k_kN) + " kN"],
  ["Resistencia de cálculo R_c,d", f0(a.Rc_d_kN) + " kN"],
  ["Axil de cálculo N_Ed", f0(a.N_Ed_kN) + " kN"],
  ["Aprovechamiento N_Ed/R_c,d", pct(a.u)]], [5026, 4000]));
ch.push(P("Resultado EC7: " + (a.ok ? "CUMPLE." : "NO cumple → alargar el pilote o aumentar diámetro."),
  { run: { bold: true, color: a.ok ? "1E7A1E" : "B00000" } }));
ch.push(P("R_c,d = R_s,k/γ_s + R_b,k/γ_b (γ = 1,10). Las resistencias unitarias del terreno proceden del estudio " +
  "geotécnico. [confirmar AN / enfoque de cálculo]", { run: { size: 18, italics: true } }));

ch.push(H("4. Comportamiento lateral (viga sobre muelles)", HeadingLevel.HEADING_1));
ch.push(...img("diag_pilote.png", 380, 290, "Figura 1. Momento flector y deformada lateral en profundidad."));
ch.push(table(["Parámetro", "Valor"], [
  ["Momento flector máximo M_Ed", f0(lt.M_Ed_kNm) + " kN·m"],
  ["Cortante máximo V_Ed", f0(lt.V_Ed_kN) + " kN"],
  ["Flecha en cabeza", f1(lt.flecha_cabeza_mm) + " mm ≤ " + f0(lt.lim_mm) + " mm (" + pct(lt.u) + ")"]], [5026, 4000]));
ch.push(P("Resultado lateral: " + (lt.ok ? "flecha de cabeza dentro del límite de servicio." : "flecha excesiva → rigidizar."),
  { run: { bold: true, color: lt.ok ? "1E7A1E" : "C07A00" } }));

ch.push(H("5. Sección de hormigón (EC2, flexo-compresión)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Excentricidad e/D", f1(s.e_sobre_D * 100) / 100 + "  (e = " + f0(s.e_mm) + " mm)"],
  ["Armadura mínima (EN 1536)", f1(s.As_min_cm2) + " cm²  (0,5 % A_c)"],
  ["Capacidad axil N_Rd", f0(s.N_Rd_kN) + " kN (aprov. " + pct(s.u_N) + ")"],
  ["Capacidad a flexión M_Rd", f0(s.M_Rd_kNm) + " kN·m (aprov. " + pct(s.u_M) + ")"]], [5026, 4000]));
ch.push(P("La sección trabaja a flexo-compresión con excentricidad reducida; la armadura la fija la cuantía " +
  "mínima de pilotes. La capacidad N-M se evalúa de forma simplificada; el diagrama de interacción completo la refina.",
  { run: { size: 18, italics: true } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P(`El pilote Ø${f0(info.D * 1e3)} mm de ${f1(info.L)} m ` +
  (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") +
  `: capacidad axil EC7 al ${pct(a.u)}, flecha lateral de cabeza al ${pct(lt.u)} del límite, y la sección a ` +
  `flexo-compresión cubierta con la armadura mínima (${f1(s.As_min_cm2)} cm²). El modelo lateral de viga sobre ` +
  "muelles cierra el equilibrio con error nulo. Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: capacidad axil y comportamiento lateral desacoplados (predimensionado); balasto y " +
  "resistencias unitarias del estudio geotécnico; no se incluye rozamiento negativo, efecto grupo, ni P-Δ; el " +
  "encepado se calcula por bielas y tirantes (módulo aparte). Revisión y firma por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Pilote · Fase 5", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

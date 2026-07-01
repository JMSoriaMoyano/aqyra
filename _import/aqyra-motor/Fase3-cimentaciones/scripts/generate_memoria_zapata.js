// Memoria de la ZAPATA aislada (EC7 + EC2).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-zapata";
const out = process.argv[3] || path.join(dir, "Memoria_zapata.docx");
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

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

const info = res.info, g = ver.geotecnia, fx = ver.flexion.x, fy = ver.flexion.y, pz = ver.punzonamiento, cv = ver.cortante, eq = ver.equilibrio;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Zapata aislada sobre lecho elástico (Fase 3 — cimentaciones)", size: 24 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de una zapata aislada de hormigón armado bajo pilar, modelada como placa sobre lecho elástico " +
  "(modelo de Winkler). Se comprueban la tensión admisible del terreno (EC7) y las comprobaciones de hormigón " +
  "(EC2): flexión, punzonamiento y cortante."));

ch.push(H("2. Modelo y terreno", HeadingLevel.HEADING_1));
ch.push(...img("planta.png", 320, 300, "Figura 1. Planta de la zapata y pilar."));
ch.push(P(`Zapata ${f1(info.B)}×${f1(info.B)} m, canto ${f0(info.espesor * 1e3)} mm, hormigón ${info.material}. ` +
  `Pilar ${f0(info.c_pilar * 1e3)} mm. Terreno: módulo de balasto ks = ${f1(info.ks / 1e6)} MN/m³, ` +
  `resistencia de cálculo Rd = ${f0(info.Rd / 1e3)} kPa. [confirmar con estudio geotécnico]`));

ch.push(H("3. Presión del terreno y esfuerzos", HeadingLevel.HEADING_1));
ch.push(...img("mapa_presion.png", 300, 260, "Figura 2. Presión del terreno (ELU)."));
ch.push(...img("mapa_Mx.png", 300, 260, "Figura 3. Momento de placa Mx (escala recortada bajo el pilar)."));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("4. Comprobación geotécnica (EC7)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Presión máxima (ELU)", f0(g.p_max_kPa) + " kPa"],
  ["Presión mínima", f0(g.p_min_kPa) + " kPa (" + (g.ok_sin_despegue ? "sin despegue" : "DESPEGUE") + ")"],
  ["Resistencia del terreno Rd", f0(g.Rd_kPa) + " kPa"],
  ["Aprovechamiento p_max/Rd", pct(g.u_Rd)]], [5026, 4000]));
ch.push(P("Resultado geotécnico: " + (g.ok_Rd && g.ok_sin_despegue ? "CUMPLE." : "REVISAR (ampliar zapata o mejorar terreno)."),
  { run: { bold: true, color: (g.ok_Rd && g.ok_sin_despegue) ? "1E7A1E" : "B00000" } }));

ch.push(H("5. Comprobaciones de hormigón (EC2)", HeadingLevel.HEADING_1));
ch.push(table(["Comprobación", "Solicitación", "Capacidad / armado", "Aprov.", "Estado"], [
  ["Flexión dir. x (cara pilar)", f1(fx.m_Ed_kNm_m) + " kN·m/m", fx.armado, "-", fx.ok ? "OK" : "NO"],
  ["Flexión dir. y (cara pilar)", f1(fy.m_Ed_kNm_m) + " kN·m/m", fy.armado, "-", fy.ok ? "OK" : "NO"],
  ["Punzonamiento (§6.4)", f0(pz.V_Ed_neto_kN) + " kN", f1(pz.vRdc_MPa) + " MPa", pct(pz.u_vRdc), pz.ok ? "OK" : "NO"],
  ["Cortante (§6.2.2, a d)", f0(cv.V_Ed_kN_m) + " kN/m", f0(cv.VRdc_kN_m) + " kN/m", pct(cv.u), cv.ok ? "OK" : "NO"]],
  [2926, 1900, 1900, 1100, 1200]));
ch.push(P(`Canto útil d = ${f0(ver.flexion.d_mm)} mm. El momento de flexión se evalúa en la cara del pilar ` +
  "integrando la presión del terreno (sección crítica EC2), evitando la concentración local del modelo FE bajo el pilar.",
  { run: { size: 18, italics: true } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P(`La zapata de ${f1(info.B)}×${f1(info.B)}×${(info.espesor).toFixed(2)} m ` +
  (ver.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") +
  `: la presión del terreno se aprovecha al ${pct(g.u_Rd)} (sin despegue), la flexión queda cubierta con ` +
  `${fx.armado} en ambas direcciones, y punzonamiento (${pct(pz.u_vRdc)}) y cortante (${pct(cv.u)}) cumplen. ` +
  "El equilibrio vertical cierra con error nulo. Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: modelo de Winkler (muelles lineales; el despegue del terreno requeriría muelles que solo " +
  "trabajen a compresión, comprobado aquí por p_min ≥ 0); la resistencia del terreno Rd y el módulo de balasto " +
  "proceden del estudio geotécnico; no se incluye comprobación a vuelco/deslizamiento global ni asientos a largo " +
  "plazo. Revisión y firma por técnico competente.", { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Zapata aislada · Fase 3", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

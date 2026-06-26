// Memoria de la LOSA DE CIMENTACION (raft): EC7 (presion/asientos) + EC2 (flexion 2D + punzonamiento).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || path.join(__dirname, "..", "proyecto-losa-cimentacion");
const out = process.argv[3] || path.join(dir, "Memoria_raft.docx");
const v = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

const CW = 9026, HEAD = "1F4E79", ZEBRA = "EEF3F8";
const bd = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const f1 = (x) => (x == null) ? "-" : Number(x).toFixed(1);
const f0 = (x) => (x == null) ? "-" : Number(x).toFixed(0);
const f2 = (x) => (x == null) ? "-" : Number(x).toFixed(2);
const pct = (x) => (x * 100).toFixed(0) + " %";
const okc = (b) => b ? "1E7A1E" : "B00000";
const okt = (b) => b ? "CUMPLE" : "NO CUMPLE";
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

const info = v.info, g = v.geotecnia, a = v.asientos, fx = v.flexion, pc = v.punz_critico, eq = v.equilibrio;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Losa de cimentación (raft) sobre lecho elástico", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "Veredicto global: " + v.veredicto, bold: true, size: 24, color: okc(v.veredicto === "CUMPLE") })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Predimensionado: revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y modelo", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de una losa de cimentación (raft) de hormigón armado de " + f0(info.BX) + " × " + f0(info.LY) +
  " m y canto " + f2(info.espesor) + " m, bajo una retícula de " + info.n_pilares + " pilares. La losa se modela " +
  "como placa (elementos MITC4) sobre muelles verticales de Winkler (módulo de balasto k_s = " + f1(info.ks / 1e6) +
  " MN/m³); la presión del terreno es k_s·asiento. Se comprueba la capacidad del terreno y los asientos (EC7) y la " +
  "losa a flexión en dos direcciones y a punzonamiento en cada pilar (EC2). Coeficientes parciales [confirmar AN España]."));

ch.push(H("2. Mapas de resultados", HeadingLevel.HEADING_1));
ch.push(...img("mapas_raft.png", 620, 195, "Figura 1. Presión del terreno y momentos Mx, My (ELU). Los recuadros marcan los pilares."));
ch.push(P("Equilibrio vertical (ELU): carga aplicada = " + f0(eq.aplicada_ELU_kN) + " kN, reacción del terreno = " +
  f0(eq.reaccion_suelo_ELU_kN) + " kN; error " + f2(eq.error_pct) + " %.", { run: { size: 19 } }));

ch.push(H("3. Comprobación geotécnica (EC7)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor", "Resultado"], [
  ["Presión máxima del terreno (ELU + p.p.)", f0(g.p_max_kPa) + " kPa (Rd " + f0(g.Rd_kPa) + ", " + pct(g.u_Rd) + ")", okt(g.ok_Rd)],
  ["Presión mínima (sin despegue)", f0(g.p_min_kPa) + " kPa", okt(g.ok_sin_despegue)],
  ["Asiento máx / mín", f2(a.asiento_max_mm) + " / " + f2(a.asiento_min_mm) + " mm", ""],
  ["Asiento diferencial / distorsión angular", f2(a.asiento_dif_mm) + " mm  (1/" + f0(1 / a.distorsion) + ")", okt(a.ok)]],
  [4526, 3000, 1500]));
ch.push(P("Distorsión angular admisible 1/" + f0(1 / a.distorsion_lim) + " [criterio EC7]. El peso propio de la losa " +
  "(" + f0(g.peso_propio_kPa) + " kPa) se añade a la presión del terreno para la comprobación de capacidad.",
  { run: { size: 18, italics: true } }));

ch.push(H("4. Flexión de la losa (EC2)", HeadingLevel.HEADING_1));
ch.push(P("Momentos de diseño en la sección crítica (excluido el pico singular bajo los pilares). Canto útil d_x = " +
  f0(fx.d_x_mm) + " mm, d_y = " + f0(fx.d_y_mm) + " mm.", { run: { size: 19 } }));
ch.push(table(["Armadura", "M_Ed [kN·m/m]", "As [cm²/m]", "Resultado"], [
  ["Inferior X (vanos)", f0(fx.x_inferior.m_Ed_kNm_m), f1(fx.x_inferior.As_prov_cm2_m), okt(fx.x_inferior.ok)],
  ["Inferior Y (vanos)", f0(fx.y_inferior.m_Ed_kNm_m), f1(fx.y_inferior.As_prov_cm2_m), okt(fx.y_inferior.ok)],
  ["Superior X (pilares)", f0(fx.x_superior.m_Ed_kNm_m), f1(fx.x_superior.As_prov_cm2_m), okt(fx.x_superior.ok)],
  ["Superior Y (pilares)", f0(fx.y_superior.m_Ed_kNm_m), f1(fx.y_superior.As_prov_cm2_m), okt(fx.y_superior.ok)]],
  [3026, 2500, 2000, 1500]));

ch.push(H("5. Punzonamiento (EC2 §6.4)", HeadingLevel.HEADING_1));
ch.push(table(["Pilar crítico", "Valor"], [
  ["Posición", pc.pilar.pos],
  ["Esfuerzo de punzonamiento V_Ed,neto", f0(pc.pilar.V_net_kN) + " kN"],
  ["v_Ed / v_Rd,c (perímetro de control)", pct(pc.u_vRdc) + (pc.ok_vRdc ? " (sin armadura)" : " (requiere armadura)")],
  ["v_Ed / v_Rd,max (perímetro del pilar)", pct(pc.u_vRdmax) + (pc.ok_vRdmax ? " OK" : " EXCEDE biela")]],
  [5026, 4000]));
ch.push(P("Se evalúan los " + info.n_pilares + " pilares según su posición (interior/borde/esquina); se reporta el más " +
  "desfavorable. V_Ed,neto descuenta la presión del terreno dentro del perímetro de control. Si v_Ed > v_Rd,c se " +
  "dispone armadura de punzonamiento o se aumenta el canto (solución incluida en el cálculo).", { run: { size: 18, italics: true } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("La losa de cimentación de " + f0(info.BX) + " × " + f0(info.LY) + " m y canto " + f2(info.espesor) + " m " +
  (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") + ": presión del terreno al " + pct(g.u_Rd) +
  " de Rd, asiento diferencial " + f2(a.asiento_dif_mm) + " mm (1/" + f0(1 / a.distorsion) + "), armadura de flexión " +
  "inferior de hasta " + f1(Math.max(fx.x_inferior.As_prov_cm2_m, fx.y_inferior.As_prov_cm2_m)) + " cm²/m y " +
  "punzonamiento crítico al " + pct(pc.u_vRdc) + ". Equilibrio vertical con error " + f2(eq.error_pct) +
  " %. Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: modelo elástico-lineal de Winkler (un único k_s, sin acoplamiento entre resortes ni " +
  "variación del terreno); el pico de momento bajo el pilar es una singularidad (se usa la sección crítica); no se " +
  "incluyen subpresión por agua, fases de carga ni interacción con la superestructura. Revisión y firma por técnico " +
  "competente.", { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Losa de cimentación · Fase 3", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

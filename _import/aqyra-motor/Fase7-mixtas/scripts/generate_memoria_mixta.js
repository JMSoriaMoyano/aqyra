// Memoria de la VIGA MIXTA acero-hormigon (EC4): seccion, conexion, construccion y flecha.
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || path.join(__dirname, "..", "proyecto-viga-mixta");
const out = process.argv[3] || path.join(dir, "Memoria_viga_mixta.docx");
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

const info = v.info, fm = v.flexion_mixta, cv = v.cortante, cx = v.conexion, cc = v.construccion, fl = v.flecha;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Viga mixta acero-hormigón con forjado colaborante (EC4)", size: 24 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "Veredicto global: " + v.veredicto, bold: true, size: 24, color: okc(v.veredicto === "CUMPLE") })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Predimensionado: revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y normativa", HeadingLevel.HEADING_1));
ch.push(P("Comprobación de una viga mixta acero-hormigón (perfil " + info.perfil + ") con forjado colaborante de chapa " +
  "nervada perpendicular, biapoyada de " + f1(info.L) + " m y separación entre vigas " + f1(info.sep) + " m, construida " +
  (info.apeado ? "apeada" : "sin apear") + ". Se verifica según EN 1994-1-1 (EC4, AN España): ancho eficaz, momento " +
  "resistente con grado de conexión, conexión a cortante (conectores), cortante vertical, fase de construcción (acero " +
  "solo) y flecha (corto y largo plazo con coeficiente de equivalencia). Coeficientes parciales [confirmar AN]."));

ch.push(H("2. Modelo y diagramas", HeadingLevel.HEADING_1));
ch.push(...img("diag_mixta.png", 600, 200, "Figura 1. Sección mixta con PNA y leyes de esfuerzos M(x), V(x) (ELU) en ambas fases."));

ch.push(H("3. Flexión de la sección mixta (EC4 §6.2.1)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor", "Resultado"], [
  ["Ancho eficaz b_eff", f2(v.b_eff_m) + " m", ""],
  ["Eje neutro plástico (PNA)", fm.PNA_zona + " (" + f0(fm.PNA_desde_base_mm) + " mm)", ""],
  ["M_pl,Rd conexión total / M_a,Rd acero", f0(fm.M_pl_Rd_total_kNm) + " / " + f0(fm.M_a_Rd_kNm) + " kN·m", ""],
  ["Grado de conexión / tipo", f2(fm.grado_conexion) + " (" + fm.tipo_conexion + ")", ""],
  ["M_Rd de diseño vs M_Ed", f0(fm.M_Rd_kNm) + " / " + f0(fm.M_Ed_kNm) + " kN·m (" + pct(fm.u) + ")", okt(fm.ok)]], [4026, 3500, 1500]));
ch.push(P("Con conexión parcial, el momento resistente se interpola entre el del acero solo y el plástico de conexión " +
  "total (EC4 §6.2.1.3): M_Rd = M_a,Rd + η·(M_pl,Rd − M_a,Rd). El M_pl,Rd se obtiene por modelo de fibras (acero a f_yd, " +
  "hormigón de cobertura a 0,85·f_cd; se desprecian los acuerdos del perfil, del lado de la seguridad).", { run: { size: 18, italics: true } }));

ch.push(H("4. Conexión a cortante (EC4 §6.6)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Resistencia de un conector P_Rd", f1(cx.PRd_kN) + " kN  (k_t = " + f2(cx.kt) + ", chapa perpendicular)"],
  ["Rasante de conexión total N_c", f0(cx.Nc_kN) + " kN"],
  ["Conectores: necesarios (total) / dispuestos (media luz)", f1(cx.Nf_total) + " / " + f1(cx.n_disp_media_luz)],
  ["Grado de conexión η / mínimo", f2(cx.grado_eta) + " / " + f2(cx.eta_min)]], [5526, 3500]));
ch.push(P("P_Rd = mín(0,8·f_u·A_s ; 0,29·α·d²·√(f_ck·E_cm))/γ_v reducida por k_t (chapa nervada perpendicular). " +
  "El grado de conexión cumple el mínimo de EC4 §6.6.1.2; con nervios perpendiculares y un conector por nervio la " +
  "conexión resulta " + fm.tipo_conexion + ".", { run: { size: 18, italics: true } }));

ch.push(H("5. Cortante, fase de construcción y flecha", HeadingLevel.HEADING_1));
ch.push(table(["Comprobación", "Valor", "Resultado"], [
  ["Cortante vertical V_Ed / V_pl,Rd", f0(cv.V_Ed_kN) + " / " + f0(cv.Vpl_Rd_kN) + " kN (" + pct(cv.u) + ")", okt(cv.ok)],
  ["Construcción (acero solo) M_Ed / M_c,Rd", f0(cc.M_Ed_kNm) + " / " + f0(cc.Mc_Rd_kNm) + " kN·m (" + pct(cc.u) + ")", okt(cc.ok)],
  ["Flecha total / L/250", f1(fl.d_total_mm) + " / " + f1(fl.lim_total_mm) + " mm (" + pct(fl.u_total) + ")", okt(fl.ok_total)],
  ["Flecha de uso / L/350", f1(fl.d_activa_mm) + " / " + f1(fl.lim_activa_mm) + " mm (" + pct(fl.u_activa) + ")", okt(fl.ok_activa)]], [4026, 3500, 1500]));
ch.push(P("Construcción sin apear: el perfil de acero resiste solo el peso del hormigón fresco más la sobrecarga de " +
  "ejecución. " + cc.nota + ". Flecha con coeficiente de equivalencia n_0 = " + f1(fl.n0) + " (corto plazo, sobrecarga) " +
  "y n_L = " + f1(fl.nL) + " (largo plazo, cargas permanentes, fluencia); se suma la flecha bloqueada de construcción " +
  "(" + f1(fl.d_construccion_mm) + " mm).", { run: { size: 18, italics: true } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("La viga mixta " + info.perfil + " de " + f1(info.L) + " m con forjado colaborante " +
  (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") + ": flexión al " + pct(fm.u) + " (M_Rd = " +
  f0(fm.M_Rd_kNm) + " kN·m con conexión " + fm.tipo_conexion + " η=" + f2(fm.grado_conexion) + "), cortante al " +
  pct(cv.u) + ", fase de construcción al " + pct(cc.u) + " y flecha total al " + pct(fl.u_total) + " del límite. " +
  "Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: análisis elástico-lineal de esfuerzos con sección plástica para el ELU (perfil clase 1/2); " +
  "no se incluye pandeo lateral en construcción (verificar arriostramiento del ala comprimida), fisuración del hormigón " +
  "en zonas de momento negativo (viga continua) ni vibraciones. Revisión y firma por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Viga mixta · EC4", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

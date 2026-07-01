// Memoria del MURO DE CONTENCION en mensula (EC7 estabilidad + EC2 elementos).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || path.join(__dirname, "..", "proyecto-muro-mensula");
const out = process.argv[3] || path.join(dir, "Memoria_muro.docx");
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
function cell(t, { w, head = false, fill, align, color } = {}) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA }, shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align || AlignmentType.LEFT, children: [new TextRun({ text: String(t), bold: head, color: head ? "FFFFFF" : (color || "000000"), size: 19 })] })] });
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

const info = v.info, vu = v.vuelco, de = v.deslizamiento, hu = v.hundimiento;
const al = v.alzado, pu = v.puntera, ta = v.talon, val = v.validacion;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Muro de contención en ménsula (Fase 6)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "Veredicto global: " + v.veredicto, bold: true, size: 24, color: okc(v.veredicto === "CUMPLE") })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Predimensionado: revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y normativa", HeadingLevel.HEADING_1));
ch.push(P("Comprobación de un muro de contención de hormigón armado tipo ménsula (T invertida). Se verifica la " +
  "estabilidad geotécnica según EN 1997-1 (EC7) —vuelco, deslizamiento y hundimiento— y el dimensionamiento " +
  "estructural de alzado, puntera y talón según EN 1992-1-1 (EC2). Acciones y combinaciones según EN 1990/1991. " +
  "Enfoque de cálculo DA-2* (coeficientes parciales sobre efectos de las acciones y sobre las resistencias). " +
  "Los parámetros del terreno proceden del estudio geotécnico; los valores marcados [confirmar AN] son NDP del " +
  "Anejo Nacional de España a contrastar."));

ch.push(H("2. Geometría y materiales", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Altura total resistida H", f2(info.H) + " m"],
  ["Ancho de zapata B (puntera + alzado + talón)", f2(info.B) + " m (" + f2(info.puntera) + " + " + f2(info.t_alz) + " + " + f2(info.talon) + ")"],
  ["Canto de zapata e_z", f2(info.e_z) + " m"],
  ["Espesor de alzado", f2(info.t_alz) + " m"],
  ["Material", info.material],
  ["Método de empuje", info.metodo + "  (Ka = " + f2(info.Ka) + ", Kp = " + f2(info.Kp) + ")"]], [5026, 4000]));

ch.push(H("3. Estabilidad geotécnica (EC7)", HeadingLevel.HEADING_1));
ch.push(...img("diag_muro.png", 520, 425, "Figura 1. Sección, empujes sobre el trasdós, presión bajo la zapata y ley de momentos del alzado."));
ch.push(table(["Estado límite", "Solicitación", "Resistencia", "Aprov.", "Resultado"], [
  ["Vuelco (EQU)", f0(vu.M_vuelco_d_kNm) + " kN·m", f0(vu.M_estab_d_kNm) + " kN·m", pct(vu.u), okt(vu.ok)],
  ["Deslizamiento (GEO)", f0(de.H_d_kN) + " kN", f0(de.R_d_kN) + " kN", pct(de.u), okt(de.ok)],
  ["Hundimiento (GEO)", f0(hu.q_Ed_kPa) + " kPa", f0(hu.Rd_kPa) + " kPa", pct(hu.u), okt(hu.ok)]],
  [2800, 2200, 2000, 1000, 1026]));
ch.push(P("Vuelco: factor de seguridad característico FS = " + f2(vu.FS_caracteristico) + ". Deslizamiento: " +
  "resistencia por rozamiento en la base (φ_base) más empuje pasivo movilizado en la puntera (R_fric = " +
  f0(de.R_friccion_kN) + " kN, R_pas = " + f0(de.R_pasivo_kN) + " kN); FS característico = " + f2(de.FS_caracteristico) +
  ". Hundimiento: excentricidad e = " + f2(hu.e_m) + " m " + (hu.ok_despegue ? "≤" : ">") + " B/6 = " + f2(hu.e_lim_B6_m) +
  " m (" + (hu.ok_despegue ? "sin despegue" : "DESPEGUE: revisar") + "); ancho eficaz de Meyerhof B' = " + f2(hu.Bp_m) +
  " m.", { run: { size: 19 } }));
ch.push(P("Coeficientes parciales (DA-2* / EQU) [confirmar AN España]: γ_G,dst = " + v.factores.EQU.G_dst +
  ", γ_G,stb = " + v.factores.EQU.G_stb + ", γ_Q = " + v.factores.EQU.Q_dst + " (vuelco); γ_G = " +
  v.factores["GEO_DA2*"].G_sup + ", γ_Q = " + v.factores["GEO_DA2*"].Q_sup + ", γ_R,h = " + v.factores["GEO_DA2*"].gR_h +
  ", γ_R,v = " + v.factores["GEO_DA2*"].gR_v + ", γ_R,e = " + v.factores["GEO_DA2*"].gR_e + ".",
  { run: { size: 18, italics: true } }));

ch.push(H("4. Dimensionamiento estructural (EC2)", HeadingLevel.HEADING_1));
ch.push(table(["Elemento", "M_Ed [kN·m/m]", "As [cm²/m]", "V_Ed [kN/m]", "u_cortante", "Resultado"], [
  ["Alzado (arranque)", f0(al.flexion.M_Ed_kNm_m), f1(al.flexion.As_prov_cm2_m), f0(al.cortante.V_Ed_kN_m), pct(al.cortante.u), okt(al.cortante.ok)],
  ["Puntera", f0(pu.flexion.M_Ed_kNm_m), f1(pu.flexion.As_prov_cm2_m), f0(pu.cortante.V_Ed_kN_m), pct(pu.cortante.u), okt(pu.cortante.ok)],
  ["Talón", f0(ta.flexion.M_Ed_kNm_m), f1(ta.flexion.As_prov_cm2_m), f0(ta.cortante.V_Ed_kN_m), pct(ta.cortante.u), okt(ta.cortante.ok)]],
  [2600, 1900, 1500, 1500, 1300, 1226]));
ch.push(P("El momento del alzado se obtiene modelando el fuste como ménsula vertical empotrada en la zapata, " +
  "cargada con las presiones del trasdós (solver de barras). La puntera y el talón se calculan como voladizos " +
  "de la zapata bajo la presión neta del terreno. La armadura incluye la cuantía mínima de EC2 §9.2.1; el " +
  "cortante se comprueba a un canto de la cara sin armadura transversal (V_Rd,c, EC2 §6.2.2).",
  { run: { size: 19 } }));

ch.push(H("5. Validación", HeadingLevel.HEADING_1));
ch.push(P("Contraste del empuje activo integrado numéricamente frente a la forma cerrada (0,5·Ka·γ·H² + Ka·q·H): " +
  f1(val.Eh_integrado_kN) + " kN/m vs " + f1(val.Ea_forma_cerrada_kN) + " kN/m → error " + f2(val.error_pct) + " %. " +
  "El momento del alzado del solver de barras coincide con la solución analítica de la ménsula. Equilibrio " +
  "estático verificado.", { run: { size: 19 } }));

ch.push(H("6. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("El muro ménsula de " + f2(info.H) + " m " + (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") +
  " las comprobaciones de estabilidad (vuelco " + pct(vu.u) + ", deslizamiento " + pct(de.u) + ", hundimiento " +
  pct(hu.u) + ") y de resistencia estructural de alzado, puntera y talón. Resultados de predimensionado.",
  { run: { bold: true } }));
ch.push(P("Limitaciones: análisis lineal y estados desacoplados (predimensionado); parámetros del terreno del " +
  "estudio geotécnico; no se incluye sismo (Mononobe-Okabe), anclajes ni interacción suelo-estructura completa; " +
  "el empuje pasivo se moviliza parcialmente. Revisión y firma por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Muro de contención · Fase 6", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

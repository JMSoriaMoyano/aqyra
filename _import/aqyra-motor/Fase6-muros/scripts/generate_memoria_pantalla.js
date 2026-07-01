// Memoria de la PANTALLA ANCLADA (EC7 empotramiento + ancla/bulbo + EC2 fuste).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || path.join(__dirname, "..", "proyecto-pantalla-anclada");
const out = process.argv[3] || path.join(dir, "Memoria_pantalla.docx");
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

const info = v.info, em = v.empotramiento, an = v.ancla, fu = v.fuste, eq = v.equilibrio;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Pantalla de contención anclada (Fase 6)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [new TextRun({ text: "Veredicto global: " + v.veredicto, bold: true, size: 24, color: okc(v.veredicto === "CUMPLE") })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Predimensionado: revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y normativa", HeadingLevel.HEADING_1));
ch.push(P("Comprobación de una pantalla de contención de hormigón armado con una fila de anclajes al terreno, para " +
  "una excavación de " + f1(info.h) + " m. Se idealiza la pantalla como viga vertical: el empuje activo del trasdós " +
  "como carga, el terreno delante del empotramiento como muelles horizontales (módulo de balasto) que movilizan el " +
  "empuje pasivo, y el anclaje como apoyo horizontal. Se verifica el empotramiento (EC7, método de apoyo libre), el " +
  "anclaje (fuerza, bulbo y longitud libre) y el fuste a flexión (EC2). Enfoque DA-2* con NDP [confirmar AN España]."));

ch.push(H("2. Geometría y terreno", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Altura de excavación h", f1(info.h) + " m"],
  ["Empotramiento d / longitud total L", f1(info.d) + " m / " + f1(info.L) + " m"],
  ["Espesor de pantalla", f2(info.t) + " m, " + info.material],
  ["Módulo de balasto horizontal kh", f1(info.kh / 1e6) + " MN/m³"],
  ["Coeficientes de empuje", info.metodo + " — Ka = " + f2(info.Ka) + ", Kp = " + f2(info.Kp)],
  ["Ancla", "profundidad " + f2(info.z_ancla) + " m, inclinación " + f0(an.inclinacion_grados) + "°, separación " + f1(an.separacion_m) + " m"]], [4526, 4500]));

ch.push(H("3. Modelo y diagramas", HeadingLevel.HEADING_1));
ch.push(...img("diag_pantalla.png", 600, 260, "Figura 1. Esquema, empujes activo/pasivo, ley de momentos del fuste y deformada."));
ch.push(P("Equilibrio horizontal de la modelización (ELU): empuje activo aplicado = " + f0(eq.H_aplicado_ELU_kN) +
  " kN/m, equilibrado por el ancla (" + f0(eq.T_h_ELU_kN) + " kN/m) y el terreno (" + f0(eq.Pp_mov_ELU_kN) +
  " kN/m); error " + f2(eq.error_pct) + " %.", { run: { size: 19 } }));

ch.push(H("4. Empotramiento (EC7, apoyo libre)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor", "Resultado"], [
  ["Empuje activo característico", f0(em.Ea_caract_kN) + " kN/m", ""],
  ["Empuje pasivo disponible (caract.)", f0(em.Pp_disp_caract_kN) + " kN/m", ""],
  ["Factor de seguridad del pasivo", f2(em.FoS_pasivo) + "  (objetivo " + f2(em.FoS_objetivo) + ")", okt(em.ok)]], [4526, 3000, 1500]));
ch.push(P("FoS del empotramiento por el método de apoyo libre (momentos respecto al ancla): M_pasivo / M_activo = " +
  f2(em.FoS_pasivo) + ". El pasivo movilizado por el modelo de muelles (ELU) es " + f0(em.Pp_movilizado_ELU_kN) +
  " kN/m (ratio informativo frente al pasivo de cálculo " + f2(em.u_pasivo_informativo) + "); con muelles lineales " +
  "el pasivo no está acotado, por lo que el criterio de suficiencia es el FoS de apoyo libre.", { run: { size: 18, italics: true } }));

ch.push(H("5. Anclaje y bulbo", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [
  ["Reacción horizontal (muelles FE / apoyo libre)", f0(an.T_h_FE_kN_m) + " / " + f0(an.T_h_freeearth_kN_m) + " kN/m"],
  ["Reacción de diseño (envolvente, dim. " + an.metodo_dimensionante + ")", f0(an.T_h_kN_m) + " kN/m"],
  ["Fuerza de cálculo por ancla (sep. " + f1(an.separacion_m) + " m)", f0(an.F_ancla_kN) + " kN"],
  ["Longitud de bulbo (Ø" + f2(an.D_bulbo_m) + " m, τ=" + f0(an.tau_kPa) + " kPa, FS=" + f1(an.fs_bulbo) + ")", f1(an.L_bulbo_m) + " m"],
  ["Longitud libre mínima (más allá de la cuña activa)", "≥ " + f1(an.L_libre_min_m) + " m"],
  ["Longitud total mínima del ancla", "≥ " + f1(an.L_total_min_m) + " m"]], [5526, 3500]));
ch.push(P("La fuerza por ancla es la reacción horizontal mayorada dividida por cos(inclinación) y multiplicada por la " +
  "separación. La longitud de bulbo se obtiene del rozamiento lechada-terreno (L_b = F·FS / (π·D·τ)); la longitud " +
  "libre debe situar el bulbo por detrás de la cuña activa de rotura. Parámetros del bulbo a confirmar con ensayos.",
  { run: { size: 18, italics: true } }));

ch.push(H("6. Fuste de la pantalla (EC2)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor", "Resultado"], [
  ["Momento flector máximo M_Ed", f0(fu.flexion.M_Ed_kNm_m) + " kN·m/m", ""],
  ["Armadura de flexión As", f1(fu.flexion.As_prov_cm2_m) + " cm²/m", okt(fu.flexion.ok)],
  ["Cortante V_Ed / V_Rd,c", f0(fu.cortante.V_Ed_kN_m) + " / " + f0(fu.cortante.VRdc_kN_m) + " kN/m (" + pct(fu.cortante.u) + ")", okt(fu.cortante.ok)]], [4526, 3000, 1500]));

ch.push(H("7. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("La pantalla anclada (excavación " + f1(info.h) + " m, empotramiento " + f1(info.d) + " m) " +
  (v.veredicto === "CUMPLE" ? "CUMPLE" : "REQUIERE revisión") + ": FoS del empotramiento = " + f2(em.FoS_pasivo) +
  ", fuerza de ancla = " + f0(an.F_ancla_kN) + " kN (bulbo ≥ " + f1(an.L_bulbo_m) + " m, longitud total ≥ " +
  f1(an.L_total_min_m) + " m), y fuste armado con " + f1(fu.flexion.As_prov_cm2_m) + " cm²/m. El equilibrio horizontal " +
  "del modelo cierra con error " + f2(eq.error_pct) + " %. Resultados de predimensionado.", { run: { bold: true } }));
ch.push(P("Limitaciones: análisis lineal con una fila de anclas; el terreno se representa por muelles (balasto) y el " +
  "pasivo no se acota en el modelo de muelles (la suficiencia la fija el FoS de apoyo libre); no se incluyen fases de " +
  "excavación, agua diferencial entre caras, pretensado del ancla ni sismo. Revisión y firma por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Pantalla anclada · Fase 6", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

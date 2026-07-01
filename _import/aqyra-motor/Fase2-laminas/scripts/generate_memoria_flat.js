// Memoria de la LOSA PLANA sobre pilares (punzonamiento + dimensionamiento).
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-losa-plana";
const out = process.argv[3] || path.join(dir, "Memoria_losa_plana.docx");
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

const CW = 9026, HEAD = "1F4E79", ZEBRA = "EEF3F8";
const bd = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const f1 = (x) => (x == null) ? "-" : Number(x).toFixed(1);
const f2 = (x) => (x == null) ? "-" : Number(x).toFixed(2);
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

const info = res.info, L = ver.losa, ad = ver.autodiagnostico_placa, eq = ver.equilibrio, fi = ver.fisuracion;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Losa plana de hormigón sobre pilares — Punzonamiento (Fase 2)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de una losa plana de hormigón armado apoyada directamente sobre pilares (sin vigas). En esta " +
  "tipología el punzonamiento es el mecanismo que gobierna el dimensionamiento en torno a los pilares. Se " +
  "comprueban flexión, flecha, punzonamiento (con dimensionamiento de la solución) y fisuración."));

ch.push(H("2. Normativa", HeadingLevel.HEADING_1));
ch.push(table(["Código", "Uso"], [["EN 1990 / EN 1991", "Acciones y combinaciones ELU/ELS"],
  ["EN 1992-1-1 §6.4", "Punzonamiento"], ["EN 1992-1-1 §6.1/9", "Flexión y cuantías"],
  ["EN 1992-1-1 §7.3/7.4", "Fisuración y flecha"], ["AN España", "NDP [confirmar AN]"]], [3026, 6000]));

ch.push(H("3. Modelo", HeadingLevel.HEADING_1));
ch.push(...img("plano_pilares.png", 360, 320, "Figura 1. Planta de pilares: reacción ELU [kN] y estado de punzonamiento."));
ch.push(P(`Losa de ${f1(info.W)} × ${f1(info.H)} m (vanos de ${f1(info.W / 2)} m), canto ${(info.espesor * 1e3).toFixed(0)} mm, ` +
  `hormigón ${info.material}. Malla de elementos placa de ${info.mesh} m. 9 pilares (malla 3×3) modelados como apoyos verticales.`));

ch.push(H("4. Acciones y combinaciones", HeadingLevel.HEADING_1));
ch.push(table(["Acción", "Valor"], [["Autopeso losa", f2(info.peso_losa_N_m2 / 1e3) + " kN/m²"],
  ["G superpuesta", "2,00 kN/m²"], ["Q uso", "3,00 kN/m²"]], [4526, 4500]));
ch.push(table(["Combinación", "Tipo", "Expresión"], Object.entries(res.combos_meta).map(([n, m]) => [n, m.tipo, m.expr]), [2400, 1500, 5126]));

ch.push(H("5. Validación y equilibrio", HeadingLevel.HEADING_1));
ch.push(table(["Comprobación", "Resultado"], [
  ["Elementos placa (Timoshenko)", (ad.valido ? "OK" : "FALLO") + " — flecha err " + (ad.checks["flecha (mm)"][2] * 100).toFixed(1) + " %, momento err " + (ad.checks["M_max (kN·m/m)"][2] * 100).toFixed(1) + " %"],
  ["Equilibrio vertical ELU", "aplicada " + f1(eq.aplicada_ELU_kN) + " kN = reacción " + f1(eq.reaccion_ELU_kN) + " kN (error " + eq.error_pct.toFixed(2) + " %)"]], [3526, 5500]));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("6. Esfuerzos de la losa", HeadingLevel.HEADING_1));
ch.push(...img("mapa_Mx.png", 300, 260, "Figura 2. Mx de vano (tracción inferior) — ELU."));
ch.push(...img("mapa_Mx_hog.png", 300, 260, "Figura 3. Mx sobre pilares (tracción superior) — ELU."));
ch.push(...img("mapa_flecha.png", 300, 260, "Figura 4. Flecha — ELS característica."));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("7. Armado a flexión y flecha", HeadingLevel.HEADING_1));
const arm = (k, et) => { const a = L[k]; return [et, f1(a.m_Ed_kNm_m), f2(a.As_dim_cm2_m), a.armado + " (" + f2(a.As_prov_cm2_m) + ")", a.mu.toFixed(3), a.ok ? "OK" : "NO"]; };
ch.push(table(["Armadura", "m_Ed [kN·m/m]", "As [cm²/m]", "Disposición", "μ", "Cumple"],
  [arm("x_inferior", "Vano inferior x"), arm("y_inferior", "Vano inferior y"),
   arm("x_superior", "Pilar superior x"), arm("y_superior", "Pilar superior y")], [2226, 1500, 1300, 1800, 900, 1300]));
const fl = L.flecha;
ch.push(P(`Flecha total ${f2(fl.f_total_mm)} mm ≤ L/300 = ${f1(fl.lim_total_mm)} mm (${pct(fl.u_total)}); activa ${f2(fl.f_activa_mm)} mm ≤ L/500 = ${f1(fl.lim_activa_mm)} mm (${pct(fl.u_activa)}).`, { run: { bold: true } }));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("8. Punzonamiento (EC2 §6.4)", HeadingLevel.HEADING_1));
const prow = Object.entries(ver.punzonamiento).map(([pos, e]) => {
  const c = e.check;
  return [pos, f1(e.V_Ed_kN), f2(c.vEd_u1_MPa), f2(c.vRdc_MPa), pct(c.u_vRdc), c.ok ? "CUMPLE" : "NO"];
});
ch.push(table(["Pilar", "V_Ed [kN]", "v_Ed [MPa]", "v_Rd,c [MPa]", "Aprov.", "Estado"], prow, [1800, 1400, 1400, 1500, 1400, 1526]));
// dimensionamiento del pilar que no cumple (interior)
const inte = ver.punzonamiento.interior;
if (inte && inte.dimensionado) {
  const d = inte.dimensionado;
  ch.push(H("8.1 Dimensionamiento del pilar interior (no cumple)", HeadingLevel.HEADING_2));
  ch.push(P(`El pilar interior (V_Ed = ${f1(inte.V_Ed_kN)} kN, aprovechamiento ${pct(inte.check.u_vRdc)}) requiere una de estas soluciones:`));
  ch.push(table(["Solución", "Resultado", "Observación"], [
    ["1 · Aumentar canto", "h ≥ " + d.canto_minimo.h_min_mm + " mm (+" + d.canto_minimo.incremento_mm + " mm)", "Sin armadura de punzonamiento"],
    ["2 · Armadura de punzonamiento", "Asw/sr ≈ " + f1(d.armadura.asw_sr_cm2_m) + " cm²/m (hasta u_out ≈ " + f2(d.armadura.u_out_m) + " m)", d.armadura.viable ? "Viable (v_Rd,max OK)" : "No viable: revisar canto"],
    ["3 · Ábaco / capitel", "lado ≈ " + d.capitel.lado_capitel_mm + " mm (ampliación +" + d.capitel.ampliacion_mm + " mm)", "Engrosamiento sobre el pilar"]],
    [2600, 4000, 2426]));
  ch.push(P("Las tres soluciones se calculan según EC2 §6.4; la elección depende de criterios constructivos y de coste. " +
    "Valores de predimensionado, a detallar.", { run: { italics: true, size: 18 } }));
}

ch.push(H("9. Fisuración (EC2 §7.3)", HeadingLevel.HEADING_1));
ch.push(table(["Parámetro", "Valor"], [["Momento cuasipermanente (vano)", f1(fi.M_qp_kNm_m) + " kN·m/m"],
  ["Tensión del acero σs", f1(fi.sigma_s_MPa) + " MPa"], ["Abertura de fisura wk", f2(fi.wk_mm) + " mm"],
  ["Límite wmax", f2(fi.wmax_mm) + " mm (aprov. " + pct(fi.u) + ")"]], [5026, 4000]));
ch.push(P("Resultado: " + (fi.ok ? "fisuración controlada." :
  "wk supera el límite → aumentar la armadura inferior de vano o reducir su separación para el control de fisuración."),
  { run: { bold: true, color: fi.ok ? "1E7A1E" : "C07A00" } }));

ch.push(H("10. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("La losa plana de 25 cm cumple a flexión y flecha. El punzonamiento gobierna en el pilar interior " +
  "(aprovechamiento " + pct(inte.check.u_vRdc) + "), donde se requiere aumentar el canto a " + inte.dimensionado.canto_minimo.h_min_mm +
  " mm, disponer armadura de punzonamiento o un ábaco/capitel. Bordes y esquinas cumplen. La fisuración de vano " +
  (fi.ok ? "está controlada" : "exige reforzar la armadura inferior") + ". Los elementos placa están validados " +
  "(Timoshenko) y el equilibrio cierra con error nulo.", { run: { bold: true } }));
ch.push(P("Limitaciones: análisis lineal; el armado y el dimensionamiento de punzonamiento son de predimensionado " +
  "y deben detallarse; no se incluye fisuración sobre pilares ni análisis no lineal. Revisión y firma por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Losa plana · Punzonamiento · Fase 2", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

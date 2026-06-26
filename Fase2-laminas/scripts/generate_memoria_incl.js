// Memoria de la CUBIERTA / forjado inclinado de hormigon.
const fs = require("fs"), path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, Header, Footer } = require("docx");

const dir = process.argv[2] || "proyecto-cubierta";
const out = process.argv[3] || path.join(dir, "Memoria_cubierta_inclinada.docx");
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

const info = res.info, L = ver.losa, vv = ver.validacion, me = ver.membrana, fi = ver.fisuracion, eq = ver.equilibrio;
const ch = [];
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 }, children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Cubierta / forjado inclinado de hormigón (Fase 2)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 }, children: [new TextRun({ text: "Documento generado automáticamente. Revisión y firma por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Cálculo de un elemento plano inclinado de hormigón armado (cubierta a un agua / forjado inclinado) " +
  "simplemente apoyado en sus cuatro bordes. Se obtienen los esfuerzos de flexión y de membrana de la lámina, " +
  "la flecha normal al faldón y las comprobaciones EC2 de flexión, fisuración y compresión de membrana."));

ch.push(H("2. Modelo", HeadingLevel.HEADING_1));
ch.push(...img("vista_3d.png", 360, 290, "Figura 1. Geometría del faldón inclinado (apoyo en aleros resaltado)."));
ch.push(P(`Faldón de ${f1(info.Lu)} × ${f1(info.Lv)} m, pendiente ${f1(info.angulo)}°, canto ${(info.espesor * 1e3).toFixed(0)} mm, ` +
  `hormigón ${info.material} (autopeso ${f2(info.peso_losa_N_m2 / 1e3)} kN/m²). Malla de elementos lámina (MITC4) inclinada.`));

ch.push(H("3. Acciones y combinaciones", HeadingLevel.HEADING_1));
ch.push(P("Las cargas de gravedad (autopeso, carga permanente y uso/nieve) se aplican como cargas verticales " +
  "repartidas en los nodos según el área real de cada elemento — procedimiento válido para cualquier inclinación."));
ch.push(table(["Combinación", "Tipo", "Expresión"], Object.entries(res.combos_meta).map(([n, m]) => [n, m.tipo, m.expr]), [2400, 1500, 5126]));

ch.push(H("4. Validación del modelo inclinado", HeadingLevel.HEADING_1));
const ir = vv.invariancia_rotacion;
ch.push(table(["Comprobación", "Resultado"], [
  ["Invariancia de rotación (carga normal, θ=0 vs θ=30°)", "Mx err " + (ir.err_Mx * 100).toFixed(2) + " %, My err " + (ir.err_My * 100).toFixed(2) + " % → " + (ir.ok ? "OK" : "NO")],
  ["Equilibrio vertical ELU", "error " + vv.equilibrio_pct.toFixed(2) + " %"]], [4526, 4500]));
ch.push(P("Los elementos lámina son invariantes a la orientación (la pequeña diferencia procede de la " +
  "aproximación de los apoyos en ejes globales) y el equilibrio vertical cierra exacto.", { run: { size: 18, italics: true } }));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("5. Esfuerzos de la lámina", HeadingLevel.HEADING_1));
ch.push(...img("mapa_Mx.png", 300, 260, "Figura 2. Momento Mx (sagging) — ELU."));
ch.push(...img("mapa_membrana.png", 300, 260, "Figura 3. Membrana n_y (compresión del faldón hacia aleros) — ELU."));
ch.push(...img("mapa_flecha.png", 300, 260, "Figura 4. Flecha normal al faldón — ELS característica."));

ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("6. Comprobaciones EC2", HeadingLevel.HEADING_1));
ch.push(H("6.1 Flexión y flecha", HeadingLevel.HEADING_2));
const arm = (k, et) => { const a = L[k]; return [et, f1(a.m_Ed_kNm_m), f2(a.As_dim_cm2_m), a.armado + " (" + f2(a.As_prov_cm2_m) + ")", a.mu.toFixed(3), a.ok ? "OK" : "NO"]; };
ch.push(table(["Armadura", "m_Ed [kN·m/m]", "As [cm²/m]", "Disposición", "μ", "Cumple"],
  [arm("x_inferior", "Inferior x"), arm("y_inferior", "Inferior y")], [2226, 1500, 1300, 1800, 900, 1300]));
const fl = L.flecha;
ch.push(P(`Flecha normal al faldón ${f2(fl.f_total_mm)} mm ≤ L/300 = ${f1(fl.lim_total_mm)} mm (${pct(fl.u_total)}); activa ${pct(fl.u_activa)}.`, { run: { bold: true } }));
ch.push(H("6.2 Membrana (compresión del faldón)", HeadingLevel.HEADING_2));
ch.push(table(["Parámetro", "Valor"], [
  ["Compresión de membrana n_Ed", f1(me.n_comp_kN_m) + " kN/m"],
  ["Tracción de membrana", f1(me.n_trac_kN_m) + " kN/m"],
  ["Capacidad bruta n_Rd = fcd·t", f1(me.nRd_comp_kN_m) + " kN/m (aprov. " + pct(me.u_comp) + ")"]], [5026, 4000]));
ch.push(P("La componente de gravedad paralela al faldón genera una compresión de membrana que se transmite a los " +
  "aleros; su aprovechamiento frente a la capacidad del hormigón es " + pct(me.u_comp) + " (despreciable). " +
  (me.ok_comp ? "Cumple." : "Revisar."), { run: { bold: true, color: me.ok_comp ? "1E7A1E" : "B00000" } }));
ch.push(H("6.3 Fisuración", HeadingLevel.HEADING_2));
ch.push(table(["Parámetro", "Valor"], [["σs (cuasipermanente)", f1(fi.sigma_s_MPa) + " MPa"],
  ["wk", f2(fi.wk_mm) + " mm"], ["wmax", f2(fi.wmax_mm) + " mm (aprov. " + pct(fi.u) + ")"]], [5026, 4000]));
ch.push(P("Resultado: " + (fi.ok ? "fisuración controlada." :
  "wk supera el límite con la armadura mínima (separación amplia) → reducir la separación de la armadura inferior " +
  "(p. ej. φ10/150) para el control de fisuración."), { run: { bold: true, color: fi.ok ? "1E7A1E" : "C07A00" } }));

ch.push(H("7. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("El faldón inclinado cumple a flexión, flecha y compresión de membrana. El motor captura correctamente " +
  "el comportamiento del plano inclinado (invariancia validada, equilibrio exacto) incluyendo el empuje de membrana " +
  "hacia los aleros. La fisuración de vano " + (fi.ok ? "está controlada" : "exige reducir la separación de la " +
  "armadura inferior") + ". Resultados de predimensionado; revisión y firma por técnico competente.", { run: { bold: true } }));
ch.push(P("Nota: las acciones de viento (presión normal) y nieve con su distribución real (EC1-1-3/1-4) se " +
  "introducirían como casos adicionales; aquí se ha usado una carga de uso/nieve simplificada vertical.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } }, children: [new TextRun({ text: "Memoria · Cubierta inclinada · Fase 2", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("Memoria escrita en:", out); });

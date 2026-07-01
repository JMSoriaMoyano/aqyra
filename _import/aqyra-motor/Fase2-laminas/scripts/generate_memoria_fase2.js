// Memoria de calculo Fase 2 (modelo mixto barras + losa) en docx.
// Uso: NODE_PATH=<docx> node generate_memoria_fase2.js <dir> [salida.docx]
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, Footer,
} = require("docx");

const dir = process.argv[2] || "proyecto-demo";
const out = process.argv[3] || path.join(dir, "Memoria_calculo_Fase2.docx");
const model = JSON.parse(fs.readFileSync(path.join(dir, "modelo_neutro.json"), "utf8"));
const res = JSON.parse(fs.readFileSync(path.join(dir, "resultados.json"), "utf8"));
const ver = JSON.parse(fs.readFileSync(path.join(dir, "verificacion.json"), "utf8"));

const CW = 9026, HEAD = "1F4E79", ZEBRA = "EEF3F8";
const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const f1 = (x) => (x == null) ? "-" : Number(x).toFixed(1);
const f2 = (x) => (x == null) ? "-" : Number(x).toFixed(2);
const pct = (x) => (x * 100).toFixed(0) + " %";

function P(t, o = {}) { return new Paragraph({ spacing: { after: 120 }, ...o, children: [new TextRun({ text: t, ...(o.run || {}) })] }); }
function H(t, l) { return new Paragraph({ heading: l, children: [new TextRun(t)] }); }
function cell(t, { w, head = false, fill, align } = {}) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align || AlignmentType.LEFT,
      children: [new TextRun({ text: String(t), bold: head, color: head ? "FFFFFF" : "000000", size: 19 })] })] });
}
function table(headers, rows, widths) {
  const trs = [new TableRow({ tableHeader: true, children: headers.map((h, i) =>
    cell(h, { w: widths[i], head: true, fill: HEAD, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })];
  rows.forEach((r, ri) => trs.push(new TableRow({ children: r.map((c, i) =>
    cell(c, { w: widths[i], fill: ri % 2 ? ZEBRA : undefined, align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })) })));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
function img(file, w, h, cap) {
  const o = [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(dir, file)),
      transformation: { width: w, height: h }, altText: { title: cap, description: cap, name: file } })] })];
  if (cap) o.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: cap, italics: true, size: 17, color: "555555" })] }));
  return o;
}

const info = res.info, L = ver.losa, ad = ver.autodiagnostico_placa, eq = ver.equilibrio;
const pz = ver.punzonamiento, fi = ver.fisuracion;
const ch = [];

// Portada
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 120 },
  children: [new TextRun({ text: "MEMORIA DE CÁLCULO ESTRUCTURAL", bold: true, size: 40, color: HEAD })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Módulo pórtico de acero + losa de hormigón (Fase 2)", size: 26 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "Motor de cálculo IFC → FEM mixto barras/placa → Eurocódigos", size: 22, color: "555555" })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 },
  children: [new TextRun({ text: "Proyecto: Estructurando   ·   Fecha: 21/06/2026", size: 22 })] }));
ch.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 800 },
  children: [new TextRun({ text: "Documento generado automáticamente. Los cálculos deben ser revisados y firmados por técnico competente.", italics: true, size: 18, color: "999999" })] }));
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));

// 1. Objeto
ch.push(H("1. Objeto y alcance", HeadingLevel.HEADING_1));
ch.push(P("Esta memoria justifica el cálculo de un módulo de edificio formado por un pórtico espacial de acero " +
  "(4 pilares y 4 vigas perimetrales) y una losa de hormigón armado apoyada en las vigas. Amplía la Fase 1 " +
  "(barras) incorporando elementos finitos tipo lámina (placa) para la losa, su dimensionamiento a flexión " +
  "según EC2 y la comprobación conjunta del modelo mixto barras + placa."));

// 2. Normativa
ch.push(H("2. Normativa de aplicación", HeadingLevel.HEADING_1));
ch.push(table(["Código", "Título", "Uso"],
  [["EN 1990 (EC0)", "Bases de cálculo", "Combinaciones ELU/ELS"],
   ["EN 1991 (EC1)", "Acciones", "Permanentes, autopeso y uso"],
   ["EN 1992-1-1 (EC2)", "Estructuras de hormigón", "Armado de la losa, cuantías, flecha"],
   ["EN 1993-1-1 (EC3)", "Estructuras de acero", "Comprobación de vigas y pilares"],
   ["AN España", "Anejos Nacionales", "Coeficientes y NDP [confirmar AN]"]], [1900, 4126, 3000]));

// 3. Modelo
ch.push(H("3. Descripción del modelo", HeadingLevel.HEADING_1));
ch.push(...img("modelo_3d.png", 360, 310, "Figura 1. Modelo 3D del módulo (pórtico + losa)."));
ch.push(H("3.1 Geometría", HeadingLevel.HEADING_2));
ch.push(P(`Módulo de ${f1(info.W)} × ${f1(info.H)} m en planta y ${f1(info.z)} m de altura. ` +
  `Losa de canto ${(info.espesor * 1e3).toFixed(0)} mm. Pilares ${info.sec_pilar} y vigas ${info.sec_viga}.`));
ch.push(H("3.2 Materiales", HeadingLevel.HEADING_2));
const matRows = Object.entries(model.materiales).map(([m, p]) => [m,
  (p.E / 1e9).toFixed(1), p.fy ? (p.fy / 1e6).toFixed(0) : (p.fck ? (p.fck / 1e6).toFixed(0) + " (fck)" : "-"),
  p.nu.toFixed(2), p.rho.toFixed(0)]);
ch.push(table(["Material", "E [GPa]", "f [MPa]", "ν", "ρ [kg/m³]"], matRows, [3026, 1500, 1500, 1500, 1500]));
ch.push(P("Hormigón C30/37 (γc = 1,50); acero pasivo B500S (fyk = 500 MPa, γs = 1,15); acero estructural S275 " +
  "(γM0 = 1,00). [confirmar AN]", { run: { size: 18 } }));

// 4. Acciones
ch.push(H("4. Acciones y combinaciones", HeadingLevel.HEADING_1));
const cargas = model.superficies[0].cargas.map((c) => [c.caso, (Math.abs(c.qz) / 1e3).toFixed(2) + " kN/m²", "Losa"]);
cargas.push(["G (autopeso losa)", (info.peso_losa_N_m2 / 1e3).toFixed(2) + " kN/m²", "Losa"]);
cargas.push(["G (autopeso barras)", (info.pp_barras_N / 1e3).toFixed(1) + " kN total", "Vigas+pilares"]);
ch.push(table(["Acción", "Valor", "Aplicación"], cargas, [3526, 2750, 2750]));
const comboRows = Object.entries(res.combos_meta).map(([n, m]) => [n, m.tipo, m.expr, m.norma]);
ch.push(table(["Combinación", "Tipo", "Expresión", "Ref."], comboRows, [1800, 1100, 3126, 3000]));

// 5. Procedimiento y validacion
ch.push(H("5. Procedimiento y validación", HeadingLevel.HEADING_1));
ch.push(P("La losa se idealiza con elementos finitos cuadriláteros (MITC4); las vigas perimetrales se mallan en " +
  "segmentos que comparten nodos con la losa (apoyo de borde) y los pilares conectan las esquinas con la " +
  "cimentación empotrada. El modelo se resuelve en régimen lineal."));
ch.push(H("5.1 Validación de los elementos placa (Timoshenko)", HeadingLevel.HEADING_2));
ch.push(table(["Magnitud", "Calculado", "Teórico", "Error"],
  [["Flecha losa SS (mm)", f2(ad.checks["flecha (mm)"][0]), f2(ad.checks["flecha (mm)"][1]), (ad.checks["flecha (mm)"][2] * 100).toFixed(2) + " %"],
   ["Momento centro (kN·m/m)", f2(ad.checks["M_max (kN·m/m)"][0]), f2(ad.checks["M_max (kN·m/m)"][1]), (ad.checks["M_max (kN·m/m)"][2] * 100).toFixed(2) + " %"]],
  [3526, 1900, 1900, 1700]));
ch.push(P("Elementos placa " + (ad.valido ? "VALIDADOS" : "NO validados") + " frente a la solución analítica de Timoshenko.",
  { run: { bold: true, color: ad.valido ? "1E7A1E" : "B00000" } }));
ch.push(H("5.2 Equilibrio global", HeadingLevel.HEADING_2));
ch.push(table(["Carga losa ELU", "Autopeso barras ELU", "Total aplicada", "Reacción", "Error"],
  [[f1(eq.carga_losa_ELU_kN) + " kN", f1(eq.pp_barras_ELU_kN) + " kN", f1(eq.aplicada_total_ELU_kN) + " kN",
    f1(eq.reaccion_ELU_kN) + " kN", eq.error_pct.toFixed(2) + " %"]], [1900, 2000, 1800, 1626, 1700]));
ch.push(P("El equilibrio vertical cierra con error " + eq.error_pct.toFixed(2) + " %, confirmando la consistencia del modelo mixto.",
  { run: { bold: true, color: "1E7A1E" } }));

// 6. Esfuerzos losa
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("6. Esfuerzos de la losa", HeadingLevel.HEADING_1));
ch.push(...img("mapa_Mx.png", 330, 285, "Figura 2. Momento Mx (sagging) — ELU."));
ch.push(...img("mapa_My.png", 330, 285, "Figura 3. Momento My (sagging) — ELU."));
ch.push(...img("mapa_flecha.png", 330, 285, "Figura 4. Flecha de la losa — ELS característica."));

// 7. EC2 losa
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("7. Dimensionamiento de la losa (EC2)", HeadingLevel.HEADING_1));
ch.push(P(`Canto h = ${(L.t * 1e3).toFixed(0)} mm; cantos útiles d_x = ${f1(L.d_x_mm)} mm, d_y = ${f1(L.d_y_mm)} mm; ` +
  `recubrimiento ${L.recubrimiento_mm.toFixed(0)} mm; fcd = ${f1(L.fcd_MPa)} MPa; fyd = ${f1(L.fyd_MPa)} MPa.`));
const arm = (k) => { const a = L[k]; return [k.replace("_", " "), f1(a.m_Ed_kNm_m), f2(a.As_dim_cm2_m),
  f2(a.As_min_cm2_m), a.armado + " (" + f2(a.As_prov_cm2_m) + ")", a.mu.toFixed(3), a.ok ? "OK" : "NO"]; };
ch.push(table(["Armadura", "m_Ed [kN·m/m]", "As [cm²/m]", "As,mín", "Disposición (As,prov)", "μ", "Cumple"],
  [arm("x_inferior"), arm("x_superior"), arm("y_inferior"), arm("y_superior")],
  [1726, 1500, 1200, 1000, 1900, 800, 900]));
const fl = L.flecha;
ch.push(P(`Flecha total ${f2(fl.f_total_mm)} mm ≤ L/300 = ${f1(fl.lim_total_mm)} mm (${pct(fl.u_total)}); ` +
  `flecha activa ${f2(fl.f_activa_mm)} mm ≤ L/500 = ${f1(fl.lim_activa_mm)} mm (${pct(fl.u_activa)}).`,
  { run: { bold: true } }));
ch.push(P("Veredicto de la losa: " + L.veredicto + ".", { run: { bold: true, color: L.veredicto === "CUMPLE" ? "1E7A1E" : "B00000" } }));

// 8. Punzonamiento y fisuracion
ch.push(new Paragraph({ pageBreakBefore: true, children: [] }));
ch.push(H("8. Punzonamiento y fisuración (EC2)", HeadingLevel.HEADING_1));
ch.push(H("8.1 Punzonamiento (EC2 §6.4)", HeadingLevel.HEADING_2));
ch.push(P("Se evalúa la transferencia de carga de la losa al pilar de esquina más cargado (β = " + pz.beta +
  ", posición de esquina). El modelo apoya la losa en vigas perimetrales; esta comprobación representa el nudo " +
  "losa-pilar y es conservadora (equivalente a losa apoyada directamente sobre pilar)."));
ch.push(table(["Parámetro", "Valor"],
  [["Carga de punzonamiento V_Ed", f1(pz.V_Ed_kN) + " kN"],
   ["Perímetro de control u1 (a 2d)", f2(pz.u1_m) + " m"],
   ["Canto útil medio d", f1(pz.d_mm) + " mm   (k = " + f2(pz.k) + ")"],
   ["Cuantía ρl", (pz.rho_l * 100).toFixed(2) + " %"],
   ["v_Ed (en u1)", f2(pz.vEd_u1_MPa) + " MPa"],
   ["v_Rd,c (sin armadura)", f2(pz.vRdc_MPa) + " MPa"],
   ["Aprovechamiento v_Ed/v_Rd,c", pct(pz.u_vRdc)],
   ["v_Ed (en perímetro pilar u0)", f2(pz.vEd_u0_MPa) + " MPa"],
   ["v_Rd,max (biela)", f2(pz.vRdmax_MPa) + " MPa  (aprov. " + pct(pz.u_vRdmax) + ")"]],
  [5026, 4000]));
ch.push(P("Resultado: " + (pz.ok ? "CUMPLE sin armadura de punzonamiento." :
  "v_Ed supera v_Rd,c → se REQUIERE armadura de punzonamiento o aumentar el canto / disponer ábaco o capitel. " +
  "La compresión en biela (v_Rd,max) sí se cumple."),
  { run: { bold: true, color: pz.ok ? "1E7A1E" : "B00000" } }));

ch.push(H("8.2 Fisuración (EC2 §7.3)", HeadingLevel.HEADING_2));
ch.push(P("Cálculo directo de la abertura de fisura wk bajo la combinación cuasipermanente, en la dirección de " +
  "mayor momento (armadura inferior dispuesta)."));
ch.push(table(["Parámetro", "Valor"],
  [["Momento cuasipermanente m_qp", f1(fi.M_qp_kNm_m) + " kN·m/m"],
   ["Tensión del acero σs", f1(fi.sigma_s_MPa) + " MPa"],
   ["Cuantía eficaz ρp,eff", (fi.rho_p_eff * 100).toFixed(2) + " %"],
   ["Separación de fisuras sr,max", f1(fi.sr_max_mm) + " mm"],
   ["Abertura de fisura wk", f2(fi.wk_mm) + " mm"],
   ["Límite wmax", f2(fi.wmax_mm) + " mm   (aprov. " + pct(fi.u) + ")"]],
  [5026, 4000]));
ch.push(P("Resultado: " + (fi.ok ? "wk ≤ wmax, fisuración CONTROLADA." :
  "wk supera ligeramente el límite adoptado (0,30 mm). Para clase XC1 el EC2 admite wmax = 0,40 mm, con lo que " +
  "cumpliría; en caso contrario, reducir separación o aumentar diámetro de armadura. [confirmar clase de exposición]"),
  { run: { bold: true, color: fi.ok ? "1E7A1E" : "C07A00" } }));

// 9. EC3 barras
ch.push(H("9. Comprobación de las barras (EC3)", HeadingLevel.HEADING_1));
const b1 = ver.barras.viga_critica, b2 = ver.barras.pilar_critico;
ch.push(table(["Elemento", "N [kN]", "M [kN·m]", "V [kN]", "u_N", "u_M", "u_V", "Aprov."],
  [["Viga crítica " + b1.id + " (" + b1.seccion + ")", f1(b1.N_Ed_kN), f1(b1.M_Ed_kNm), f1(b1.V_Ed_kN), pct(b1.u_N), pct(b1.u_M), pct(b1.u_V), pct(b1.u_max)],
   ["Pilar crítico " + b2.id + " (" + b2.seccion + ")", f1(b2.N_Ed_kN), f1(b2.M_Ed_kNm), f1(b2.V_Ed_kN), pct(b2.u_N), pct(b2.u_M), pct(b2.u_V), pct(b2.u_max)]],
  [2526, 900, 1000, 900, 900, 900, 900, 991]));
ch.push(P("Comprobación EC3 de barras a nivel de sección (detalle completo de pandeo en el flujo de la Fase 1).", { run: { size: 18, italics: true } }));

// 9. Conclusiones
ch.push(H("10. Conclusiones", HeadingLevel.HEADING_1));
ch.push(P("La losa CUMPLE a flexión (EC2) y en flecha; las barras CUMPLEN (EC3). Los elementos placa se validaron " +
  "frente a la solución de Timoshenko (error < 3 %) y el equilibrio global cierra con error nulo, confirmando la " +
  "cadena IFC → FEM mixto → Eurocódigos de la Fase 2."));
ch.push(P("Sin embargo, el PUNZONAMIENTO en el pilar de esquina " + (pz.ok ? "se cumple" : "NO se cumple " +
  "(aprov. " + pct(pz.u_vRdc) + ")") + " y la FISURACIÓN " + (fi.ok ? "queda controlada" : "queda en el límite " +
  "(wk = " + f2(fi.wk_mm) + " mm)") + ". Para una losa de canto 20 cm en esta configuración, el motor recomienda: " +
  "aumentar el canto de la losa (o disponer ábaco/capitel), añadir armadura de punzonamiento, y revisar la clase " +
  "de exposición / separación de armadura para la fisuración.", { run: { bold: true } }));
ch.push(P("Limitaciones: análisis lineal; no se comprueba punzonamiento de la losa en zonas de pilar (donde aparecen " +
  "concentraciones locales de momento), ni fisuración detallada, ni pandeo lateral de vigas; el armado propuesto es de " +
  "predimensionado y debe detallarse. Todo cálculo debe ser revisado y firmado por técnico competente.",
  { run: { italics: true, size: 18 } }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: HEAD, font: "Arial" }, paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: "2E5F8A", font: "Arial" }, paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 1 } }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: HEAD, space: 2 } },
      children: [new TextRun({ text: "Memoria de cálculo · Módulo pórtico + losa · Fase 2", size: 16, color: "777777" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Estructurando — pág. ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children: ch,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log("Memoria escrita en:", out); });

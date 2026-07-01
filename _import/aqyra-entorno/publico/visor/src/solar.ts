/**
 * Soleamiento y Norte real (P1·A) — herramienta de ayuda al diseño sobre el
 * emplazamiento ya georreferenciado. Módulo PURO (sin DOM, sin web-ifc) para que
 * tenga golden delante antes de cablearlo a la maqueta del skin Diseño.
 *
 * Dos piezas:
 *  1. Norte real: a partir de la rotación de IfcMapConversion (GeoRef.rotationDeg)
 *     devuelve la dirección del Norte geográfico en los ejes del proyecto (XY),
 *     para alinear los cardinales N-S-E-O ya dibujados con la orientación real.
 *  2. Soleamiento: posición del Sol (altitud/azimut) para una latitud/longitud y
 *     un instante, y la sombra proyectada (dirección y factor de longitud). Sirve
 *     para orientación de fachadas y sombras básicas.
 *
 * Precisión: algoritmo solar de bajo orden (NOAA/Meeus simplificado), error típico
 * < ~0,2° — sobrado para orientación y soleamiento de diseño. NO incluye refracción
 * atmosférica. El instante se da en UTC (el llamador convierte la hora civil local;
 * Sant Cugat = UTC+1 en invierno, UTC+2 en verano).
 */

const RAD = Math.PI / 180;
const DEG = 180 / Math.PI;

/** Posición aparente del Sol. azimuthDeg medido desde el Norte, horario (0=N, 90=E, 180=S, 270=O). */
export interface SunPosition {
  /** Altitud sobre el horizonte (grados). Negativa ⇒ Sol bajo el horizonte. */
  altitudeDeg: number;
  /** Azimut desde el Norte geográfico, sentido horario (grados, 0..360). */
  azimuthDeg: number;
}

/**
 * Dirección del Norte REAL en los ejes del proyecto (XY del modelo / de la maqueta),
 * dada la rotación de IfcMapConversion (ángulo del eje +X del proyecto respecto al
 * Este del mapa, CCW positivo). rotationDeg=0 ⇒ Norte = +Y. Vector unitario.
 */
export function trueNorthInProject(rotationDeg = 0): { x: number; y: number } {
  const a = rotationDeg * RAD;
  return { x: Math.sin(a), y: Math.cos(a) };
}

/** Día juliano a partir de un Date (su instante absoluto, UTC). */
function julianDay(date: Date): number {
  return date.getTime() / 86400000 + 2440587.5;
}

/**
 * Posición del Sol para (lat, lon) en grados decimales y un instante UTC.
 * lon positiva al Este. Algoritmo NOAA/Meeus de bajo orden.
 */
export function sunPosition(latDeg: number, lonDeg: number, dateUtc: Date): SunPosition {
  const n = julianDay(dateUtc) - 2451545.0; // días desde J2000.0

  // Longitud media y anomalía media del Sol (grados).
  const L = ((280.46 + 0.9856474 * n) % 360 + 360) % 360;
  const g = (((357.528 + 0.9856003 * n) % 360 + 360) % 360) * RAD;

  // Longitud eclíptica aparente y oblicuidad (grados).
  const lambda = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * RAD;
  const eps = (23.439 - 0.0000004 * n) * RAD;

  // Declinación y ascensión recta.
  const delta = Math.asin(Math.sin(eps) * Math.sin(lambda));
  const alpha = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda)) * DEG;

  // Tiempo sidéreo: GMST (h) → tiempo sidéreo local (grados) → ángulo horario.
  const gmst = ((18.697374558 + 24.06570982441908 * n) % 24 + 24) % 24;
  const lst = (gmst * 15 + lonDeg) % 360;
  let H = (lst - alpha) % 360;
  if (H < -180) H += 360;
  if (H > 180) H -= 360;
  H *= RAD;

  const lat = latDeg * RAD;
  const sinAlt = Math.sin(lat) * Math.sin(delta) + Math.cos(lat) * Math.cos(delta) * Math.cos(H);
  const altitudeDeg = Math.asin(sinAlt) * DEG;

  // Azimut de Meeus (desde el Sur, positivo al Oeste) → desde el Norte, horario.
  const aSouth =
    Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(lat) - Math.tan(delta) * Math.cos(lat)) * DEG;
  const azimuthDeg = (aSouth + 180 + 360) % 360;

  return { altitudeDeg, azimuthDeg };
}

/**
 * Sombra horizontal de un elemento vertical para una posición del Sol:
 * dirección (azimut desde el Norte, opuesta al Sol) y factor de longitud por unidad
 * de altura (cot(altitud)). Con el Sol en o bajo el horizonte la sombra es infinita
 * (factor = Infinity): no hay soleamiento útil.
 */
export function shadow(sun: SunPosition): { azimuthDeg: number; lengthFactor: number } {
  const lengthFactor = sun.altitudeDeg > 0 ? 1 / Math.tan(sun.altitudeDeg * RAD) : Infinity;
  return { azimuthDeg: (sun.azimuthDeg + 180) % 360, lengthFactor };
}

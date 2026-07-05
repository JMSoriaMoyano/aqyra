/** El logo «la apertura»: anillo de 6 segmentos + núcleo.
 *  Doble uso — marca en reposo y, con `thinking`, ensamblaje aleatorio lento (~6,2 s). */

const SEG = "M3.5,-39.8 A40,40 0 0 1 32.8,-22.9 L14.7,-10.3 A18,18 0 0 0 1.57,-17.9 Z";

// posición (grados) → turno de aparición (keyTimes) para el ensamblaje aleatorio
const SLOTS: { a: number; kt: string }[] = [
  { a: 0, kt: "0;0.33;0.43;0.88;1" },
  { a: 60, kt: "0;0.06;0.16;0.88;1" },
  { a: 120, kt: "0;0.51;0.61;0.88;1" },
  { a: 180, kt: "0;0.15;0.25;0.88;1" },
  { a: 240, kt: "0;0.24;0.34;0.88;1" },
  { a: 300, kt: "0;0.42;0.52;0.88;1" },
];

export function AqyraMark({
  size = 32,
  thinking = false,
  useAccent = false,
}: {
  size?: number;
  thinking?: boolean;
  useAccent?: boolean;
}) {
  const cls = "aqmark" + (useAccent ? " accent" : "");
  if (!thinking) {
    return (
      <svg className={cls} width={size} height={size} viewBox="0 0 100 100" aria-label="Aqyra">
        <g transform="translate(50,50)">
          {SLOTS.map((s) => (
            <path key={s.a} className="seg" d={SEG} transform={`rotate(${s.a})`} />
          ))}
          <circle className="core" cx="0" cy="0" r="7.5" />
        </g>
      </svg>
    );
  }
  return (
    <svg className={cls} width={size} height={size} viewBox="0 0 100 100" aria-label="Aqyra pensando">
      <g transform="translate(50,50)">
        <circle className="core" cx="0" cy="0" r="7.5">
          <animate attributeName="r" values="4;8;7.5" keyTimes="0;0.1;1" dur="6.2s" repeatCount="indefinite" />
        </circle>
        {SLOTS.map((s) => (
          <g key={s.a} transform={`rotate(${s.a})`}>
            <path className="seg" d={SEG} />
            <animateTransform
              attributeName="transform"
              additive="sum"
              type="scale"
              values="0;0;1;1;0"
              keyTimes={s.kt}
              dur="6.2s"
              repeatCount="indefinite"
            />
            <animate attributeName="opacity" values="0;0;1;1;0" keyTimes={s.kt} dur="6.2s" repeatCount="indefinite" />
          </g>
        ))}
      </g>
    </svg>
  );
}

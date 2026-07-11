// Spectrum Camelot wheel — the brand signature, ported from the Python SVG
// generator. `present` null lights every key (landing hero); a set of codes
// lights only those (used later in the analyzer).
const CX = 200;
const CY = 200;
const RINGS: [number, number, string][] = [
  [132, 190, "B"],
  [74, 128, "A"],
];
const GAP = 1.4;

function annular(rIn: number, rOut: number, a0: number, a1: number): string {
  const a0r = (a0 * Math.PI) / 180;
  const a1r = (a1 * Math.PI) / 180;
  const x0o = CX + rOut * Math.cos(a0r);
  const y0o = CY + rOut * Math.sin(a0r);
  const x1o = CX + rOut * Math.cos(a1r);
  const y1o = CY + rOut * Math.sin(a1r);
  const x1i = CX + rIn * Math.cos(a1r);
  const y1i = CY + rIn * Math.sin(a1r);
  const x0i = CX + rIn * Math.cos(a0r);
  const y0i = CY + rIn * Math.sin(a0r);
  return `M ${x0o.toFixed(2)} ${y0o.toFixed(2)} A ${rOut} ${rOut} 0 0 1 ${x1o.toFixed(
    2,
  )} ${y1o.toFixed(2)} L ${x1i.toFixed(2)} ${y1i.toFixed(2)} A ${rIn} ${rIn} 0 0 0 ${x0i.toFixed(
    2,
  )} ${y0i.toFixed(2)} Z`;
}

export default function CamelotWheel({ present }: { present?: Set<string> }) {
  const segments: React.ReactElement[] = [];
  const labels: React.ReactElement[] = [];

  for (const [rIn, rOut, letter] of RINGS) {
    for (let i = 0; i < 12; i++) {
      const code = `${i + 1}${letter}`;
      const lit = !present || present.has(code);
      const a0 = -90 + i * 30 + GAP / 2;
      const a1 = -90 + (i + 1) * 30 - GAP / 2;
      const hue = (i / 12) * 360;
      const fill = lit
        ? `hsl(${hue.toFixed(0)} 68% ${letter === "B" ? "56%" : "46%"})`
        : "rgba(255,255,255,0.05)";
      const textFill = lit ? "#121016" : "rgba(255,255,255,0.3)";
      segments.push(
        <path key={`s${code}`} d={annular(rIn, rOut, a0, a1)} fill={fill} stroke="#121016" strokeWidth={1.5} />,
      );
      const amid = (((a0 + a1) / 2) * Math.PI) / 180;
      const rmid = (rIn + rOut) / 2;
      labels.push(
        <text
          key={`t${code}`}
          x={(CX + rmid * Math.cos(amid)).toFixed(1)}
          y={(CY + rmid * Math.sin(amid)).toFixed(1)}
          fill={textFill}
          fontSize={12}
          fontWeight={700}
          fontFamily="var(--font-mono)"
          textAnchor="middle"
          dominantBaseline="central"
        >
          {code}
        </text>,
      );
    }
  }

  return (
    <svg
      viewBox="0 0 400 400"
      role="img"
      aria-label="Camelot wheel of musical keys"
      className="relative z-10 h-auto w-full [filter:drop-shadow(0_0_26px_rgba(94,234,212,0.14))]"
    >
      {segments}
      <circle cx={CX} cy={CY} r={70} fill="#171420" stroke="rgba(255,255,255,0.12)" strokeWidth={1} />
      <text x={CX} y={CY - 5} fill="#fff" fontSize={15} fontWeight={700} fontFamily="var(--font-display)" textAnchor="middle">
        CAMELOT
      </text>
      <text x={CX} y={CY + 15} fill="#5eead4" fontSize={10} letterSpacing={3} fontFamily="var(--font-mono)" textAnchor="middle">
        WHEEL
      </text>
      {labels}
    </svg>
  );
}

"use client";

// Shared set visualization — used by the Analyze module (fresh results) and
// the Set builder (saved sets). One source of truth for how a set looks.

import Link from "next/link";
import type { PlaylistRow } from "@/lib/api";
import type { Role } from "@/lib/entitlements";

/** Same hue mapping as the Camelot wheel: number → hue, ring → lightness. */
export function camelotColor(code: string): string {
  const num = parseInt(code, 10);
  if (!Number.isFinite(num)) return "var(--color-mint)";
  const hue = ((num - 1) / 12) * 360;
  return `hsl(${hue.toFixed(0)} 62% ${code.toUpperCase().endsWith("B") ? 64 : 54}%)`;
}

export const EXPORT_FORMATS: [string, string, string, boolean][] = [
  // fmt, label, filename, pro-only
  ["csv", "CSV", "keyflow_set.csv", false],
  ["m3u", "M3U", "keyflow_set.m3u", false],
  ["rekordbox", "rekordbox XML", "keyflow_set.xml", true],
  ["serato", "Serato crate", "keyflow_set.crate", true],
  ["traktor", "Traktor NML", "keyflow_set.nml", true],
];

export function EnergyArc({ rows }: { rows: PlaylistRow[] }) {
  if (rows.length < 2) return null;
  const energies = rows.map((r) => r.energy);
  const min = Math.min(...energies);
  const max = Math.max(...energies);
  const span = max - min || 1;
  const W = 560;
  const H = 96;
  const pad = 10;
  const x = (i: number) => pad + (i / (rows.length - 1)) * (W - 2 * pad);
  const y = (e: number) => H - pad - ((e - min) / span) * (H - 2 * pad);
  const points = rows.map((r, i) => `${x(i).toFixed(1)},${y(r.energy).toFixed(1)}`);
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="h-24 w-full"
      role="img"
      aria-label="Energy across the set, in playing order"
    >
      <polygon
        points={`${pad},${H - pad} ${points.join(" ")} ${W - pad},${H - pad}`}
        fill="rgba(94,234,212,0.09)"
      />
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke="var(--color-mint)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {rows.map((r, i) => (
        <circle key={r.order} cx={x(i)} cy={y(r.energy)} r="3" fill="var(--color-mint)">
          <title>{`${r.order}. ${r.title} — ${r.energy.toFixed(1)} dB`}</title>
        </circle>
      ))}
    </svg>
  );
}

export function MetricChips({ rows }: { rows: PlaylistRow[] }) {
  const avgBpm = rows.reduce((s, r) => s + r.bpm, 0) / (rows.length || 1);
  const keys = new Map<string, number>();
  rows.forEach((r) => keys.set(r.camelot, (keys.get(r.camelot) || 0) + 1));
  const topKey = [...keys.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
  const scored = rows.filter((r) => r.transition_score_from_previous !== null);
  const avgScore = scored.length
    ? scored.reduce((s, r) => s + (r.transition_score_from_previous || 0), 0) / scored.length
    : 0;

  return (
    <div className="grid gap-3 sm:grid-cols-4">
      {[
        [String(rows.length), "tracks in the set"],
        [avgBpm.toFixed(1), "average BPM"],
        [topKey, "most common key"],
        [avgScore.toFixed(1), "avg transition score"],
      ].map(([value, label]) => (
        <div key={label} className="rounded-2xl border border-line bg-surface p-4">
          <div className="font-mono text-2xl font-semibold text-mint">{value}</div>
          <div className="mt-1 text-xs uppercase tracking-[0.14em] text-[color:var(--faint)]">
            {label}
          </div>
        </div>
      ))}
    </div>
  );
}

export function PlaylistTable({
  rows,
  onMove,
  busy,
}: {
  rows: PlaylistRow[];
  /** When given, each row grows ▲▼ controls; (index, -1 | 1) → new order. */
  onMove?: (index: number, delta: -1 | 1) => void;
  busy?: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-line font-mono text-[0.68rem] uppercase tracking-[0.16em] text-[color:var(--faint)]">
            <th className="px-4 py-3 font-medium">#</th>
            <th className="px-4 py-3 font-medium">Track</th>
            <th className="px-4 py-3 font-medium">Key</th>
            <th className="px-4 py-3 font-medium">BPM</th>
            <th className="px-4 py-3 font-medium">Energy</th>
            <th className="px-4 py-3 font-medium">Transition</th>
            {onMove && <th className="px-4 py-3 font-medium">Move</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.order} className="border-b border-line/60 last:border-0">
              <td className="px-4 py-3 font-mono text-[color:var(--faint)]">{row.order}</td>
              <td className="max-w-[280px] truncate px-4 py-3 font-medium">{row.title}</td>
              <td className="px-4 py-3">
                <span
                  className="inline-block rounded-full border px-2.5 py-0.5 font-mono text-xs font-semibold"
                  style={{ color: camelotColor(row.camelot), borderColor: "var(--color-line)" }}
                >
                  {row.camelot}
                </span>
                <span className="ml-2 text-xs text-[color:var(--muted)]">{row.key}</span>
              </td>
              <td className="px-4 py-3 font-mono">{row.bpm.toFixed(1)}</td>
              <td className="px-4 py-3 font-mono text-[color:var(--muted)]">
                {row.energy.toFixed(1)} dB
              </td>
              <td className="px-4 py-3 font-mono">
                {row.transition_score_from_previous === null ? (
                  <span className="text-[color:var(--faint)]">opener</span>
                ) : (
                  row.transition_score_from_previous.toFixed(1)
                )}
              </td>
              {onMove && (
                <td className="px-4 py-3">
                  <span className="flex gap-1">
                    <button
                      onClick={() => onMove(index, -1)}
                      disabled={busy || index === 0}
                      aria-label={`Move ${row.title} earlier`}
                      className="rounded-md border border-line bg-surface-2 px-2 py-0.5 font-mono text-xs transition-colors hover:border-mint/50 disabled:cursor-not-allowed disabled:opacity-30"
                    >
                      ▲
                    </button>
                    <button
                      onClick={() => onMove(index, 1)}
                      disabled={busy || index === rows.length - 1}
                      aria-label={`Move ${row.title} later`}
                      className="rounded-md border border-line bg-surface-2 px-2 py-0.5 font-mono text-xs transition-colors hover:border-mint/50 disabled:cursor-not-allowed disabled:opacity-30"
                    >
                      ▼
                    </button>
                  </span>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ExportRow({
  role,
  onDownload,
  note,
}: {
  role: Role;
  onDownload: (fmt: string, filename: string) => void;
  note: string | null;
}) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <h2 className="font-display text-lg font-bold">Take it with you</h2>
      <p className="mt-1 text-sm text-[color:var(--muted)]">
        CSV and M3U are free. DJ software formats come with Pro.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {EXPORT_FORMATS.map(([fmt, label, filename, pro]) => {
          const locked = pro && role === "free";
          return locked ? (
            <Link
              key={fmt}
              href="/#pricing"
              className="rounded-full border border-line bg-surface-2 px-4 py-2 text-sm font-semibold text-[color:var(--faint)] transition-colors hover:border-lavender/50 hover:text-lavender"
              title={`${label} export is a Pro feature`}
            >
              {label} · Pro
            </Link>
          ) : (
            <button
              key={fmt}
              onClick={() => onDownload(fmt, filename)}
              className="rounded-full border border-mint/40 bg-mint/10 px-4 py-2 text-sm font-semibold text-mint transition-colors hover:bg-mint/20"
            >
              {label}
            </button>
          );
        })}
      </div>
      {note && <p className="mt-3 text-sm text-[#f2a6c9]">{note}</p>}
    </div>
  );
}

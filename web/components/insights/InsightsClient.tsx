"use client";

// Insights module — the big picture of a saved set: which keys are in play
// (Camelot wheel + mix), how BPM and energy spread, and how every track
// pairs with every other (compatibility heatmap, scored by the engine).

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { PlaylistRow, SetDetail } from "@/lib/api";
import { apiDetail, apiUrl } from "@/lib/api";
import CamelotWheel from "@/components/CamelotWheel";
import { camelotColor } from "@/components/set/SetResults";

type Matrix = { titles: string[]; matrix: (number | null)[][] };

function KeyMix({ rows }: { rows: PlaylistRow[] }) {
  const counts = new Map<string, number>();
  rows.forEach((r) => counts.set(r.camelot, (counts.get(r.camelot) || 0) + 1));
  const entries = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  return (
    <div className="flex flex-wrap gap-2">
      {entries.map(([code, count]) => (
        <span
          key={code}
          className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface-2 px-3 py-1 font-mono text-xs font-semibold"
          style={{ color: camelotColor(code) }}
        >
          {code}
          <span className="text-[color:var(--faint)]">× {count}</span>
        </span>
      ))}
    </div>
  );
}

function BpmEnergyScatter({ rows }: { rows: PlaylistRow[] }) {
  const W = 520;
  const H = 300;
  const pad = 42;
  const bpms = rows.map((r) => r.bpm);
  const energies = rows.map((r) => r.energy);
  const bMin = Math.min(...bpms);
  const bMax = Math.max(...bpms);
  const eMin = Math.min(...energies);
  const eMax = Math.max(...energies);
  const bSpan = bMax - bMin || 1;
  const eSpan = eMax - eMin || 1;
  const x = (b: number) => pad + ((b - bMin) / bSpan) * (W - 2 * pad);
  const y = (e: number) => H - pad - ((e - eMin) / eSpan) * (H - 2 * pad);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="h-auto w-full"
      role="img"
      aria-label="Each track by tempo and energy"
    >
      <line x1={pad} y1={H - pad} x2={W - pad} y2={H - pad} stroke="var(--color-line)" />
      <line x1={pad} y1={pad} x2={pad} y2={H - pad} stroke="var(--color-line)" />
      <text x={x(bMin)} y={H - pad + 18} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="start">
        {bMin.toFixed(0)}
      </text>
      <text x={x(bMax)} y={H - pad + 18} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="end">
        {bMax.toFixed(0)}
      </text>
      <text x={W / 2} y={H - 6} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="2">
        BPM →
      </text>
      <text x={pad - 8} y={y(eMin) + 4} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="end">
        {eMin.toFixed(0)}
      </text>
      <text x={pad - 8} y={y(eMax) + 4} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="end">
        {eMax.toFixed(0)}
      </text>
      <text x={14} y={H / 2} fill="var(--faint)" fontSize="11" fontFamily="var(--font-mono)" textAnchor="middle" letterSpacing="2" transform={`rotate(-90 14 ${H / 2})`}>
        ENERGY dB →
      </text>
      {rows.map((r) => (
        <circle key={r.title} cx={x(r.bpm)} cy={y(r.energy)} r="7" fill={camelotColor(r.camelot)} fillOpacity="0.85" stroke="#121016" strokeWidth="1.5">
          <title>{`${r.title} — ${r.camelot} · ${r.bpm.toFixed(1)} BPM · ${r.energy.toFixed(1)} dB`}</title>
        </circle>
      ))}
    </svg>
  );
}

function Heatmap({ titles, matrix }: Matrix) {
  const n = titles.length;
  const cell = n > 18 ? 22 : 34;
  const gutter = 34;
  const size = gutter + n * cell + 6;
  const values = matrix.flat().filter((v): v is number => v !== null);
  const maxAbs = Math.max(...values.map(Math.abs), 1);

  const fill = (v: number | null): string => {
    if (v === null) return "rgba(255,255,255,0.03)";
    const t = Math.abs(v) / maxAbs;
    return v >= 0
      ? `rgba(94,234,212,${(0.07 + 0.75 * t).toFixed(3)})`
      : `rgba(242,166,201,${(0.07 + 0.75 * t).toFixed(3)})`;
  };

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="h-auto w-full max-w-[560px]"
      role="img"
      aria-label="Transition compatibility between every pair of tracks"
    >
      {titles.map((_, i) => (
        <text key={`c${i}`} x={gutter + i * cell + cell / 2} y={gutter - 10} fill="var(--faint)" fontSize={cell > 25 ? 11 : 9} fontFamily="var(--font-mono)" textAnchor="middle">
          {i + 1}
        </text>
      ))}
      {titles.map((_, i) => (
        <text key={`r${i}`} x={gutter - 10} y={gutter + i * cell + cell / 2 + 3} fill="var(--faint)" fontSize={cell > 25 ? 11 : 9} fontFamily="var(--font-mono)" textAnchor="end">
          {i + 1}
        </text>
      ))}
      {matrix.map((fila, i) =>
        fila.map((v, j) => (
          <rect
            key={`${i}-${j}`}
            x={gutter + j * cell + 1}
            y={gutter + i * cell + 1}
            width={cell - 2}
            height={cell - 2}
            rx={4}
            fill={fill(v)}
          >
            <title>
              {v === null
                ? `${titles[i]} — same track`
                : `${titles[i]} → ${titles[j]}: ${v.toFixed(1)}`}
            </title>
          </rect>
        )),
      )}
    </svg>
  );
}

export default function InsightsClient({
  sets,
}: {
  sets: { id: string; name: string }[];
}) {
  const supabase = createClient();
  const [activeId, setActiveId] = useState(sets[0].id);
  const [detail, setDetail] = useState<SetDetail | null>(null);
  const [matrix, setMatrix] = useState<Matrix | null>(null);
  const [error, setError] = useState<string | null>(null);

  const token = useCallback(async (): Promise<string | null> => {
    if (!supabase) return null;
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  }, [supabase]);

  useEffect(() => {
    let alive = true;
    setDetail(null);
    setMatrix(null);
    setError(null);
    (async () => {
      const bearer = await token();
      if (!bearer) return;
      try {
        const headers = { Authorization: `Bearer ${bearer}` };
        const [detailRes, matrixRes] = await Promise.all([
          fetch(`${apiUrl()}/v1/sets/${activeId}`, { headers }),
          fetch(`${apiUrl()}/v1/sets/${activeId}/matrix`, { headers }),
        ]);
        if (!alive) return;
        if (!detailRes.ok) {
          setError(await apiDetail(detailRes));
          return;
        }
        setDetail(await detailRes.json());
        if (matrixRes.ok) setMatrix(await matrixRes.json());
      } catch {
        if (alive) setError(`Couldn't reach the engine at ${apiUrl()}.`);
      }
    })();
    return () => {
      alive = false;
    };
  }, [activeId, token]);

  if (!supabase) return null;

  return (
    <div className="animate-rise">
      {sets.length > 1 && (
        <label className="mt-8 flex items-center gap-3 text-sm text-[color:var(--muted)]">
          <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
            Set
          </span>
          <select
            value={activeId}
            onChange={(e) => setActiveId(e.target.value)}
            className="rounded-full border border-line bg-surface-2 px-3 py-1.5 text-sm text-ink outline-none transition-colors focus:border-mint/60"
          >
            {sets.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
      )}

      {error && (
        <div className="mt-8 rounded-2xl border border-[#f2a6c9]/30 bg-[#f2a6c9]/5 p-5">
          <p className="font-medium text-[#f2a6c9]">{error}</p>
        </div>
      )}

      {!detail && !error && (
        <p className="mt-8 text-[color:var(--muted)]" aria-live="polite">
          Reading the set…
        </p>
      )}

      {detail && (
        <>
          <div className="mt-8 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-display text-lg font-bold">Keys in play</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Lit segments are the keys your set actually uses — neighbours mix smoothly.
              </p>
              <div className="mx-auto mt-4 max-w-[340px]">
                <CamelotWheel present={new Set(detail.playlist.map((r) => r.camelot))} />
              </div>
              <div className="mt-4">
                <KeyMix rows={detail.playlist} />
              </div>
            </div>

            <div className="rounded-2xl border border-line bg-surface p-6">
              <h2 className="font-display text-lg font-bold">Tempo × energy</h2>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Every track placed by BPM and loudness, coloured by its key.
              </p>
              <div className="mt-4">
                <BpmEnergyScatter rows={detail.playlist} />
              </div>
            </div>
          </div>

          {matrix && matrix.titles.length > 1 && (
            <div className="mt-4 rounded-2xl border border-line bg-surface p-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="font-display text-lg font-bold">Who pairs with whom</h2>
                <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
                  row → column · mint good · rose clash
                </span>
              </div>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Numbers are playing order. Hover any cell for the pair and its transition score
                — bright mint means the engine loves that hand-off.
              </p>
              <div className="mt-4 overflow-x-auto">
                <Heatmap titles={matrix.titles} matrix={matrix.matrix} />
              </div>
              <ol className="mt-4 grid gap-1 text-xs text-[color:var(--muted)] sm:grid-cols-2 lg:grid-cols-3">
                {matrix.titles.map((t, i) => (
                  <li key={t} className="truncate font-mono">
                    <span className="text-[color:var(--faint)]">{i + 1}.</span> {t}
                  </li>
                ))}
              </ol>
            </div>
          )}

          <p className="mt-6 text-sm text-[color:var(--muted)]">
            Want a different order?{" "}
            <Link
              href={`/app/sets/${activeId}`}
              className="text-mint underline decoration-mint/40 underline-offset-4 hover:decoration-mint"
            >
              Open this set in the builder →
            </Link>
          </p>
        </>
      )}
    </div>
  );
}

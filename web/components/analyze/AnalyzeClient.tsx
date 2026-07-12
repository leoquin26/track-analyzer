"use client";

// Analyze module — the first real workspace module. Uploads audio to the
// FastAPI with the Supabase access token, follows the job, then renders the
// ordered set with an energy arc and exports. No audio is ever stored:
// the engine deletes uploads right after feature extraction.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { JobStatus, PlaylistRow } from "@/lib/api";
import { AUDIO_EXTENSIONS, apiDetail, apiUrl, formatBytes, isAudioFile } from "@/lib/api";
import type { Role } from "@/lib/entitlements";

type Phase =
  | { kind: "pick" }
  | { kind: "uploading" }
  | { kind: "analyzing"; job: JobStatus }
  | { kind: "building" }
  | { kind: "done"; rows: PlaylistRow[]; failed: string[]; jobId: string; cachedHits: number }
  | { kind: "error"; message: string; hint?: string };

const DURATIONS: [number, string, string][] = [
  [60, "Quick", "First 60 s per track"],
  [180, "Standard", "First 3 min per track"],
  [300, "Deep", "First 5 min per track"],
];

const EXPORTS: [string, string, string, boolean][] = [
  // fmt, label, filename, pro-only
  ["csv", "CSV", "keyflow_set.csv", false],
  ["m3u", "M3U", "keyflow_set.m3u", false],
  ["rekordbox", "rekordbox XML", "keyflow_set.xml", true],
  ["serato", "Serato crate", "keyflow_set.crate", true],
  ["traktor", "Traktor NML", "keyflow_set.nml", true],
];

/** Same hue mapping as the Camelot wheel: number → hue, ring → lightness. */
function camelotColor(code: string): string {
  const num = parseInt(code, 10);
  if (!Number.isFinite(num)) return "var(--color-mint)";
  const hue = ((num - 1) / 12) * 360;
  return `hsl(${hue.toFixed(0)} 62% ${code.toUpperCase().endsWith("B") ? 64 : 54}%)`;
}

function EnergyArc({ rows }: { rows: PlaylistRow[] }) {
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

export default function AnalyzeClient({
  role,
  maxTracks,
}: {
  role: Role;
  maxTracks: number | null;
}) {
  const supabase = createClient();
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [duration, setDuration] = useState(180);
  const [phase, setPhase] = useState<Phase>({ kind: "pick" });
  const [dragOver, setDragOver] = useState(false);
  const [exportNote, setExportNote] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const cancelled = useRef(false);

  useEffect(() => () => void (cancelled.current = true), []);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    setPhase({ kind: "pick" });
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => f.name));
      const fresh = Array.from(incoming).filter((f) => isAudioFile(f.name) && !seen.has(f.name));
      return [...prev, ...fresh];
    });
  }, []);

  const overCap = maxTracks !== null && files.length > maxTracks;
  const totalBytes = files.reduce((sum, f) => sum + f.size, 0);

  async function token(): Promise<string | null> {
    if (!supabase) return null;
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  }

  async function start() {
    const bearer = await token();
    if (!bearer) {
      router.push("/login?next=/app/analyze");
      return;
    }
    setExportNote(null);
    setPhase({ kind: "uploading" });

    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("duration", String(duration));

    let jobId: string;
    try {
      const res = await fetch(`${apiUrl()}/v1/analyze`, {
        method: "POST",
        headers: { Authorization: `Bearer ${bearer}` },
        body: form,
      });
      if (!res.ok) {
        const message = await apiDetail(res);
        setPhase({
          kind: "error",
          message,
          hint:
            res.status === 403
              ? "upgrade"
              : res.status === 429
                ? "Give it a moment — analysis requests are rate-limited."
                : undefined,
        });
        return;
      }
      jobId = (await res.json()).job_id;
    } catch {
      setPhase({
        kind: "error",
        message: "Couldn't reach the analysis engine.",
        hint: `Is the API running at ${apiUrl()}?`,
      });
      return;
    }

    // Follow the job until the engine is done with every track.
    while (!cancelled.current) {
      await new Promise((r) => setTimeout(r, 1200));
      let job: JobStatus;
      try {
        const res = await fetch(`${apiUrl()}/v1/jobs/${jobId}`, {
          headers: { Authorization: `Bearer ${bearer}` },
        });
        if (!res.ok) {
          setPhase({ kind: "error", message: await apiDetail(res) });
          return;
        }
        job = await res.json();
      } catch {
        setPhase({ kind: "error", message: "Lost contact with the engine mid-job." });
        return;
      }
      if (job.status === "error") {
        setPhase({ kind: "error", message: job.error || "The analysis failed." });
        return;
      }
      if (job.status === "done") {
        setPhase({ kind: "building" });
        try {
          const [playlistRes, resultRes] = await Promise.all([
            fetch(`${apiUrl()}/v1/playlist`, {
              method: "POST",
              headers: { Authorization: `Bearer ${bearer}`, "Content-Type": "application/json" },
              body: JSON.stringify({ job_id: jobId }),
            }),
            fetch(`${apiUrl()}/v1/jobs/${jobId}/result`, {
              headers: { Authorization: `Bearer ${bearer}` },
            }),
          ]);
          if (!playlistRes.ok) {
            setPhase({ kind: "error", message: await apiDetail(playlistRes) });
            return;
          }
          const rows: PlaylistRow[] = (await playlistRes.json()).playlist;
          const failed: string[] = resultRes.ok ? (await resultRes.json()).failed : [];
          setPhase({ kind: "done", rows, failed, jobId, cachedHits: job.cached_hits });
        } catch {
          setPhase({ kind: "error", message: "The set couldn't be built from the results." });
        }
        return;
      }
      setPhase({ kind: "analyzing", job });
    }
  }

  async function download(fmt: string, filename: string) {
    if (phase.kind !== "done") return;
    const bearer = await token();
    if (!bearer) return;
    setExportNote(null);
    try {
      const res = await fetch(`${apiUrl()}/v1/export/${fmt}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${bearer}`, "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: phase.jobId }),
      });
      if (!res.ok) {
        setExportNote(await apiDetail(res));
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setExportNote("Export failed — couldn't reach the engine.");
    }
  }

  function reset() {
    setFiles([]);
    setExportNote(null);
    setPhase({ kind: "pick" });
  }

  if (!supabase) {
    return (
      <p className="mt-10 text-[color:var(--muted)]">
        Supabase isn&apos;t configured — set NEXT_PUBLIC_SUPABASE_URL and the anon key.
      </p>
    );
  }

  const busy = phase.kind === "uploading" || phase.kind === "analyzing" || phase.kind === "building";

  // ------------------------------------------------------------------ done —
  if (phase.kind === "done") {
    const { rows, failed, cachedHits } = phase;
    const avgBpm = rows.reduce((s, r) => s + r.bpm, 0) / rows.length;
    const keys = new Map<string, number>();
    rows.forEach((r) => keys.set(r.camelot, (keys.get(r.camelot) || 0) + 1));
    const topKey = [...keys.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
    const scored = rows.filter((r) => r.transition_score_from_previous !== null);
    const avgScore = scored.length
      ? scored.reduce((s, r) => s + (r.transition_score_from_previous || 0), 0) / scored.length
      : 0;

    return (
      <div className="animate-rise">
        <div className="mt-8 grid gap-3 sm:grid-cols-4">
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

        <div className="mt-6 rounded-2xl border border-line bg-surface p-5">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-lg font-bold">Energy across the set</h2>
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
              playing order →
            </span>
          </div>
          <div className="mt-3">
            <EnergyArc rows={rows} />
          </div>
        </div>

        <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-surface">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-line font-mono text-[0.68rem] uppercase tracking-[0.16em] text-[color:var(--faint)]">
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Track</th>
                <th className="px-4 py-3 font-medium">Key</th>
                <th className="px-4 py-3 font-medium">BPM</th>
                <th className="px-4 py-3 font-medium">Energy</th>
                <th className="px-4 py-3 font-medium">Transition</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {failed.length > 0 && (
          <p className="mt-4 rounded-xl border border-line bg-surface px-4 py-3 text-sm text-[color:var(--muted)]">
            {failed.length} file{failed.length > 1 ? "s" : ""} couldn&apos;t be analyzed:{" "}
            <span className="font-mono text-xs">{failed.join(", ")}</span>
          </p>
        )}
        {cachedHits > 0 && (
          <p className="mt-3 text-xs text-[color:var(--faint)]">
            {cachedHits} track{cachedHits > 1 ? "s were" : " was"} served from the feature cache —
            repeat analyses are instant.
          </p>
        )}

        <div className="mt-8 rounded-2xl border border-line bg-surface p-5">
          <h2 className="font-display text-lg font-bold">Take it with you</h2>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            CSV and M3U are free. DJ software formats come with Pro.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {EXPORTS.map(([fmt, label, filename, pro]) => {
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
                  onClick={() => download(fmt, filename)}
                  className="rounded-full border border-mint/40 bg-mint/10 px-4 py-2 text-sm font-semibold text-mint transition-colors hover:bg-mint/20"
                >
                  {label}
                </button>
              );
            })}
          </div>
          {exportNote && <p className="mt-3 text-sm text-[#f2a6c9]">{exportNote}</p>}
        </div>

        <button
          onClick={reset}
          className="mt-8 rounded-full border border-line bg-surface-2 px-5 py-2.5 text-sm font-semibold transition-colors hover:border-mint/45"
        >
          Analyze another batch
        </button>
      </div>
    );
  }

  // ------------------------------------------------------- pick / busy / error —
  return (
    <div className="animate-rise">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        className={`mt-8 rounded-3xl border-2 border-dashed p-10 text-center transition-colors ${
          dragOver ? "border-mint/70 bg-mint/5" : "border-line bg-surface"
        }`}
      >
        <svg viewBox="0 0 24 24" className="mx-auto h-8 w-8" fill="none" stroke="var(--color-mint)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M12 17V5" />
          <path d="m7 10 5-5 5 5" />
          <path d="M4 19h16" />
        </svg>
        <p className="mt-3 font-medium">
          Drop your tracks here, or{" "}
          <button
            onClick={() => inputRef.current?.click()}
            className="text-mint underline decoration-mint/40 underline-offset-4 transition-colors hover:decoration-mint"
          >
            browse files
          </button>
        </p>
        <p className="mt-1 text-sm text-[color:var(--muted)]">
          {AUDIO_EXTENSIONS.join(" · ")} — analyzed on the server, deleted right after.
          {maxTracks !== null && ` Free plan: up to ${maxTracks} tracks per batch.`}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={AUDIO_EXTENSIONS.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {files.length > 0 && (
        <div className="mt-5 rounded-2xl border border-line bg-surface p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-display text-lg font-bold">
              {files.length} track{files.length > 1 ? "s" : ""} ready
            </h2>
            <span className="font-mono text-xs text-[color:var(--faint)]">
              {formatBytes(totalBytes)} total
            </span>
          </div>
          <ul className="mt-3 max-h-56 space-y-1 overflow-y-auto pr-1">
            {files.map((f) => (
              <li
                key={f.name}
                className="flex items-center justify-between gap-3 rounded-lg bg-surface-2 px-3 py-1.5 text-sm"
              >
                <span className="truncate">{f.name}</span>
                <span className="flex shrink-0 items-center gap-3">
                  <span className="font-mono text-xs text-[color:var(--faint)]">
                    {formatBytes(f.size)}
                  </span>
                  <button
                    onClick={() => setFiles((prev) => prev.filter((x) => x.name !== f.name))}
                    aria-label={`Remove ${f.name}`}
                    className="text-[color:var(--faint)] transition-colors hover:text-[#f2a6c9]"
                  >
                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
                      <path d="M6 6l12 12M18 6L6 18" />
                    </svg>
                  </button>
                </span>
              </li>
            ))}
          </ul>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="mr-1 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
              Listen depth
            </span>
            {DURATIONS.map(([value, label, hint]) => (
              <button
                key={value}
                onClick={() => setDuration(value)}
                title={hint}
                className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors ${
                  duration === value
                    ? "border-mint/60 bg-mint/10 text-mint"
                    : "border-line bg-surface-2 text-[color:var(--muted)] hover:border-mint/40"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {overCap && (
            <p className="mt-4 rounded-xl border border-lavender/30 bg-lavender/5 px-4 py-3 text-sm">
              Your Free plan analyzes up to <b>{maxTracks}</b> tracks per batch — you have{" "}
              <b>{files.length}</b> queued.{" "}
              <Link href="/#pricing" className="text-lavender underline underline-offset-4">
                Go Pro for unlimited tracks
              </Link>{" "}
              or trim the list.
            </p>
          )}

          <div className="mt-5 flex items-center gap-4">
            <button
              onClick={start}
              disabled={busy || overCap}
              className="rounded-full bg-mint px-6 py-2.5 text-sm font-bold text-[#0c221d] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "Working…" : `Analyze ${files.length} track${files.length > 1 ? "s" : ""}`}
            </button>
            {!busy && (
              <button
                onClick={() => setFiles([])}
                className="text-sm text-[color:var(--muted)] transition-colors hover:text-ink"
              >
                Clear all
              </button>
            )}
          </div>
        </div>
      )}

      {busy && (
        <div className="mt-5 rounded-2xl border border-line bg-surface p-5" aria-live="polite">
          {phase.kind === "analyzing" ? (
            <>
              <div className="flex items-baseline justify-between">
                <p className="font-medium">
                  Listening to your tracks{" "}
                  <span className="font-mono text-sm text-mint">
                    {phase.job.progress}/{phase.job.total}
                  </span>
                </p>
                {phase.job.cached_hits > 0 && (
                  <span className="font-mono text-xs text-[color:var(--faint)]">
                    {phase.job.cached_hits} from cache
                  </span>
                )}
              </div>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-2">
                <div
                  className="h-full rounded-full bg-mint transition-[width] duration-700"
                  style={{
                    width: `${phase.job.total ? (phase.job.progress / phase.job.total) * 100 : 4}%`,
                  }}
                />
              </div>
              <p className="mt-3 text-xs text-[color:var(--faint)]">
                BPM, key, groove and energy per track — roughly a few seconds each.
              </p>
            </>
          ) : (
            <p className="font-medium">
              {phase.kind === "uploading" ? "Sending your tracks to the engine…" : "Ordering the set…"}
            </p>
          )}
        </div>
      )}

      {phase.kind === "error" && (
        <div className="mt-5 rounded-2xl border border-[#f2a6c9]/30 bg-[#f2a6c9]/5 p-5">
          <p className="font-medium text-[#f2a6c9]">{phase.message}</p>
          {phase.hint === "upgrade" ? (
            <p className="mt-2 text-sm text-[color:var(--muted)]">
              <Link href="/#pricing" className="text-lavender underline underline-offset-4">
                See plans
              </Link>{" "}
              — Pro removes the per-batch track limit.
            </p>
          ) : phase.hint ? (
            <p className="mt-2 text-sm text-[color:var(--muted)]">{phase.hint}</p>
          ) : null}
        </div>
      )}
    </div>
  );
}

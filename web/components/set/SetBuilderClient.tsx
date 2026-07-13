"use client";

// Set builder — a saved set as a living document. Reordering and rebuilding
// go through the API so the engine re-scores every transition; the audio is
// long gone, only features travel.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { SetDetail } from "@/lib/api";
import { apiDetail, apiUrl } from "@/lib/api";
import type { Role } from "@/lib/entitlements";
import { EnergyArc, ExportRow, MetricChips, PlaylistTable } from "@/components/set/SetResults";

export default function SetBuilderClient({ setId, role }: { setId: string; role: Role }) {
  const supabase = createClient();
  const router = useRouter();
  const [detail, setDetail] = useState<SetDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [exportNote, setExportNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [nameDraft, setNameDraft] = useState<string | null>(null); // null = not editing
  const [startPick, setStartPick] = useState("");
  const [curve, setCurve] = useState("build_up");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const confirmTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const token = useCallback(async (): Promise<string | null> => {
    if (!supabase) return null;
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  }, [supabase]);

  const absorb = useCallback((d: SetDetail) => {
    setDetail(d);
    setStartPick(d.params?.start_title || "");
    setCurve(d.params?.energy_curve || "build_up");
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      const bearer = await token();
      if (!bearer) {
        router.push(`/login?next=/app/sets/${setId}`);
        return;
      }
      try {
        const res = await fetch(`${apiUrl()}/v1/sets/${setId}`, {
          headers: { Authorization: `Bearer ${bearer}` },
        });
        if (!alive) return;
        if (!res.ok) {
          setLoadError(await apiDetail(res));
          return;
        }
        absorb(await res.json());
      } catch {
        if (alive) setLoadError(`Couldn't reach the engine at ${apiUrl()}.`);
      }
    })();
    return () => {
      alive = false;
    };
  }, [setId, token, router, absorb]);

  async function put(body: Record<string, unknown>) {
    const bearer = await token();
    if (!bearer) return;
    setBusy(true);
    setNote(null);
    try {
      const res = await fetch(`${apiUrl()}/v1/sets/${setId}`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${bearer}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        setNote(await apiDetail(res));
        return;
      }
      absorb(await res.json());
    } catch {
      setNote("Couldn't reach the engine — the change wasn't saved.");
    } finally {
      setBusy(false);
    }
  }

  function move(index: number, delta: -1 | 1) {
    if (!detail) return;
    const titles = detail.playlist.map((r) => r.title);
    const target = index + delta;
    if (target < 0 || target >= titles.length) return;
    [titles[index], titles[target]] = [titles[target], titles[index]];
    void put({ order: titles });
  }

  function rebuild() {
    if (!detail) return;
    void put({
      rebuild: {
        weights: detail.params?.weights,
        start_title: startPick || null,
        energy_curve: curve,
      },
    });
  }

  /** Inspector-style key/BPM correction — server recomputes camelot + scores. */
  function overrideTrack(title: string, patch: { key: string; bpm: number }) {
    void put({ overrides: { [title]: { key: patch.key, bpm: patch.bpm } } });
  }

  async function destroy() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      confirmTimer.current = setTimeout(() => setConfirmDelete(false), 4000);
      return;
    }
    if (confirmTimer.current) clearTimeout(confirmTimer.current);
    const bearer = await token();
    if (!bearer) return;
    setBusy(true);
    try {
      const res = await fetch(`${apiUrl()}/v1/sets/${setId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${bearer}` },
      });
      if (!res.ok) {
        setNote(await apiDetail(res));
        setBusy(false);
        return;
      }
      router.push("/app/sets");
      router.refresh();
    } catch {
      setNote("Couldn't reach the engine — the set wasn't deleted.");
      setBusy(false);
    }
  }

  async function download(fmt: string, filename: string) {
    const bearer = await token();
    if (!bearer) return;
    setExportNote(null);
    try {
      const res = await fetch(`${apiUrl()}/v1/export/${fmt}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${bearer}`, "Content-Type": "application/json" },
        body: JSON.stringify({ set_id: setId }),
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

  if (loadError) {
    return (
      <div className="mt-10 rounded-2xl border border-[#f2a6c9]/30 bg-[#f2a6c9]/5 p-5">
        <p className="font-medium text-[#f2a6c9]">{loadError}</p>
        <Link href="/app/sets" className="mt-2 inline-block text-sm text-[color:var(--muted)] underline underline-offset-4">
          Back to your sets
        </Link>
      </div>
    );
  }

  if (!detail) {
    return (
      <p className="mt-10 text-[color:var(--muted)]" aria-live="polite">
        Loading your set…
      </p>
    );
  }

  const plateauLocked = role === "free";

  return (
    <div className="animate-rise">
      <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
        {nameDraft === null ? (
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold">
            {detail.name}
            <button
              onClick={() => setNameDraft(detail.name)}
              aria-label="Rename set"
              className="text-[color:var(--faint)] transition-colors hover:text-mint"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
              </svg>
            </button>
          </h2>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const clean = nameDraft.trim();
              setNameDraft(null);
              if (clean && clean !== detail.name) void put({ name: clean });
            }}
            className="flex items-center gap-2"
          >
            <input
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              autoFocus
              className="w-64 rounded-full border border-mint/50 bg-surface-2 px-4 py-1.5 font-display text-lg font-bold outline-none"
            />
            <button className="rounded-full border border-mint/40 bg-mint/10 px-4 py-1.5 text-sm font-semibold text-mint">
              Save
            </button>
          </form>
        )}
        <button
          onClick={destroy}
          disabled={busy}
          className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors disabled:opacity-40 ${
            confirmDelete
              ? "border-[#f2a6c9]/60 bg-[#f2a6c9]/10 text-[#f2a6c9]"
              : "border-line bg-surface-2 text-[color:var(--muted)] hover:border-[#f2a6c9]/50 hover:text-[#f2a6c9]"
          }`}
        >
          {confirmDelete ? "Click again to delete" : "Delete set"}
        </button>
      </div>

      <div className="mt-6">
        <MetricChips rows={detail.playlist} />
      </div>

      <div className="mt-6 rounded-2xl border border-line bg-surface p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="font-display text-lg font-bold">Energy across the set</h2>
          <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
            playing order →
          </span>
        </div>
        <div className="mt-3">
          <EnergyArc rows={detail.playlist} />
        </div>
      </div>

      <div className="mt-6 rounded-2xl border border-line bg-surface p-5">
        <h2 className="font-display text-lg font-bold">Rebuild the order</h2>
        <p className="mt-1 text-sm text-[color:var(--muted)]">
          Pick an opener and an energy shape, and the engine re-orders the whole set for flow.
          Manual moves in the table below are kept until the next rebuild.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
              Opener
            </span>
            <select
              value={startPick}
              onChange={(e) => setStartPick(e.target.value)}
              className="rounded-full border border-line bg-surface-2 px-3 py-1.5 text-sm text-ink outline-none transition-colors focus:border-mint/60"
            >
              <option value="">Auto (energy curve decides)</option>
              {detail.playlist.map((r) => (
                <option key={r.title} value={r.title}>
                  {r.title}
                </option>
              ))}
            </select>
          </label>
          <span className="flex items-center gap-2">
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
              Energy
            </span>
            <button
              onClick={() => setCurve("build_up")}
              className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors ${
                curve === "build_up"
                  ? "border-mint/60 bg-mint/10 text-mint"
                  : "border-line bg-surface-2 text-[color:var(--muted)] hover:border-mint/40"
              }`}
            >
              Build up
            </button>
            {plateauLocked ? (
              <Link
                href="/#pricing"
                title="The plateau curve is a Pro feature"
                className="rounded-full border border-line bg-surface-2 px-4 py-1.5 text-sm font-semibold text-[color:var(--faint)] transition-colors hover:border-lavender/50 hover:text-lavender"
              >
                Plateau · Pro
              </Link>
            ) : (
              <button
                onClick={() => setCurve("plateau")}
                className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors ${
                  curve === "plateau"
                    ? "border-mint/60 bg-mint/10 text-mint"
                    : "border-line bg-surface-2 text-[color:var(--muted)] hover:border-mint/40"
                }`}
              >
                Plateau
              </button>
            )}
          </span>
          <button
            onClick={rebuild}
            disabled={busy}
            className="rounded-full bg-mint px-5 py-2 text-sm font-bold text-[#0c221d] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Working…" : "Rebuild order"}
          </button>
        </div>
        {detail.params?.manual && (
          <p className="mt-3 text-xs text-[color:var(--faint)]">
            This order includes manual moves.
          </p>
        )}
        {note && <p className="mt-3 text-sm text-[#f2a6c9]">{note}</p>}
      </div>

      <div className="mt-6">
        <PlaylistTable
          rows={detail.playlist}
          onMove={move}
          onOverride={overrideTrack}
          busy={busy}
        />
      </div>

      <div className="mt-6">
        <ExportRow role={role} onDownload={download} note={exportNote} />
      </div>
    </div>
  );
}

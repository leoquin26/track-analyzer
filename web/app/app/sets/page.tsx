import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole } from "@/lib/entitlements";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";

export const metadata = { title: "Your sets — Keyflow" };

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default async function SetsPage() {
  const supabase = await createClient();
  if (!supabase) redirect("/login");

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login?next=/app/sets");

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, role")
    .eq("id", user.id)
    .single();

  // RLS scopes this to the signed-in user's rows; the jsonb arrow pulls just
  // the order array so we can count tracks without shipping every feature.
  const { data: sets } = await supabase
    .from("sets")
    .select("id, name, created_at, updated_at, track_order:playlist->order")
    .order("updated_at", { ascending: false });

  const role = asRole(profile?.role);

  return (
    <main className="mx-auto max-w-[1120px] px-5 py-6">
      <WorkspaceNav name={profile?.name || user.email || ""} role={role} crumb="Sets" />

      <section className="mt-12 animate-rise">
        <div className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-mint">
          Set builder
        </div>
        <h1 className="mt-1 font-display text-[clamp(1.9rem,4vw,2.8rem)] font-extrabold tracking-tight">
          Your saved sets
        </h1>
        <p className="mt-2 max-w-xl text-[color:var(--muted)]">
          Every set keeps its analysis — reorder, rebuild and export any time, no re-upload.
        </p>
      </section>

      {sets && sets.length > 0 ? (
        <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sets.map((s) => (
            <Link
              key={s.id}
              href={`/app/sets/${s.id}`}
              className="group rounded-2xl border border-line bg-surface p-6 transition-colors hover:border-mint/50"
            >
              <h3 className="flex items-center justify-between font-semibold">
                <span className="truncate">{s.name}</span>
                <span className="text-mint transition-transform group-hover:translate-x-0.5">→</span>
              </h3>
              <p className="mt-2 font-mono text-xs text-[color:var(--muted)]">
                {(s.track_order as unknown as string[] | null)?.length ?? 0} tracks
              </p>
              <p className="mt-3 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
                updated {formatDate(s.updated_at)}
              </p>
            </Link>
          ))}
        </section>
      ) : (
        <section className="mt-10 rounded-3xl border-2 border-dashed border-line bg-surface p-10 text-center">
          <p className="font-medium">No saved sets yet.</p>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            Analyze a batch of tracks and save the result — it&apos;ll live here.
          </p>
          <Link
            href="/app/analyze"
            className="mt-5 inline-block rounded-full bg-mint px-6 py-2.5 text-sm font-bold text-[#0c221d] transition-opacity hover:opacity-90"
          >
            Analyze tracks →
          </Link>
        </section>
      )}
    </main>
  );
}

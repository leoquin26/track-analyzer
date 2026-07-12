import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole, ENTITLEMENTS, ROLE_LABELS } from "@/lib/entitlements";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";

// Workspace home. Modules light up as they come online — Analyze is live and
// consumes the FastAPI with the Supabase access token.
const MODULES: [string, string, string | null][] = [
  ["Overview", "Your workspace at a glance — library metrics and where to go next.", null],
  ["Analyze", "Upload tracks and read every song's key, BPM, groove and energy.", "/app/analyze"],
  ["Set builder", "Your set in playing order — reorder, rebuild, watch the energy flow.", "/app/sets"],
  ["Inspector", "One track under the microscope — preview, compatibilities, fixes.", null],
  ["Discover", "Find new tracks similar to yours, ranked by how well they'd mix in.", null],
  ["Insights", "The big picture: keys in play and how everything pairs up.", "/app/insights"],
  ["Export", "Take the set with you — CSV, M3U, and DJ software formats with Pro.", null],
];

export default async function AppHome() {
  const supabase = await createClient();
  if (!supabase) redirect("/login");

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, role")
    .eq("id", user.id)
    .single();

  const role = asRole(profile?.role);
  const plan = ROLE_LABELS[role];
  const limits = ENTITLEMENTS[role];

  return (
    <main className="mx-auto max-w-[1120px] px-5 py-6">
      <WorkspaceNav name={profile?.name || user.email || ""} role={role} />

      <section className="mt-12 animate-rise">
        <div className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-mint">Welcome</div>
        <h1 className="mt-1 font-display text-[clamp(1.9rem,4vw,2.8rem)] font-extrabold tracking-tight">
          Your harmonic mixing workspace
        </h1>
        <p className="mt-2 max-w-xl text-[color:var(--muted)]">
          Signed in as <b className="text-ink">{profile?.name || user.email}</b> on the{" "}
          <b className="text-mint">{plan}</b> plan
          {limits.maxTracks ? ` — up to ${limits.maxTracks} tracks per analysis.` : " — unlimited tracks."}
        </p>
      </section>

      <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODULES.map(([title, desc, href]) =>
          href ? (
            <Link
              key={title}
              href={href}
              className="group rounded-2xl border border-mint/25 bg-surface p-6 transition-colors hover:border-mint/60"
            >
              <h3 className="flex items-center justify-between font-semibold">
                {title}
                <span className="text-mint transition-transform group-hover:translate-x-0.5">→</span>
              </h3>
              <p className="mt-1 text-sm text-[color:var(--muted)]">{desc}</p>
              <p className="mt-4 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-mint">
                Live — start here
              </p>
            </Link>
          ) : (
            <div key={title} className="rounded-2xl border border-line bg-surface p-6 opacity-90">
              <h3 className="font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-[color:var(--muted)]">{desc}</p>
              <p className="mt-4 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
                Coming online — next increment
              </p>
            </div>
          ),
        )}
      </section>
    </main>
  );
}

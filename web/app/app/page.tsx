import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole, ENTITLEMENTS, ROLE_LABELS } from "@/lib/entitlements";

// Workspace shell — proves the auth + role wiring end to end. The analyzer
// modules land here in the next increment, consuming the FastAPI.
const MODULES = [
  ["Overview", "Your workspace at a glance — library metrics and where to go next."],
  ["Analyze", "Upload tracks and read every song's key, BPM, groove and energy."],
  ["Set builder", "Your set in playing order — listen, reorder, watch the energy flow."],
  ["Inspector", "One track under the microscope — preview, compatibilities, fixes."],
  ["Discover", "Find new tracks similar to yours, ranked by how well they'd mix in."],
  ["Insights", "The big picture: keys in play and how everything pairs up."],
  ["Export", "Take the set with you — CSV, M3U, and DJ software formats with Pro."],
] as const;

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
      <nav className="flex items-center justify-between rounded-full border border-line bg-[rgba(24,20,30,0.72)] py-2 pl-5 pr-2 backdrop-blur-md">
        <Link href="/" className="flex items-center gap-2 font-display text-lg font-extrabold tracking-tight">
          <span className="h-3.5 w-3.5 rounded-full bg-[conic-gradient(from_0deg,#5eead4,#a78bfa,#f2a6c9,#f5d98f,#5eead4)]" />
          Keyflow
        </Link>
        <div className="flex items-center gap-3">
          <span className="hidden font-mono text-xs text-[color:var(--muted)] sm:inline">
            {profile?.name || user.email} ·{" "}
            <b className={role === "free" ? "text-ink" : "text-mint"}>{plan}</b>
          </span>
          <form action="/auth/signout" method="post">
            <button className="rounded-full border border-line bg-surface-2 px-4 py-2 text-sm font-semibold transition-colors hover:border-mint/45">
              Sign out
            </button>
          </form>
        </div>
      </nav>

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
        {MODULES.map(([title, desc]) => (
          <div key={title} className="rounded-2xl border border-line bg-surface p-6 opacity-90">
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-[color:var(--muted)]">{desc}</p>
            <p className="mt-4 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-[color:var(--faint)]">
              Coming online — next increment
            </p>
          </div>
        ))}
      </section>
    </main>
  );
}

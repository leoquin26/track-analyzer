import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole } from "@/lib/entitlements";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";
import InsightsClient from "@/components/insights/InsightsClient";

export const metadata = { title: "Insights — Keyflow" };

export default async function InsightsPage() {
  const supabase = await createClient();
  if (!supabase) redirect("/login");

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login?next=/app/insights");

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, role")
    .eq("id", user.id)
    .single();

  // RLS scopes to the signed-in user; newest first so the default pick is fresh.
  const { data: sets } = await supabase
    .from("sets")
    .select("id, name")
    .order("updated_at", { ascending: false });

  const role = asRole(profile?.role);

  return (
    <main className="mx-auto max-w-[1120px] px-5 py-6">
      <WorkspaceNav name={profile?.name || user.email || ""} role={role} crumb="Insights" />

      <section className="mt-12 animate-rise">
        <div className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-mint">
          Insights
        </div>
        <h1 className="mt-1 font-display text-[clamp(1.9rem,4vw,2.8rem)] font-extrabold tracking-tight">
          The big picture of your set
        </h1>
        <p className="mt-2 max-w-xl text-[color:var(--muted)]">
          Keys in play on the wheel, tempo against energy, and how every track pairs with
          every other — all from the saved analysis.
        </p>
      </section>

      {sets && sets.length > 0 ? (
        <InsightsClient sets={sets} />
      ) : (
        <section className="mt-10 rounded-3xl border-2 border-dashed border-line bg-surface p-10 text-center">
          <p className="font-medium">No saved sets to explore yet.</p>
          <p className="mt-1 text-sm text-[color:var(--muted)]">
            Analyze a batch, save it as a set, and its insights will land here.
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

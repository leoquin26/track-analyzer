import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole, ENTITLEMENTS } from "@/lib/entitlements";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";
import AnalyzeClient from "@/components/analyze/AnalyzeClient";

export const metadata = { title: "Analyze — Keyflow" };

export default async function AnalyzePage() {
  const supabase = await createClient();
  if (!supabase) redirect("/login");

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login?next=/app/analyze");

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, role")
    .eq("id", user.id)
    .single();

  const role = asRole(profile?.role);

  return (
    <main className="mx-auto max-w-[1120px] px-5 py-6">
      <WorkspaceNav name={profile?.name || user.email || ""} role={role} crumb="Analyze" />

      <section className="mt-12">
        <div className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-mint">
          Analyze
        </div>
        <h1 className="mt-1 font-display text-[clamp(1.9rem,4vw,2.8rem)] font-extrabold tracking-tight">
          Read every track, order the set
        </h1>
        <p className="mt-2 max-w-xl text-[color:var(--muted)]">
          Upload a batch and the engine reads each track&apos;s key, BPM, groove and energy —
          then orders them so every transition flows.
        </p>
      </section>

      <AnalyzeClient role={role} maxTracks={ENTITLEMENTS[role].maxTracks} />
    </main>
  );
}

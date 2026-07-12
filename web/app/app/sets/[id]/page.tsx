import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { asRole } from "@/lib/entitlements";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";
import SetBuilderClient from "@/components/set/SetBuilderClient";

export const metadata = { title: "Set builder — Keyflow" };

export default async function SetBuilderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const supabase = await createClient();
  if (!supabase) redirect("/login");

  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(`/login?next=/app/sets/${id}`);

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, role")
    .eq("id", user.id)
    .single();

  const role = asRole(profile?.role);

  return (
    <main className="mx-auto max-w-[1120px] px-5 py-6">
      <WorkspaceNav name={profile?.name || user.email || ""} role={role} crumb="Set builder" />
      <SetBuilderClient setId={id} role={role} />
    </main>
  );
}

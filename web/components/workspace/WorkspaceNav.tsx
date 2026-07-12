import Link from "next/link";
import type { Role } from "@/lib/entitlements";
import { ROLE_LABELS } from "@/lib/entitlements";

/** Shared pill nav for every workspace page. `crumb` names the open module. */
export default function WorkspaceNav({
  name,
  role,
  crumb,
}: {
  name: string;
  role: Role;
  crumb?: string;
}) {
  return (
    <nav className="flex items-center justify-between rounded-full border border-line bg-[rgba(24,20,30,0.72)] py-2 pl-5 pr-2 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <Link
          href="/app"
          className="flex items-center gap-2 font-display text-lg font-extrabold tracking-tight"
        >
          <span className="h-3.5 w-3.5 rounded-full bg-[conic-gradient(from_0deg,#5eead4,#a78bfa,#f2a6c9,#f5d98f,#5eead4)]" />
          Keyflow
        </Link>
        {crumb ? (
          <span className="hidden items-center gap-2 text-sm text-[color:var(--muted)] sm:flex">
            <span className="text-[color:var(--faint)]">/</span>
            {crumb}
          </span>
        ) : null}
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden font-mono text-xs text-[color:var(--muted)] sm:inline">
          {name} ·{" "}
          <b className={role === "free" ? "text-ink" : "text-mint"}>{ROLE_LABELS[role]}</b>
        </span>
        <form action="/auth/signout" method="post">
          <button className="rounded-full border border-line bg-surface-2 px-4 py-2 text-sm font-semibold transition-colors hover:border-mint/45">
            Sign out
          </button>
        </form>
      </div>
    </nav>
  );
}

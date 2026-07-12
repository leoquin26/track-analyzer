"use client";

// Small shared pieces for the auth screens — one visual voice, three pages.

export function Field({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-[color:var(--muted)]">{label}</span>
      <input
        {...props}
        className="w-full rounded-xl border border-line bg-surface-2 px-3.5 py-2.5 font-mono text-sm text-ink outline-none transition-colors placeholder:text-[color:var(--faint)] focus:border-mint/50"
      />
    </label>
  );
}

export function SubmitButton({ children, busy }: { children: React.ReactNode; busy?: boolean }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full rounded-xl bg-ink px-4 py-2.5 font-semibold text-bg transition-all hover:-translate-y-0.5 disabled:translate-y-0 disabled:opacity-60"
    >
      {busy ? "One moment…" : children}
    </button>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="rounded-xl border border-[#e66767]/30 bg-[#e66767]/10 px-3.5 py-2.5 text-sm text-[#ffb4a2]">
      {message}
    </p>
  );
}

export function FormNotice({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="rounded-xl border border-mint/30 bg-mint/10 px-3.5 py-2.5 text-sm text-mint">
      {message}
    </p>
  );
}

export function NotConfigured() {
  return (
    <div className="space-y-3 text-sm text-[color:var(--muted)]">
      <h1 className="font-display text-2xl font-bold text-ink">Almost there</h1>
      <p>
        Accounts aren&apos;t configured yet on this deployment — set{" "}
        <code className="font-mono text-mint">NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
        <code className="font-mono text-mint">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in{" "}
        <code className="font-mono">.env.local</code> (see <code className="font-mono">.env.example</code>).
      </p>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Field, FormError, NotConfigured, SubmitButton } from "@/components/auth/AuthBits";

/** Only allow same-origin relative paths as a post-login destination:
 *  "//evil.com" (protocol-relative) and "/\evil.com" (backslash-normalized)
 *  are classic open-redirect vectors. Anything suspicious falls back to /app. */
function safeNext(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//") && !raw.startsWith("/\\")) {
    return raw;
  }
  return "/app";
}

function LoginForm() {
  const supabase = createClient();
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!supabase) return <NotConfigured />;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const { error } = await supabase!.auth.signInWithPassword({
      email: String(form.get("email")),
      password: String(form.get("password")),
    });
    if (error) {
      setError(error.message);
      setBusy(false);
      return;
    }
    router.push(next);
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Sign in to your workspace</h1>
      <p className="text-sm text-[color:var(--muted)]">
        Your plan, sets and preferences live with your account.
      </p>
      <FormError message={error} />
      <Field label="Email" name="email" type="email" autoComplete="email" required />
      <Field label="Password" name="password" type="password" autoComplete="current-password" required />
      <SubmitButton busy={busy}>Sign in</SubmitButton>
      <div className="flex justify-between pt-1 text-sm text-[color:var(--muted)]">
        <Link href="/signup" className="transition-colors hover:text-mint">
          Create account
        </Link>
        <Link href="/reset" className="transition-colors hover:text-mint">
          Forgot password?
        </Link>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

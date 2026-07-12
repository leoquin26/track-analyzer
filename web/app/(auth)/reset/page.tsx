"use client";

import Link from "next/link";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Field, FormError, FormNotice, NotConfigured, SubmitButton } from "@/components/auth/AuthBits";

export default function ResetPage() {
  const supabase = createClient();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!supabase) return <NotConfigured />;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const { error } = await supabase!.auth.resetPasswordForEmail(String(form.get("email")), {
      redirectTo: `${window.location.origin}/login`,
    });
    setBusy(false);
    if (error) setError(error.message);
    else setNotice("If that email has an account, a reset link is on its way.");
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Reset your password</h1>
      <p className="text-sm text-[color:var(--muted)]">
        We&apos;ll email you a link to set a new one.
      </p>
      <FormError message={error} />
      <FormNotice message={notice} />
      <Field label="Email" name="email" type="email" autoComplete="email" required />
      <SubmitButton busy={busy}>Send reset link</SubmitButton>
      <p className="pt-1 text-sm text-[color:var(--muted)]">
        Remembered it?{" "}
        <Link href="/login" className="transition-colors hover:text-mint">
          Sign in
        </Link>
      </p>
    </form>
  );
}

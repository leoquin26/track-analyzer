"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  Field,
  FormError,
  FormNotice,
  NotConfigured,
  SubmitButton,
} from "@/components/auth/AuthBits";

export default function SignupPage() {
  const supabase = createClient();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!supabase) return <NotConfigured />;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const form = new FormData(event.currentTarget);
    const { data, error } = await supabase!.auth.signUp({
      email: String(form.get("email")),
      password: String(form.get("password")),
      options: { data: { name: String(form.get("name")) } },
    });
    if (error) {
      setError(error.message);
      setBusy(false);
      return;
    }
    // With email confirmation enabled there's no session yet — tell the user.
    if (!data.session) {
      setNotice("Check your inbox to confirm your email, then sign in.");
      setBusy(false);
      return;
    }
    router.push("/app");
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Create your free account</h1>
      <p className="text-sm text-[color:var(--muted)]">
        Free plan: 50 tracks per analysis, harmonic ordering, CSV + M3U export.
      </p>
      <FormError message={error} />
      <FormNotice message={notice} />
      <Field label="Name / DJ name" name="name" autoComplete="nickname" required />
      <Field label="Email" name="email" type="email" autoComplete="email" required />
      <Field
        label="Password (8+ characters)"
        name="password"
        type="password"
        autoComplete="new-password"
        minLength={8}
        required
      />
      <SubmitButton busy={busy}>Create free account</SubmitButton>
      <p className="pt-1 text-sm text-[color:var(--muted)]">
        Already have one?{" "}
        <Link href="/login" className="transition-colors hover:text-mint">
          Sign in
        </Link>
      </p>
    </form>
  );
}

# SaaS Fase 2 — Next.js frontend + Supabase — Design Spec

Date: 2026-07-11 · Direction confirmed: full Next.js web app, Supabase backend.

## Architecture

```
Browser ── Next.js (App Router, Tailwind, design tokens ported from Streamlit)
   │           ├─ Supabase Auth (email/pass + verify + reset + sessions, SSR)
   │           └─ calls FastAPI for analysis with the Supabase JWT
   ▼
Supabase ── Postgres (profiles/role, feature_cache, sets) + Storage (temp audio) + Auth
   ▲
FastAPI (existing engine wrapper) ── validates the Supabase JWT, reads role,
   enforces plan limits, runs analysis jobs, deletes audio after.
```

## Key decision: use **Supabase Auth**, not our authcore sessions
Supabase Auth ships email verification, password reset, secure SSR sessions and
(later) social login — the exact things we hand-rolled and the SMTP blocker.
Consequences:
- Next.js uses `@supabase/ssr` for auth; no custom login/session/reset code.
- Roles live in a `profiles` table (1:1 with `auth.users`), default `free` via a
  signup trigger, protected by RLS. `ENTITLEMENTS` stays the single source of
  limits (shared constant, mirrored in `authcore` and the web).
- **FastAPI** stops issuing its own tokens; it validates the Supabase JWT
  (verify signature with the project JWT secret) and reads `role` from `profiles`.
  The `/v1/auth/*` endpoints are retired for the web; the Streamlit app keeps its
  own authcore login for the local desktop use-case.
- **Gumroad** → a webhook (Next.js route or FastAPI) flips `profiles.role` on
  sale/refund/cancel; manual license-link stays as a fallback.

## Increments (each verifiable)
1. **Scaffold + design system + landing** — Next.js under `web/`, tokens
   (Outfit/Inter/DM Mono, warm-dark palette) as Tailwind config + CSS vars, the
   landing page ported (navbar pill, hero + Camelot wheel, stats, pricing).
   *Verifiable at localhost:3000 with zero Supabase keys.* ← start here
2. **Supabase project + schema** — SQL migration: `profiles`, `feature_cache`,
   `sets`, RLS, signup trigger. Needs the user to create the project (keys).
3. **Auth pages** — sign in / up / reset via Supabase Auth, protected app routes.
4. **Analyzer UI** — upload → call FastAPI (Supabase JWT) → poll job → render
   playlist / energy curve / wheel (Plotly.js or the SVG wheel) → exports.
5. **FastAPI adapts** — Supabase JWT validation + role from Postgres; Postgres
   feature cache.
6. **Billing** — Gumroad webhook → role; then LemonSqueezy for real subscriptions.

## Needs from the user (when we reach increment 2)
Create a Supabase project → provide `NEXT_PUBLIC_SUPABASE_URL`, anon key, service
role key, and the JWT secret. Until then, increment 1 proceeds fully.

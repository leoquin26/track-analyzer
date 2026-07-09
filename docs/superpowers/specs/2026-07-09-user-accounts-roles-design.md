# User accounts + role system (Free / Pro / Lifetime) — Design Spec

Date: 2026-07-09 · Phase: Streamlit prototype (pre-SaaS). Migrates to Supabase in SaaS Fase 2.

## Goal
Tie plans to users: registration/login, roles free/pro/lifetime, and plan
restrictions enforced across the whole analyzer flow.

## Auth (`ui/auth.py`)
- Store: SQLite at `~/.keyflow/keyflow.db`, table `users(id, email UNIQUE, name,
  pw_hash, role, license_key, license_checked_at, created_at)`.
- Passwords: `hashlib.scrypt` (n=16384, r=8, p=1) with per-user random salt,
  stored `salt_hex$hash_hex`. Constant-time compare.
- Session: `st.session_state["auth_user"]` dict. (Honest limit: a hard browser
  refresh starts a new Streamlit session → re-login. Cookie persistence lands
  with the real web stack in Fase 2.)
- Roles: `free` (default on signup), `pro`, `lifetime`.

## Upgrading roles (Gumroad)
- Account module: paste license key → verified against **two** products:
  membership (`gumroad_product_id`) → role `pro`; one-off
  (`gumroad_lifetime_product_id`) → role `lifetime`. Key + timestamp persisted.
- Pro is re-verified on login if older than 7 days; an authoritative "invalid"
  (cancelled/refunded) downgrades to free. Network failure never downgrades.

## Entitlements (single source: `auth.ENTITLEMENTS`)
| Capability | Free | Pro | Lifetime |
|---|---|---|---|
| Tracks per analysis | 50 (truncated + upgrade notice) | ∞ | ∞ |
| Harmonic ordering, CSV+M3U, live reorder | ✓ | ✓ | ✓ |
| Energy-curve selector (plateau) | ✗ (locked to build-up) | ✓ | ✓ |
| Discover (similar tracks) | ✗ | ✓ | ✓ |
| DJ exports (rekordbox/Serato/Traktor) + tag writing | ✗ | ✓ | ✓ |

## Flow
- Landing stays public. The app (`analyzer_page`) requires login: unauthenticated
  users see a sign-in / create-account panel (no sidebar).
- Sidebar gains an account block: email + role badge + Upgrade CTA (free) + Sign out.
- New **Account** module: profile, plan, license linking, upgrade links.
- `ui/premium.py.is_premium()` becomes role-based (`auth.entitled("dj_export")`).

## Out of scope
OAuth/social login, email verification, password reset, cookie sessions,
multi-device sync — all arrive with Supabase in SaaS Fase 2.

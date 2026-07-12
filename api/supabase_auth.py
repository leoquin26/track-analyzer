"""Supabase JWT verification + role lookup for the API (SaaS Fase 2, inc. 3).

The web app authenticates users with Supabase Auth and calls this API with the
session's access token as a Bearer credential. We verify it **offline**:

- Primary: asymmetric keys via the project's public JWKS
  (``{SUPABASE_URL}/auth/v1/.well-known/jwks.json``) — this is what current
  Supabase stacks sign with (verified empirically: local CLI issues ES256).
- Fallback: legacy HS256 projects, when ``SUPABASE_JWT_SECRET`` is set.

The plan (``role``) is NOT trusted from the token — it lives in
``public.profiles`` (users can't write their own role there; column-level
grants enforce it), read via PostgREST with the service key and cached briefly.

Config (env):
    SUPABASE_URL                e.g. http://127.0.0.1:54321 or https://xyz.supabase.co
    SUPABASE_SERVICE_ROLE_KEY   server-only; used to read profiles
    SUPABASE_JWT_SECRET         optional, only for legacy HS256 projects
"""

from __future__ import annotations

import logging
import os
import threading
import time

import httpx
import jwt as pyjwt
from jwt import PyJWKClient

logger = logging.getLogger("keyflow.api.supabase")

_ROLE_TTL = 60.0  # seconds; a Gumroad upgrade shows up within a minute
# uid -> (role, name, ts); role None = tombstone (account deleted)
_role_cache: dict[str, tuple[str | None, str, float]] = {}
_cache_lock = threading.Lock()

_jwks_client: PyJWKClient | None = None
_jwks_lock = threading.Lock()


def supabase_url() -> str:
    return (os.environ.get("SUPABASE_URL") or "").rstrip("/")


def configured() -> bool:
    return bool(supabase_url() and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))


def _jwks() -> PyJWKClient:
    global _jwks_client
    with _jwks_lock:
        if _jwks_client is None:
            _jwks_client = PyJWKClient(
                f"{supabase_url()}/auth/v1/.well-known/jwks.json",
                cache_keys=True,
                lifespan=3600,
            )
        return _jwks_client


def verify_token(token: str) -> dict | None:
    """Return the JWT claims when the signature and audience check out."""
    try:
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "")
        if alg.startswith("HS"):
            secret = os.environ.get("SUPABASE_JWT_SECRET", "")
            if not secret:
                logger.warning("HS256 Supabase token but SUPABASE_JWT_SECRET unset")
                return None
            key = secret
        else:
            key = _jwks().get_signing_key_from_jwt(token).key
        return pyjwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except Exception:  # noqa: BLE001 - any verification failure = anonymous
        return None


def _fetch_profile(user_id: str) -> tuple[str, str] | None:
    """(role, name) from public.profiles via PostgREST with the service key.

    ``None`` means the profile row definitively does not exist — the account
    was deleted (or never provisioned). The signup trigger guarantees every
    live user has one, so a still-valid JWT without a row must NOT keep
    working until it expires; the per-request lookup gives us near-real-time
    revocation for free.
    """
    service = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    response = httpx.get(
        f"{supabase_url()}/rest/v1/profiles",
        params={"id": f"eq.{user_id}", "select": "role,name"},
        headers={"apikey": service, "Authorization": f"Bearer {service}"},
        timeout=5.0,
    )
    response.raise_for_status()
    rows = response.json()
    if not rows:
        return None
    role = rows[0].get("role")
    return (role if role in ("free", "pro", "lifetime") else "free",
            rows[0].get("name") or "")


def user_from_token(token: str) -> dict | None:
    """Full user dict (id/email/name/role) for a Supabase access token."""
    if not configured():
        return None
    claims = verify_token(token)
    if not claims or not claims.get("sub"):
        return None
    uid = str(claims["sub"])

    now = time.time()
    with _cache_lock:
        cached = _role_cache.get(uid)
    if cached and now - cached[2] < _ROLE_TTL:
        role, name = cached[0], cached[1]
    else:
        try:
            profile = _fetch_profile(uid)  # None = account deleted
        except Exception as exc:  # noqa: BLE001 - profiles unreachable: stale > broken
            logger.warning("profiles lookup failed for %s: %s", uid, exc)
            profile = (cached[0], cached[1]) if cached else ("free", "")
        role, name = profile if profile else (None, "")
        with _cache_lock:
            _role_cache[uid] = (role, name, now)
    if role is None:  # tombstone: deleted account, valid-looking JWT
        return None

    metadata = claims.get("user_metadata") or {}
    return {
        "id": uid,
        "email": claims.get("email", ""),
        "name": name or metadata.get("name") or (claims.get("email", "").split("@")[0]),
        "role": role,
        "verified": True,  # Supabase enforces its own email confirmation policy
        "supabase": True,  # saved sets & other Supabase-backed features key off this
    }

"""Saved sets — public.sets in Supabase, via PostgREST with the service key.

The API is the only *writer* (every mutation passes through the scoring
engine); the web reads its own rows directly with the user's token for the
list view (RLS + the grants from migration 0002 make that safe).

service_role BYPASSES RLS, so every query here filters by ``user_id`` —
on this path that filter *is* the ownership boundary. Never drop it.

Stored shape:
    playlist = {"tracks": [full feature dicts, rhythm_vector as list],
                "order":  [titles in playing order]}
    params   = {"weights", "start_title", "energy_curve", "exclude_titles",
                "manual": bool}
A saved set is self-contained: it can be re-ordered and re-scored forever
without the original job (jobs are ephemeral) or the audio (never stored).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from api.supabase_auth import supabase_url

_TIMEOUT = 10.0


def _headers(extra: dict | None = None) -> dict:
    service = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return {"apikey": service, "Authorization": f"Bearer {service}",
            "Content-Type": "application/json", **(extra or {})}


def create_set(user_id: str, name: str, tracks: list[dict], order: list[str],
               params: dict) -> dict:
    response = httpx.post(
        f"{supabase_url()}/rest/v1/sets",
        json={"user_id": user_id, "name": name,
              "playlist": {"tracks": tracks, "order": order}, "params": params},
        headers=_headers({"Prefer": "return=representation"}),
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()[0]


def list_sets(user_id: str) -> list[dict]:
    """Summaries newest-first; ``order`` comes along only to count tracks."""
    response = httpx.get(
        f"{supabase_url()}/rest/v1/sets",
        params={"user_id": f"eq.{user_id}", "order": "updated_at.desc",
                "select": "id,name,created_at,updated_at,track_order:playlist->order"},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_set(user_id: str, set_id: str) -> dict | None:
    response = httpx.get(
        f"{supabase_url()}/rest/v1/sets",
        params={"id": f"eq.{set_id}", "user_id": f"eq.{user_id}", "select": "*"},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def update_set(user_id: str, set_id: str, fields: dict) -> dict | None:
    fields = {**fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    response = httpx.patch(
        f"{supabase_url()}/rest/v1/sets",
        params={"id": f"eq.{set_id}", "user_id": f"eq.{user_id}"},
        json=fields,
        headers=_headers({"Prefer": "return=representation"}),
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def delete_set(user_id: str, set_id: str) -> bool:
    response = httpx.delete(
        f"{supabase_url()}/rest/v1/sets",
        params={"id": f"eq.{set_id}", "user_id": f"eq.{user_id}"},
        headers=_headers({"Prefer": "return=representation"}),
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return bool(response.json())

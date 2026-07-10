"""Streamlit glue over the shared auth core (``authcore.py``).

The core (DB, hashing, sessions, codes, roles, entitlements) is framework-
agnostic and shared with the FastAPI backend; this module adds what only the
UI needs: the ``st.session_state`` session, entitlement lookups for the
signed-in user, Gumroad license linking, and the weekly Pro re-check on login.
"""

from __future__ import annotations

import time

import streamlit as st

import authcore
from authcore import (  # noqa: F401 - re-exported for the rest of the UI
    CODE_TTL,
    ENTITLEMENTS,
    ROLE_LABELS,
    ROLES,
    SESSION_TTL,
    consume_code,
    create_code,
    issue_session,
    register,
    restore_session,
    revoke_all_sessions,
    revoke_session,
    set_password,
)

_RECHECK_INTERVAL = 7 * 86400  # re-verify Pro subscriptions weekly

# Kept for tests/tools that want to point the store elsewhere.
DB_PATH = authcore.DB_PATH


def login(email: str, password: str) -> tuple[dict | None, str]:
    user, error = authcore.login(email, password)
    if user:
        user = _maybe_recheck_subscription(user)
    return user, error


def current_user() -> dict | None:
    return st.session_state.get("auth_user")


def sign_in_session(user: dict) -> None:
    st.session_state["auth_user"] = user


def sign_out() -> None:
    st.session_state["auth_user"] = None


def role() -> str:
    user = current_user()
    return user["role"] if user else "free"


def entitled(capability: str):
    """Value of a capability for the signed-in user's plan (bool or limit)."""
    return ENTITLEMENTS[role()].get(capability)


def set_role(user_id: int, new_role: str, license_key: str | None = None) -> None:
    authcore.set_role(user_id, new_role, license_key)
    user = st.session_state.get("auth_user")
    if user and user["id"] == user_id:
        user["role"] = new_role


def mark_verified(user_id: int) -> None:
    authcore.mark_verified(user_id)
    user = st.session_state.get("auth_user")
    if user and user["id"] == user_id:
        user["verified"] = True


# --------------------------------------------------------------------------- #
# Gumroad license linking (membership -> pro, one-off -> lifetime)
# --------------------------------------------------------------------------- #

def link_license(user: dict, key: str) -> tuple[str, str]:
    """Verify a Gumroad key against both products and upgrade the account.

    Returns (status, message): status in {"ok", "invalid", "unreachable"}.
    """
    from ui import premium, state

    lifetime_product = state.get_secret("gumroad_lifetime_product_id",
                                        "TA_GUMROAD_LIFETIME_PRODUCT_ID")
    checks = [("pro", None)]  # None -> premium's default (membership) product id
    if lifetime_product:
        checks.insert(0, ("lifetime", lifetime_product))

    saw_unreachable = False
    for target_role, product in checks:
        status, _data = premium.verify_license(key, product_id=product)
        if status == "valid":
            set_role(user["id"], target_role, license_key=key.strip())
            return "ok", f"License linked — you're on {ROLE_LABELS[target_role]} now."
        if status == "unreachable":
            saw_unreachable = True

    if saw_unreachable:
        return "unreachable", "Couldn't reach Gumroad to verify — try again in a minute."
    return "invalid", "That key isn't valid for any Keyflow product."


def _maybe_recheck_subscription(user: dict) -> dict:
    """Weekly re-check of Pro subscriptions on login. Lifetime never expires;
    an unreachable verifier never downgrades — only an authoritative invalid."""
    if user["role"] != "pro":
        return user
    license_key, checked_at = authcore.get_license_info(user["id"])
    if not license_key or time.time() - checked_at < _RECHECK_INTERVAL:
        return user

    from ui import premium

    status, _ = premium.verify_license(license_key)
    if status == "invalid":
        set_role(user["id"], "free")
        user["role"] = "free"
    elif status == "valid":
        set_role(user["id"], "pro", license_key=license_key)
    return user

"""User accounts, roles and plan entitlements.

Self-contained for the Streamlit phase: SQLite in the user's home, scrypt
password hashing, session kept in ``st.session_state``. Roles are elevated by
linking a Gumroad license (membership → pro, one-off → lifetime). The public
surface (``current_user``, ``entitled``, ``ROLE_LABELS``) is what the rest of
the UI depends on — swapping this module for Supabase later shouldn't ripple.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import sqlite3
import time
from pathlib import Path

import streamlit as st

DB_PATH = Path.home() / ".keyflow" / "keyflow.db"

ROLES = ("free", "pro", "lifetime")
ROLE_LABELS = {"free": "Free", "pro": "Pro", "lifetime": "Lifetime"}

# Single source of truth for what each plan can do.
ENTITLEMENTS = {
    "free":     {"max_tracks": 50,   "energy_curve": False, "discover": False, "dj_export": False},
    "pro":      {"max_tracks": None, "energy_curve": True,  "discover": True,  "dj_export": True},
    "lifetime": {"max_tracks": None, "energy_curve": True,  "discover": True,  "dj_export": True},
}

_RECHECK_INTERVAL = 7 * 86400  # re-verify Pro subscriptions weekly


# --------------------------------------------------------------------------- #
# Storage
# --------------------------------------------------------------------------- #

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            pw_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'free',
            license_key TEXT,
            license_checked_at REAL DEFAULT 0,
            created_at REAL NOT NULL
        )"""
    )
    # Browser sessions: only the token HASH is stored, so a leaked DB can't
    # be replayed as a login.
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at REAL NOT NULL
        )"""
    )
    # One-time codes for password reset / email verification (hashed too).
    conn.execute(
        """CREATE TABLE IF NOT EXISTS codes (
            user_id INTEGER NOT NULL,
            purpose TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            expires_at REAL NOT NULL,
            PRIMARY KEY (user_id, purpose)
        )"""
    )
    # Lightweight migration: older DBs lack the `verified` column.
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "verified" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN verified INTEGER NOT NULL DEFAULT 0")
    return conn


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
        candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                                   n=16384, r=8, p=1)
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except Exception:  # noqa: BLE001 - malformed record = no access
        return False


def _row_to_user(row: sqlite3.Row) -> dict:
    keys = row.keys()
    return {"id": row["id"], "email": row["email"], "name": row["name"],
            "role": row["role"] if row["role"] in ROLES else "free",
            "verified": bool(row["verified"]) if "verified" in keys else False}


# --------------------------------------------------------------------------- #
# Persistent browser sessions (cookie token <-> hashed DB record)
# --------------------------------------------------------------------------- #

SESSION_TTL = 30 * 86400  # 30 days
CODE_TTL = 15 * 60        # reset/verify codes live 15 minutes

import secrets as _secrets  # noqa: E402


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def issue_session(user_id: int) -> str:
    """Create a session token for the cookie; only its hash is stored."""
    token = _secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (_sha(token), user_id, time.time() + SESSION_TTL),
        )
    return token


def restore_session(token: str | None) -> dict | None:
    if not token:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id"
            " WHERE s.token_hash = ? AND s.expires_at > ?",
            (_sha(token), time.time()),
        ).fetchone()
    return _row_to_user(row) if row else None


def revoke_session(token: str | None) -> None:
    if not token:
        return
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_sha(token),))


def revoke_all_sessions(user_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


# --------------------------------------------------------------------------- #
# One-time codes: password reset + email verification
# --------------------------------------------------------------------------- #

def create_code(email: str, purpose: str) -> tuple[str | None, int | None]:
    """Mint a 6-digit code for a user. Returns (code, user_id) or (None, None)."""
    with _connect() as conn:
        row = conn.execute("SELECT id FROM users WHERE email=?",
                           (email.strip().lower(),)).fetchone()
        if not row:
            return None, None
        code = f"{_secrets.randbelow(1_000_000):06d}"
        conn.execute(
            "INSERT OR REPLACE INTO codes (user_id, purpose, code_hash, expires_at)"
            " VALUES (?,?,?,?)",
            (row["id"], purpose, _sha(code), time.time() + CODE_TTL),
        )
    return code, row["id"]


def consume_code(email: str, purpose: str, code: str) -> int | None:
    """Validate + burn a code. Returns the user id when it matches."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT c.user_id FROM codes c JOIN users u ON u.id = c.user_id"
            " WHERE u.email=? AND c.purpose=? AND c.code_hash=? AND c.expires_at > ?",
            (email.strip().lower(), purpose, _sha(code.strip()), time.time()),
        ).fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM codes WHERE user_id=? AND purpose=?",
                     (row["user_id"], purpose))
    return row["user_id"]


def set_password(user_id: int, new_password: str) -> str:
    if len(new_password) < 8:
        return "Password needs at least 8 characters."
    with _connect() as conn:
        conn.execute("UPDATE users SET pw_hash=? WHERE id=?",
                     (_hash_password(new_password), user_id))
    revoke_all_sessions(user_id)  # force re-login everywhere
    return ""


def mark_verified(user_id: int) -> None:
    with _connect() as conn:
        conn.execute("UPDATE users SET verified=1 WHERE id=?", (user_id,))
    user = st.session_state.get("auth_user")
    if user and user["id"] == user_id:
        user["verified"] = True


# --------------------------------------------------------------------------- #
# Registration / login
# --------------------------------------------------------------------------- #

def register(email: str, name: str, password: str) -> tuple[dict | None, str]:
    """Create an account. Returns (user, "") or (None, error_message)."""
    email = email.strip().lower()
    name = name.strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return None, "That doesn't look like a valid email."
    if not name:
        return None, "Tell us your (DJ) name."
    if len(password) < 8:
        return None, "Password needs at least 8 characters."

    with _connect() as conn:
        try:
            conn.execute(
                "INSERT INTO users (email, name, pw_hash, created_at) VALUES (?,?,?,?)",
                (email, name, _hash_password(password), time.time()),
            )
        except sqlite3.IntegrityError:
            return None, "There's already an account with that email — sign in instead."
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    return _row_to_user(row), ""


def login(email: str, password: str) -> tuple[dict | None, str]:
    email = email.strip().lower()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row or not _verify_password(password, row["pw_hash"]):
        return None, "Email or password doesn't match."
    user = _row_to_user(row)
    user = _maybe_recheck_subscription(user, row)
    return user, ""


def current_user() -> dict | None:
    return st.session_state.get("auth_user")


def sign_in_session(user: dict) -> None:
    st.session_state["auth_user"] = user


def sign_out() -> None:
    st.session_state["auth_user"] = None


# --------------------------------------------------------------------------- #
# Roles + entitlements
# --------------------------------------------------------------------------- #

def role() -> str:
    user = current_user()
    return user["role"] if user else "free"


def entitled(capability: str):
    """Value of a capability for the signed-in user's plan (bool or limit)."""
    return ENTITLEMENTS[role()].get(capability)


def set_role(user_id: int, new_role: str, license_key: str | None = None) -> None:
    assert new_role in ROLES
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET role=?, license_key=COALESCE(?, license_key),"
            " license_checked_at=? WHERE id=?",
            (new_role, license_key, time.time(), user_id),
        )
    user = st.session_state.get("auth_user")
    if user and user["id"] == user_id:
        user["role"] = new_role


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


def _maybe_recheck_subscription(user: dict, row: sqlite3.Row) -> dict:
    """Weekly re-check of Pro subscriptions on login. Lifetime never expires;
    an unreachable verifier never downgrades — only an authoritative invalid."""
    if user["role"] != "pro" or not row["license_key"]:
        return user
    if time.time() - (row["license_checked_at"] or 0) < _RECHECK_INTERVAL:
        return user

    from ui import premium

    status, _ = premium.verify_license(row["license_key"])
    if status == "invalid":
        set_role(user["id"], "free")
        user["role"] = "free"
    elif status == "valid":
        set_role(user["id"], "pro", license_key=row["license_key"])
    return user

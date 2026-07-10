"""Framework-agnostic auth core shared by the Streamlit UI and the FastAPI API.

SQLite storage, scrypt password hashing, opaque revocable session tokens
(hashed at rest), one-time codes, roles and plan entitlements. No Streamlit
imports here — ``ui/auth.py`` adds the session-state glue, ``api/`` uses the
same tokens as Bearer credentials, so a login from either surface works on both.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / ".keyflow" / "keyflow.db"

ROLES = ("free", "pro", "lifetime")
ROLE_LABELS = {"free": "Free", "pro": "Pro", "lifetime": "Lifetime"}

# Single source of truth for what each plan can do.
ENTITLEMENTS = {
    "free":     {"max_tracks": 50,   "energy_curve": False, "discover": False, "dj_export": False},
    "pro":      {"max_tracks": None, "energy_curve": True,  "discover": True,  "dj_export": True},
    "lifetime": {"max_tracks": None, "energy_curve": True,  "discover": True,  "dj_export": True},
}

SESSION_TTL = 30 * 86400  # 30 days
CODE_TTL = 15 * 60        # reset/verify codes live 15 minutes


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
    # Sessions: only the token HASH is stored, so a leaked DB can't be replayed.
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


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _row_to_user(row: sqlite3.Row) -> dict:
    keys = row.keys()
    return {"id": row["id"], "email": row["email"], "name": row["name"],
            "role": row["role"] if row["role"] in ROLES else "free",
            "verified": bool(row["verified"]) if "verified" in keys else False}


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
    return _row_to_user(row), ""


def get_license_info(user_id: int) -> tuple[str | None, float]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT license_key, license_checked_at FROM users WHERE id=?", (user_id,)
        ).fetchone()
    if not row:
        return None, 0.0
    return row["license_key"], row["license_checked_at"] or 0.0


# --------------------------------------------------------------------------- #
# Sessions (browser cookie AND API Bearer share these tokens)
# --------------------------------------------------------------------------- #

def issue_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (time.time(),))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (_sha(token), user_id, time.time() + SESSION_TTL),
        )
    return token


def restore_session(token: str | None) -> dict | None:
    if not token or not isinstance(token, str):
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
        code = f"{secrets.randbelow(1_000_000):06d}"
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


def set_role(user_id: int, new_role: str, license_key: str | None = None) -> None:
    assert new_role in ROLES
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET role=?, license_key=COALESCE(?, license_key),"
            " license_checked_at=? WHERE id=?",
            (new_role, license_key, time.time(), user_id),
        )

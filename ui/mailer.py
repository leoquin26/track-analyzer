"""Outbound email for password resets and email verification.

Plain SMTP via stdlib — works with any provider (Gmail app password, Resend,
Mailgun SMTP, etc.). Config from ``st.secrets`` or env:

    smtp_host / TA_SMTP_HOST        e.g. "smtp.gmail.com"
    smtp_port / TA_SMTP_PORT        default 587 (STARTTLS)
    smtp_user / TA_SMTP_USER
    smtp_password / TA_SMTP_PASSWORD
    smtp_from / TA_SMTP_FROM        defaults to smtp_user

When unconfigured, callers should degrade gracefully (``configured()``).
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ui.state import get_secret


def _config() -> dict:
    return {
        "host": get_secret("smtp_host", "TA_SMTP_HOST"),
        "port": int(get_secret("smtp_port", "TA_SMTP_PORT") or 587),
        "user": get_secret("smtp_user", "TA_SMTP_USER"),
        "password": get_secret("smtp_password", "TA_SMTP_PASSWORD"),
        "sender": get_secret("smtp_from", "TA_SMTP_FROM")
                  or get_secret("smtp_user", "TA_SMTP_USER"),
    }


def configured() -> bool:
    cfg = _config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def send(to: str, subject: str, body: str) -> str:
    """Send a plain-text email. Returns "" on success, else an error message."""
    cfg = _config()
    if not configured():
        return "Email isn't configured (set smtp_host/smtp_user/smtp_password in secrets)."

    message = EmailMessage()
    message["From"] = cfg["sender"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(message)
        return ""
    except Exception as error:  # noqa: BLE001 - surfaced to the user
        return f"Couldn't send the email: {error}"


def send_code(to: str, code: str, purpose: str) -> str:
    subjects = {
        "reset": "Your Keyflow password reset code",
        "verify": "Verify your Keyflow email",
    }
    bodies = {
        "reset": (f"Your password reset code is: {code}\n\n"
                  "It expires in 15 minutes. If you didn't ask for this, ignore this email."),
        "verify": (f"Your verification code is: {code}\n\n"
                   "Enter it in Keyflow to confirm this email address. It expires in 15 minutes."),
    }
    return send(to, subjects[purpose], bodies[purpose])

"""Premium gating via Gumroad license verification.

Checkout is a Gumroad product link; buyers receive a Gumroad-issued license key,
which the app verifies against Gumroad's HTTP API. The verified state is cached
locally so we don't hit the network every run, and is re-checked periodically —
but a network failure never revokes access (only an explicit "invalid" does).

Config (st.secrets or env):
  gumroad_product_id  / TA_GUMROAD_PRODUCT_ID   — the product's id (required)
  gumroad_product_url / TA_GUMROAD_PRODUCT_URL  — the buy link shown in the UI
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import streamlit as st

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"
LICENSE_PATH = Path.home() / ".track_analyzer" / "license.json"
_RECHECK_INTERVAL = 7 * 86400  # re-verify weekly when online


def _secret(name: str, env: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:  # noqa: BLE001 - no secrets file configured
        pass
    return os.environ.get(env, "")


def _product_id() -> str:
    return _secret("gumroad_product_id", "TA_GUMROAD_PRODUCT_ID")


def product_url() -> str:
    return _secret("gumroad_product_url", "TA_GUMROAD_PRODUCT_URL")


def verify_license(key: str | None, product_id: str | None = None) -> tuple[str, dict | None]:
    """Verify a Gumroad license key against a product (default: the membership).

    Returns ("valid", data) | ("invalid", None) | ("unreachable", None).
    "unreachable" (network/config problem) must never revoke a cached license.
    """
    if not key:
        return ("invalid", None)
    product = product_id or _product_id()
    if not product:
        return ("unreachable", None)  # misconfigured, not the buyer's fault

    body = urllib.parse.urlencode({
        "product_id": product,
        "license_key": key.strip(),
        "increment_uses_count": "false",
    }).encode()

    try:
        request = urllib.request.Request(GUMROAD_VERIFY_URL, data=body)
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return ("invalid", None) if error.code in (400, 404) else ("unreachable", None)
    except Exception:  # noqa: BLE001 - network down, DNS, timeout, bad JSON
        return ("unreachable", None)

    if not payload.get("success"):
        return ("invalid", None)

    purchase = payload.get("purchase", {})
    if any(purchase.get(flag) for flag in
           ("refunded", "chargebacked", "disputed", "subscription_cancelled_at",
            "subscription_failed_at")):
        return ("invalid", None)

    name = purchase.get("email") or purchase.get("full_name") or "licensed"
    return ("valid", {"name": name, "key": key.strip()})


def load_record() -> dict | None:
    try:
        return json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_record(record: dict) -> None:
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_PATH.write_text(json.dumps(record), encoding="utf-8")


def is_premium() -> bool:
    """Plan-based: DJ exports belong to Pro and Lifetime accounts."""
    from ui import auth

    return bool(auth.entitled("dj_export"))


def render_unlock() -> None:
    url = product_url()
    if url:
        st.link_button("Buy Premium on Gumroad", url, width="stretch")
    else:
        st.caption("Set `gumroad_product_url` + `gumroad_product_id` in secrets to enable checkout.")

    key = st.text_input("License key", key="license_input",
                        placeholder="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX")
    if st.button("Unlock Premium", type="primary", width="stretch"):
        status, data = verify_license(key)
        if status == "valid":
            save_record({"key": data["key"], "name": data["name"], "verified_at": time.time()})
            st.session_state.pop("_premium", None)  # force re-check
            st.toast("Premium unlocked — thank you!", icon="🎉")
            st.rerun()
        elif status == "unreachable":
            st.warning("Couldn’t reach Gumroad to verify — check your connection and try again.")
        else:
            st.error("That license key isn’t valid for this product.")


def render_premium_export_section(frames: dict, tracks: list[dict]) -> None:
    st.markdown(
        '<div class="section-title">DJ exports <span class="prem-badge">PREMIUM</span></div>',
        unsafe_allow_html=True,
    )

    if not is_premium():
        from ui import state

        with st.container(border=True):
            st.markdown(
                "**Pro feature** — export straight to **rekordbox**, **Serato**, and "
                "**Traktor**, and write detected **key + BPM into your files' tags** so "
                "your DJ software reads them."
            )
            url = product_url()
            if url:
                st.link_button("Upgrade to Pro", url, type="primary", width="stretch")
            st.button("Already bought? Link your license in Account →", width="stretch",
                      key="prem_to_account", on_click=state.goto_module, args=("Account",))
        return

    import dj_export as dx

    playlist_df = frames["playlist_df"]
    name = st.session_state.get("_premium_name")
    if name:
        st.caption(f"Premium active — licensed to {name}. Thank you!")

    rb, serato, traktor = st.columns(3)
    with rb:
        st.download_button("rekordbox XML", dx.rekordbox_xml(playlist_df),
                           file_name="rekordbox.xml", mime="application/xml", width="stretch")
    with serato:
        st.download_button("Serato crate", dx.serato_crate(playlist_df),
                           file_name=f"{dx.PLAYLIST_NAME}.crate",
                           mime="application/octet-stream", width="stretch")
    with traktor:
        st.download_button("Traktor NML", dx.traktor_nml(playlist_df),
                           file_name="traktor.nml", mime="application/xml", width="stretch")

    st.markdown('<p class="section-hint">Write key + BPM into the audio files themselves:</p>',
                unsafe_allow_html=True)
    if st.button("Write key + BPM to file tags", width="stretch"):
        results = dx.write_tags(tracks)
        with st.expander("Tag write results", expanded=True):
            for line in results:
                st.write(line)

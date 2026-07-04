# Premium Tier + DJ Export — Design Spec

Date: 2026-07-01

## Goal

Add a Premium tier gating a DJ-export feature set: rekordbox XML, Serato crate,
Traktor NML, and key/BPM tag write-back. Free tier keeps CSV/M3U.

## Licensing (Gumroad — Stripe needs a US account)

- Checkout via a **Gumroad product link** (`gumroad_product_url`). Gumroad issues a
  license key per sale.
- Unlock: the buyer pastes their Gumroad key; the app POSTs `{product_id, license_key}`
  to `https://api.gumroad.com/v2/licenses/verify`. Result → `valid` / `invalid` /
  `unreachable`. Refunded / chargebacked / cancelled purchases count as `invalid`.
- The verified grant is cached in `~/.track_analyzer/license.json` and re-checked weekly
  when online. A network failure (`unreachable`) never revokes access — only an
  authoritative `invalid` does.
- Config from `st.secrets` (`gumroad_product_id`, `gumroad_product_url`) or env
  (`TA_GUMROAD_PRODUCT_ID`, `TA_GUMROAD_PRODUCT_URL`). No secret keys in the app.

## Modules

- `dj_export.py` — pure builders, engine-side (no Streamlit):
  - `rekordbox_xml(playlist_df) -> str`
  - `serato_crate(playlist_df) -> bytes`
  - `traktor_nml(playlist_df) -> str`
  - `write_tags(tracks) -> list[str]` (mutagen; returns per-file status). Only writes
    files that exist and are a supported type; failures are collected, never fatal.
- `ui/premium.py` — `is_premium()`, `verify_license(key)`, `save_license`/`load_license`,
  `render_unlock(...)` (Buy button + key entry), and `gated_download(...)` /
  `render_locked(...)` helpers used by the analyzer.

## Analyzer wiring

In the Exports section: free CSV/M3U stay as-is; a new **Premium exports** block shows the
four DJ exports. If not premium, buttons are replaced by a lock + "Upgrade" prompt that opens
the unlock UI (Payment Link + key entry). If premium, buttons produce the files.

## New dependencies

`mutagen` (tag writing), `cryptography` (Ed25519 license verification).

## Out of scope / needs user

Live go-live needs the user's Stripe Payment Link URL and running `issue_license.py` with
their private key. Webhook-based auto-unlock (needs hosting) is a later option.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Keyflow** (rebranded from Track Analyzer; domain `keyflow.dj`, tagline "Sets that flow in key.") — a DJ playlist builder. `APP_TITLE`/`TAGLINE`/`DOMAIN` live in `ui/styles.py`; the license cache stays at `~/.track_analyzer/` for backward compatibility. It analyzes a folder of audio files for BPM, musical key (Camelot code), rhythm fingerprint, onset density, and energy, then greedily orders the tracks to maximize transition compatibility. Exports CSV + M3U.

**Today** it runs fully local: no database, server, or persistent state — every run reads audio files and writes flat files. **This is changing** — the project is being rebuilt into a web SaaS with a backend API, accounts, and persistence (see the direction section below). When you touch architecture, assume the local-only model is transitional, not the target.

## Current status & direction — READ FIRST

The project is evolving from a local app into a **subscription SaaS** (web-first,
then a native Windows/Mac app via Tauri). Before starting work, read
**`docs/planning/PROJECT_STATUS.md`** for the current state and next steps. Deeper
plans live in `docs/planning/track-analyzer-roadmap-saas.md` (business +
architecture) and `docs/planning/track-analyzer-ui-plan.md` (UI redesign).

**Resync command:** when the user types **`/estado`** (defined in
`.claude/commands/estado.md`), re-read `docs/planning/PROJECT_STATUS.md` and the
two planning docs above, then summarize the current state and the concrete next
step before changing any code. Treat `/estado` as "catch up on the plan".

Key facts for orientation:
- Product direction: **100% web SaaS first** (analysis server-side via FastAPI wrapping `run_analysis()`; later browser/WASM feature extraction), then native via Tauri reusing the web frontend. Monetization = subscription + credits.
- The engine files (`harmonic_playlist.py`, `dj_export.py`, `track_suggest.py`) import **no Streamlit** — keep it that way so they port straight to a web backend.
- UI has been redesigned **premium/minimal** (`ui/styles.py` tokens, rebuilt `ui/pages/home.py` with SaaS sections incl. pricing). Restart Streamlit fully after `ui/` edits.
- Recurring billing is nearly wired: `ui/premium.py` already handles Gumroad subscription fields — converting the Gumroad product to a *membership* enables it.

## Commands

```bash
# Install
pip install -r requirements.txt

# Dashboard (primary UI) — opens at http://localhost:8501
python -m streamlit run dashboard.py
# On Windows, run_dashboard.bat does the same thing.

# CLI
python harmonic_playlist.py "<music folder>"
python harmonic_playlist.py "<folder>" -r          # scan subfolders
python harmonic_playlist.py "<folder>" -d 0        # analyze full track (0 = no cap)
python harmonic_playlist.py "<folder>" -o "<out>"  # output dir (defaults to music folder)

# Smoke test (no music library needed): generates 3 synthetic WAVs, then analyzes them
python generate_test_tracks.py
python harmonic_playlist.py test_tracks -o test_output -d 30
```

There is no test suite, linter config, or build step. `generate_test_tracks.py` is the only test harness — it produces synthetic tracks whose known BPM/key are encoded in the filenames (e.g. `track_a_124_am.wav`), so you can eyeball whether analysis output is roughly correct.

## Architecture

The engine is one file; the dashboard is a thin orchestrator over a `ui/` package that imports the engine.

**`harmonic_playlist.py` — the engine (import it, don't reimplement).** The dashboard imports scoring/playlist functions and `find_audio_files` from here. Key flow:
- `analyze_track()` → per-file feature dict via librosa. Returns BPM, key, `camelot`, `energy` (dB), `onset_rate`, and a normalized `rhythm_vector` (mean of the tempogram). Note the `rhythm_vector` is a numpy array and is **stripped out** before building the analysis DataFrame — it only exists in the in-memory track dicts, not in any exported file.
- `estimate_key()` uses Krumhansl-Schmugler major/minor profiles correlated against the mean CQT chroma. Key detection is approximate and known to be wrong sometimes; don't treat it as ground truth.
- `transition_score_breakdown(current, candidate, weights=None)` is the scoring core. Total = harmonic (Camelot) + BPM proximity + rhythm cosine similarity + onset-density match + energy proximity, each multiplied by an entry in `weights` (defaults to `DEFAULT_WEIGHTS`, all 1.0 → original behavior). The dashboard exposes these as live sliders. If you change the weighting model, this single function is the place — everything else consumes its output.
- `build_playlist(tracks, weights=, start_title=, energy_curve=, exclude_titles=)` — all params optional/backward-compatible. `energy_curve` is `"build_up"` (open lowest-energy, bias next track upward) or `"plateau"` (open nearest mean energy).
- `camelot_harmonic_score()` encodes the Camelot wheel rules: same code = 40, relative major/minor (same number, different letter) = 32, adjacent number same letter = 35, else −20.
- `build_playlist()` is a **greedy nearest-neighbor**: start from the lowest-energy track, repeatedly append the highest-scoring next track. Not globally optimal by design.
- `run_analysis()` is the single orchestration entry point. It returns an `AnalysisResult` dataclass holding three DataFrames (`analysis_df`, `playlist_df`, `matrix_df`) plus `m3u_content`; `save_files=True` also writes them to disk. The dashboard passes `save_files=True` and a `progress_callback`. It returns `None` when no audio files are found OR when files were found but none could be analyzed — callers must distinguish these two cases themselves (the dashboard re-scans with `find_audio_files` to tell them apart).

**`dashboard.py` + `ui/` package — Streamlit UI.** Owns no analysis logic. `dashboard.py` is the multipage **router**: `set_page_config` → `state.init_session_state()` → inject `CUSTOM_CSS` → `st.navigation([Home, Analyzer], position="hidden").run()`. The sidebar nav is **hidden**; navigation is via in-page buttons, so both `st.Page` objects are stashed in `st.session_state["_home_page"]`/`["_analyzer_page"]` for `st.switch_page()`. Page bodies live in `ui/pages/`:
- `home.py` = the **landing page** (no sidebar). It injects its own `HOME_CSS` (which hides the sidebar/header) and renders a navbar, a hero whose signature is a generated **SVG Camelot wheel** (`_camelot_wheel_svg`), capability cards, a 3-step sequence, and a footer — each with a Launch button into the analyzer.
- `analyzer.py` = a **dashboard shell**, no sidebar. Navigation is a **restyled native sidebar rail** (`components.render_sidebar_nav`: brand, module buttons keyed `nv_<slug>` with the active item highlighted via per-run CSS injection, a library-status card, and Home). `an_module` is a **plain session var** (not a widget key), so `state.goto_module` works from any `on_click`: `MODULES` = **Overview / Analyze / Set builder / Inspector / Discover / Insights / Data / Export**, each with a `MODULE_DESCRIPTIONS` line under the nav. **Overview** is the default landing: with no analysis it's a guided welcome (steps + locked module cards); with one it shows metric cards + "What next?" action cards. **Analyze** hosts the setup panel with **two sources** — local folder or file **uploads** (`_stash_uploads` → per-session temp dir → same folder path; uploads take priority) — and success CTAs into Set builder/Overview. The remaining modules **gate on `st.session_state.tracks`** (`_render_locked` shows a CTA to Analyze). Module navigation from buttons goes through `state.goto_module` as an `on_click` callback (writing `an_module` mid-script raises). Cloud-deployable: Tkinter imported lazily, Browse hidden when unavailable (`folder_picker_available`), `packages.txt` provides ffmpeg/libsndfile. Global chrome on data modules: app header (`components.render_app_header`), the "Set controls" bar, and status chips with the Guide popover. The Inspector module (`render_track_inspector`) previews a track, shows its top-3 compatible next tracks, and offers inline key/BPM correction via `state.override_track` (recomputes Camelot, `invalidate_order()` re-scores). **No emoji in UI chrome** — icons are inline hairline SVGs (see `home._SVG`); keep it that way.

**`track_suggest.py` — external track suggestions (Discover module).** Engine-side, no Streamlit. `find_similar(reference, lastfm_key=, getsongbpm_key=)` → Last.fm `track.getSimilar` when a key is configured, else the **keyless ListenBrainz path**: labs `recording-search` (returns the *canonical* recording MBID — plain MusicBrainz search MBIDs mostly have no similarity data) → labs `similar-recordings` (algorithm name must come from the API's published enum; a 400 response lists valid values). Optional GetSongBPM enrichment adds key/BPM to suggestions so `suggestion_compatibility()` can score them against the seed (harmonic+BPM only, max 65). `parse_artist_title()` reads mutagen tags then falls back to `Artist - Title` filename splits. All network calls degrade to empty results, never exceptions. Keys via `st.secrets` `lastfm_api_key`/`getsongbpm_api_key` or env `TA_LASTFM_API_KEY`/`TA_GETSONGBPM_KEY`; suggestions are cached a day per track (`state.fetch_suggestions`). `.streamlit/config.toml` (committed, unlike `secrets.toml`) themes native widgets teal.

The shared pieces live in `ui/`:
- `ui/state.py` — the interactivity core. `@st.cache_data`-wrapped analysis keyed on `(path, mtime, duration)`, the full track dicts (with `rhythm_vector`) persisted in `st.session_state`, and `ensure_order()` which re-derives the playlist from cached features whenever a control changes. **Live controls never re-read audio** — this is the whole point; keep it that way.
- `ui/charts.py` — Plotly builders (transition bars, heatmap, BPM/energy scatter, Camelot wheel, energy curve).
- `ui/components.py` — playlist editor (cards + `st.audio` + ▲▼ reorder), the setup panel (`render_setup_panel`), the results control bar (`render_control_bar`), the track inspector (`render_track_inspector`), Tkinter folder picker (`pick_folder`), and `KEY_OPTIONS` for the override selector. All main-area (no sidebar).
- `ui/styles.py` — the `CUSTOM_CSS` block (app theme, injected globally), the landing `HOME_CSS` block (navbar/hero/wheel/sections + sidebar-hide, injected only by `home.py`), and `ACCENT`/`SURFACE`/`COMPONENT_COLORS` theme constants.

**Accounts + roles (`ui/auth.py`).** Self-contained for the Streamlit phase: SQLite at `~/.keyflow/keyflow.db`, scrypt-hashed passwords, session in `st.session_state["auth_user"]` (a hard refresh = new session → re-login; cookies arrive with the SaaS stack). Roles `free/pro/lifetime`; **`auth.ENTITLEMENTS` is the single source of plan limits** (free: 50 tracks/analysis, no plateau curve, no Discover, no DJ exports). The analyzer gates on login (`_render_auth_gate`); enforcement points: `run_analysis_flow` (track cap via `analyze_folder(limit=)`), `render_control_bar` (plateau), `_module_discover` and `premium.is_premium()` (now role-based). Upgrades: the **Account** module links a Gumroad key via `auth.link_license` — checked against the membership product (→ pro) and `gumroad_lifetime_product_id` (→ lifetime); Pro is re-verified weekly on login and only an authoritative `invalid` downgrades.

**Premium tier + DJ export.** `dj_export.py` (engine-side, no Streamlit) builds **rekordbox XML / Serato crate / Traktor NML** from `playlist_df` and writes **key+BPM into file tags** via `mutagen` (`write_tags`). `ui/premium.py` gates it via **Gumroad** (Stripe needs a US account): `verify_license()` POSTs the pasted key + `gumroad_product_id` to Gumroad's `/v2/licenses/verify` API, returning `valid`/`invalid`/`unreachable` (refunded/chargebacked/cancelled count as invalid). The verified grant is cached in `~/.track_analyzer/license.json` and re-checked weekly — a network failure (`unreachable`) never revokes access, only an authoritative `invalid` does. Checkout is the Gumroad product link (`gumroad_product_url`). Config comes from `st.secrets` (never commit `.streamlit/secrets.toml`) or `TA_GUMROAD_PRODUCT_ID`/`TA_GUMROAD_PRODUCT_URL` env. `render_premium_export_section` shows the locked upgrade UI or the export buttons based on `is_premium()`.

Gotchas: **widgets inside `st.popover` are not a safe state store** — with the popover closed, a rerun triggered by any other widget can drop their state in a real browser (AppTest does NOT reproduce this), so a slider with no `value=` silently resets to `min_value`. That's why the scoring weights live in the plain `st.session_state.weights` dict and the sliders are fed `value=` from it each run; also, writing to widget keys outside an `on_click` callback raises `StreamlitAPIException` (see `state.reset_weights`). Score columns in `playlist_df` use NaN (not `""`) for the first row so `st.dataframe` can serialize to Arrow. Use `width="stretch"` on widgets, not the deprecated `use_container_width`. You can drive the UI headlessly with `streamlit.testing.v1.AppTest` — but note `AppTest` does **not** persist `st.navigation`'s selected page across a bare `at.run()` (it reverts to the default Home page), so to test the Analyzer page either chain interactions off the CTA click without an intervening `at.run()`, or point `AppTest` at a tiny wrapper that calls `analyzer_page()` directly. After editing engine/`ui` code, fully restart Streamlit — it caches imported submodules in-process, and a stale worker throws confusing `ImportError`s.

## Conventions that matter

- The per-track dict schema (keys like `camelot`, `onset_rate`, `rhythm_vector`, `key_strength`) is the informal contract between analysis, scoring, playlist building, and the dashboard. Adding or renaming a field ripples through `build_playlist_dataframe`, `build_transition_matrix`, and the dashboard's chart column references — grep for the key name before changing it.
- Duration convention: `duration=None` means full track; the CLI maps `-d 0` → `None`. The dashboard's "Analysis length" selectbox maps to `180 / 300 / None`.
- `AUDIO_EXTENSIONS` in `harmonic_playlist.py` is the single source of truth for supported formats.
- librosa's first run is slow to import/initialize; don't mistake startup latency for an analysis hang.

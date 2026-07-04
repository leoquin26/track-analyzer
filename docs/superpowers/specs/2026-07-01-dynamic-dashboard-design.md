# Dynamic Dashboard Redesign — Design Spec

Date: 2026-07-01

## Goal

Turn the one-shot "analyze → view" Streamlit dashboard into an interactive tool:
live scoring controls, manual playlist editing, per-track audio preview, and richer
visualizations — plus a robustness pass. Analysis of audio stays a one-time cost;
everything interactive re-scores in memory.

## Core enabler: cache + persist, re-score in memory

- Cache audio feature extraction with `@st.cache_data` keyed on `(file path, mtime, duration)`.
  Re-analysis only happens when a file or the duration setting changes.
- Persist the **full track dicts** (including the numpy `rhythm_vector`, normally stripped
  before export) in `st.session_state["tracks"]`, so re-ordering/re-scoring is in-memory.
- Manual order is stored as `st.session_state["order"]` (list of titles); up/down edits mutate it.

## Engine changes (`harmonic_playlist.py`) — backward compatible

- Add `DEFAULT_WEIGHTS = {"harmonic":1.0,"bpm":1.0,"rhythm":1.0,"onset":1.0,"energy":1.0}`.
- `transition_score_breakdown(current, candidate, weights=None)` — each component multiplied
  by its weight (default 1.0 → identical to today). `transition_score(...)` forwards `weights`.
- `build_playlist(tracks, weights=None, start_title=None, energy_curve="build_up", exclude_titles=None)`:
  - `build_up` → start at lowest-energy track (current behavior), tiebreak next-track toward higher energy.
  - `plateau` → start at the track whose energy is closest to the mean.
  - `start_title` overrides start selection; `exclude_titles` drops tracks before ordering.
- `build_playlist_dataframe(playlist, weights=None)` and `build_transition_matrix(tracks, weights=None)`
  accept weights for breakdown display.
- CLI path unchanged (all new params optional).

## UI capabilities

1. **Live scoring controls** — sidebar sliders (0.0–2.0, default 1.0) per weight; changing one
   instantly re-orders from cached features. Reset-to-defaults button.
2. **Manual editing** — pick/lock start track, exclude tracks (multiselect), energy-curve radio
   (build-up / plateau), "Regenerate order" button, and up/down reorder buttons per row.
3. **Per-track audio preview** — `st.audio` on each playlist card; searchable/sortable track table.
4. **Camelot wheel + richer viz** — Plotly polar wheel highlighting the set's keys and compatible
   neighbors; energy-curve line across the set order; existing transition breakdown + heatmap kept.

## Robustness

- Explicit empty / analyzing / error states; per-file failures surfaced, never fatal.
- Edge cases: single-track library, all-excluded, NaN scores, missing Camelot, non-existent folder.
- Extend the existing CSS theme, don't rewrite it.

## Structure

Split `dashboard.py` into a small package; `dashboard.py` becomes a thin orchestrator:

- `ui/styles.py` — the `CUSTOM_CSS` block.
- `ui/state.py` — session init, cached analysis, in-memory re-scoring helpers.
- `ui/charts.py` — Plotly builders (transition bars, heatmap, BPM/energy scatter, camelot wheel, energy curve).
- `ui/components.py` — metric cards, playlist cards (with audio), sidebar controls.

## Out of scope (YAGNI)

No database, no auth, no cloud, no drag-and-drop JS (Streamlit up/down buttons instead).
Engine accuracy work (separate spec) is not part of this change.

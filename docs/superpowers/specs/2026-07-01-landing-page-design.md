# Landing Page + Multipage Design Spec

Date: 2026-07-01

## Goal

Add a dedicated landing (Home) page with an "animated aurora mesh" hero, and split the
app into a Streamlit multipage structure. The analyzer keeps its current behavior.

## Structure

Streamlit multipage via `st.navigation` (available in the pinned streamlit >= 1.58).

- `dashboard.py` — stays the entry point (so `run_dashboard.bat` keeps working). Becomes a
  thin router: `set_page_config` → `state.init_session_state()` → inject CSS →
  `st.navigation([Home, Analyzer]).run()`. The `Analyzer` page object is stashed in
  `st.session_state["_analyzer_page"]` so the Home CTA can `st.switch_page()` into it.
- `ui/pages/home.py` — `home_page()`: aurora hero (HTML) + feature-highlight cards +
  "how it works" strip + a centered primary **Launch Analyzer** button that switches pages.
- `ui/pages/analyzer.py` — `analyzer_page()`: the current dashboard body moved verbatim
  (no behavior change). CSS injection and `set_page_config` move up to the router.

## Aurora hero (pure CSS)

- Full-bleed gradient-mesh container with 3 drifting neon blobs (teal `#00f5d4`,
  purple `#9b5de5`, pink `#f15bb5`) animated via `@keyframes` (transform + opacity), blurred.
- Glassmorphic headline: oversized gradient wordmark + tagline + eyebrow label.
- `prefers-reduced-motion: reduce` freezes the animation.
- `clamp()` type + max-width so it reads well on wide screens.
- New `HERO_CSS` block in `ui/styles.py`, reusing existing theme constants; no new deps.

## Navigation UX

Sidebar nav (default Streamlit) allows switching Home/Analyzer anytime; the hero CTA is the
primary entry into the tool.

## Verification

Headless `AppTest` drive of both pages + the CTA `switch_page`, plus a live server health check.

## Out of scope

The four feature tracks (persistent library, smarter set building, DJ-software export,
engine accuracy upgrade) are separate builds.

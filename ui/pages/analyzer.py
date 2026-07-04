"""Analyzer page — guided setup → analyzing → results, no sidebar.

Controls live in a top control bar (state 3) instead of the sidebar; the page
walks through three states so it never looks blank or stuck.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ui import charts, components, premium, state
from ui.styles import ANALYZER_CSS


def run_analysis_flow(config: dict) -> None:
    folder = config["folder"]
    if not folder or not folder.is_dir():
        st.session_state.last_error = "Please select a valid music folder."
        st.session_state.tracks = None
        return

    st.session_state.last_error = ""
    progress = st.progress(0.0, text="Starting analysis…")
    status = st.empty()

    def on_progress(name: str, index: int, total: int) -> None:
        progress.progress(index / total, text=f"Analyzing {index}/{total}: {name}")
        status.caption(f"Current track: **{name}**")

    with st.spinner("Analyzing tracks…"):
        tracks, failed, total = state.analyze_folder(
            folder, config["duration"], config["recursive"], on_progress
        )

    progress.empty()
    status.empty()

    if total == 0:
        st.session_state.last_error = "No audio files found in that folder."
        st.session_state.tracks = None
    elif not tracks:
        st.session_state.last_error = "Tracks were found, but none could be analyzed."
        st.session_state.tracks = None
    else:
        state.store_analysis(tracks, failed, total)


def _divider() -> None:
    st.markdown('<hr class="an-divider">', unsafe_allow_html=True)


def render_header() -> None:
    components.render_app_header("Analyzer")


def render_status_chips(frames: dict, ordered: list[dict]) -> None:
    analysis_df = frames["analysis_df"]
    playlist_df = frames["playlist_df"]
    avg_bpm = analysis_df["bpm"].mean() if not analysis_df.empty else float("nan")
    avg_score = pd.to_numeric(
        playlist_df["transition_score_from_previous"], errors="coerce"
    ).mean()
    keys = analysis_df["camelot"].nunique() if not analysis_df.empty else 0

    chips = [
        f"<span class='chip' title='Tracks successfully analyzed from your folder.'>"
        f"<b>{len(st.session_state.tracks or [])}</b> tracks</span>"
    ]
    if pd.notna(avg_bpm):
        chips.append(
            f"<span class='chip' title='Average tempo across the library, in beats per minute.'>"
            f"avg <b>{avg_bpm:.0f}</b> BPM</span>"
        )
    if pd.notna(avg_score):
        chips.append(
            f"<span class='chip' title='Average transition smoothness across the set, out of ~115. "
            f"75+ seamless · 40–75 workable · below 40 tricky.'>avg transition <b>{avg_score:.0f}</b></span>"
        )
    chips.append(
        f"<span class='chip' title='Tracks currently in the set (excluded tracks don’t count).'>"
        f"<b>{len(ordered)}</b> in set</span>"
    )
    chips.append(
        f"<span class='chip' title='Distinct Camelot keys in the set — fewer keys usually means easier mixing.'>"
        f"<b>{keys}</b> keys</span>"
    )
    chips_col, guide_col = st.columns([5.2, 0.9], vertical_alignment="center")
    with chips_col:
        st.markdown(f"<div class='chip-row'>{''.join(chips)}</div>", unsafe_allow_html=True)
    with guide_col:
        components.render_metrics_guide()


def render_downloads(frames: dict) -> None:
    st.markdown('<div class="section-title">Exports</div>', unsafe_allow_html=True)
    output_dir = Path(st.session_state.output_folder or "output")
    files = {
        "track_analysis.csv": frames["analysis_df"].to_csv(index=False),
        "playlist_order.csv": frames["playlist_df"].to_csv(index=False),
        "transition_matrix.csv": frames["matrix_df"].to_csv(),
        "playlist.m3u": frames["m3u_content"],
    }
    cols = st.columns(5)
    for col, (filename, content) in zip(cols, files.items()):
        with col:
            st.download_button(
                label=f"Download {filename}",
                data=content,
                file_name=filename,
                mime="text/csv" if filename.endswith(".csv") else "audio/x-mpegurl",
                width="stretch",
            )
    with cols[4]:
        if st.button("Save all to output folder", width="stretch"):
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                for filename, content in files.items():
                    (output_dir / filename).write_text(content, encoding="utf-8")
                st.success(f"Saved to {output_dir}")
            except Exception as error:  # noqa: BLE001
                st.error(f"Could not save: {error}")


MODULES = ["🎼 Set builder", "🔬 Inspector", "🌐 Discover", "📊 Insights", "📋 Data", "📦 Export"]

MODULE_DESCRIPTIONS = {
    "🎼 Set builder": "Your set in playing order — listen, reorder, and watch the energy flow.",
    "🔬 Inspector": "One track under the microscope: preview it, see what it mixes into, fix its key or BPM.",
    "🌐 Discover": "Find new tracks similar to the ones in your set, ranked by how well they'd mix in.",
    "📊 Insights": "The big picture: which keys you're playing in and how everything pairs up.",
    "📋 Data": "Every number behind the set, filterable and sortable.",
    "📦 Export": "Take the set with you — files for any player, DJ software formats with Premium.",
}


def _module_set_builder(frames: dict) -> None:
    playlist_df = frames["playlist_df"]
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown('<div class="section-title">Playlist order</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Use ▲ ▼ to reorder by hand.</p>', unsafe_allow_html=True)
        components.render_playlist_editor(playlist_df, show_audio=True)
    with right:
        st.markdown('<div class="section-title">Energy curve</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_energy_curve(playlist_df), width="stretch")
        st.markdown('<div class="section-title">Transition breakdown</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_transition_scores(playlist_df), width="stretch")


def _module_inspector(frames: dict) -> None:
    st.markdown('<div class="section-title">Track inspector</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Preview a track, see what it mixes into, or fix its key/BPM.</p>',
                unsafe_allow_html=True)
    components.render_track_inspector(frames["matrix_df"])


def _module_discover(frames: dict) -> None:
    tracks = st.session_state.tracks or []
    titles = [track["title"] for track in tracks]

    seed_col, btn_col = st.columns([3, 1], vertical_alignment="bottom")
    with seed_col:
        seed = st.selectbox("Find tracks similar to", titles, key="discover_seed")
    with btn_col:
        search = st.button("🌐 Find similar", type="primary", width="stretch")

    reference = next((t for t in tracks if t["title"] == seed), None)

    if search and reference:
        with st.spinner("Asking the music graph…"):
            suggestions, note = state.fetch_suggestions(reference)
        st.session_state["discover_results"] = {"seed": seed, "suggestions": suggestions, "note": note}

    results = st.session_state.get("discover_results")
    if results and results["seed"] == seed:
        components.render_suggestion_cards(results["suggestions"], results["note"])
    elif not search:
        st.markdown(
            '<p class="section-hint">Suggestions come from what real listeners play together '
            '(Last.fm / ListenBrainz), then get scored for key &amp; BPM fit against your seed track.</p>',
            unsafe_allow_html=True,
        )

    if not state.get_secret("lastfm_api_key", "TA_LASTFM_API_KEY"):
        st.caption("💡 Add a free `lastfm_api_key` in secrets for richer matches — "
                   "currently using open ListenBrainz data.")
    if not state.get_secret("getsongbpm_api_key", "TA_GETSONGBPM_KEY"):
        st.caption("💡 Add a `getsongbpm_api_key` to see key + BPM compatibility for suggestions.")


def _module_insights(frames: dict) -> None:
    playlist_df = frames["playlist_df"]
    wheel_col, scatter_col = st.columns(2, gap="large")
    with wheel_col:
        st.markdown('<div class="section-title">Camelot wheel</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Lit keys are in your set.</p>', unsafe_allow_html=True)
        present = {c for c in playlist_df["camelot"] if c}
        st.markdown(
            f'<div class="an-wheel">{charts.camelot_wheel_svg(present)}</div>',
            unsafe_allow_html=True,
        )
    with scatter_col:
        st.markdown('<div class="section-title">BPM vs energy map</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_bpm_energy_scatter(frames["analysis_df"]), width="stretch")

    st.markdown('<div class="section-title">Transition compatibility heatmap</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Every pairing at a glance — brighter cells mix more smoothly.</p>',
                unsafe_allow_html=True)
    st.plotly_chart(charts.plot_transition_heatmap(frames["matrix_df"]), width="stretch")


def _module_data(frames: dict) -> None:
    tab_analysis, tab_playlist, tab_matrix = st.tabs(
        ["Track analysis", "Playlist table", "Transition matrix"]
    )
    with tab_analysis:
        query = st.text_input("Filter tracks", key="analysis_filter", placeholder="search title / key…")
        table = frames["analysis_df"]
        if query:
            mask = table.apply(
                lambda r: query.lower() in " ".join(map(str, r.values)).lower(), axis=1
            )
            table = table[mask]
        st.dataframe(table, width="stretch", hide_index=True,
                     column_config=components.analysis_column_config())
    with tab_playlist:
        st.dataframe(frames["playlist_df"], width="stretch", hide_index=True,
                     column_config=components.playlist_column_config())
    with tab_matrix:
        st.caption(
            "Each cell scores mixing **from** the row track **into** the column track "
            "(out of ~115 — higher is smoother). Hover any column header in the other tabs "
            "for what each metric means."
        )
        st.dataframe(frames["matrix_df"], width="stretch")


def _module_export(frames: dict, ordered: list[dict]) -> None:
    render_downloads(frames)
    _divider()
    premium.render_premium_export_section(frames, ordered)


def render_results() -> None:
    ordered = state.ensure_order()
    if not ordered:
        st.warning("Every track is excluded — clear some exclusions in the control bar.")
        return

    frames = state.build_result_frames(ordered)

    render_status_chips(frames, ordered)

    failed = st.session_state.failed_files
    if failed:
        with st.expander(f"{len(failed)} files could not be analyzed", expanded=False):
            for failure in failed:
                st.write(failure)

    module = st.segmented_control(
        "Results section", options=MODULES, default=MODULES[0], key="an_module",
        label_visibility="collapsed", width="stretch",
    ) or MODULES[0]
    st.markdown(f'<p class="module-desc">{MODULE_DESCRIPTIONS[module]}</p>', unsafe_allow_html=True)

    if module == "🎼 Set builder":
        _module_set_builder(frames)
    elif module == "🔬 Inspector":
        _module_inspector(frames)
    elif module == "🌐 Discover":
        _module_discover(frames)
    elif module == "📊 Insights":
        _module_insights(frames)
    elif module == "📋 Data":
        _module_data(frames)
    else:
        _module_export(frames, ordered)


def analyzer_page() -> None:
    st.markdown(ANALYZER_CSS, unsafe_allow_html=True)
    render_header()

    if st.session_state.tracks is None:
        config = components.render_setup_panel()
        if config["run"]:
            run_analysis_flow(config)
            if st.session_state.tracks is not None:
                st.rerun()
        if st.session_state.last_error:
            st.error(st.session_state.last_error)
        return

    components.render_control_bar()
    render_results()

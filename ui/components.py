"""Reusable Streamlit UI pieces for the analyzer: setup panel, control bar,
playlist editor, metrics, and the track inspector."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from harmonic_playlist import (
    AUDIO_EXTENSIONS,
    CAMELOT_MAJOR,
    CAMELOT_MINOR,
    find_audio_files,
    key_to_camelot,
)

from . import state

DURATION_OPTIONS = {
    "First 3 minutes (fast)": 180.0,
    "First 5 minutes": 300.0,
    "Full track (slow)": None,
}

# All valid musical keys, for the manual-override selector.
KEY_OPTIONS = list(CAMELOT_MAJOR.keys()) + list(CAMELOT_MINOR.keys())

_WEIGHT_LABELS = {
    "harmonic": "Harmonic (key)", "bpm": "BPM", "rhythm": "Rhythm",
    "onset": "Onset density", "energy": "Energy",
}


def folder_picker_available() -> bool:
    """Native folder dialogs need Tkinter + a display — absent on cloud hosts.
    Import lazily so a headless server never crashes at import time."""
    if "_tk_available" not in st.session_state:
        try:
            import tkinter  # noqa: F401

            st.session_state["_tk_available"] = True
        except Exception:  # noqa: BLE001 - no tkinter / no display
            st.session_state["_tk_available"] = False
    return st.session_state["_tk_available"]


def pick_folder(title: str = "Select a folder") -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        folder = filedialog.askdirectory(title=title)
        root.destroy()
        return folder or ""
    except Exception:  # noqa: BLE001 - headless environment
        return ""


def camelot_class(camelot: str | None) -> str:
    if not camelot:
        return "camelot-a"
    return "camelot-b" if camelot.endswith("B") else "camelot-a"


def _key_label(key: str) -> str:
    return f"{key} · {key_to_camelot(key) or '—'}"


def folder_audio_count(folder: Path | None, recursive: bool) -> int:
    if folder and folder.is_dir():
        return len(find_audio_files(folder, recursive))
    return 0


# --------------------------------------------------------------------------- #
# Metric explanations (the numbers guide + table column help)
# --------------------------------------------------------------------------- #

def render_metrics_guide() -> None:
    with st.popover("Guide", width="stretch", help="What do all these numbers mean?"):
        st.markdown(
            """
**Every track**

| Number | What it is | How to read it |
|---|---|---|
| **BPM** | Tempo — beats per minute | Tracks within ~3 BPM blend without heavy tempo-bending. |
| **Key · Camelot** | Musical key as a DJ code (e.g. `Em · 9A`) | Compatible keys: **same code**, **number ±1 with the same letter** (9A→8A/10A), or **A↔B with the same number** (9A→9B). Detection is approximate — trust your ears. |
| **Key confidence** | How certain the key guess is, 0–1 | Above **0.7** solid · below **0.5** double-check by ear. |
| **Energy** | Average loudness in dB | A negative scale: **−25 mellow · −15 mid · −10 loud**. Closer to 0 = more intense. |
| **Hits / sec** | Percussive events per second (onset rate) | **1–2** sparse · **3–4** driving · **5+** very busy. |

**Transition score** — how smoothly one track mixes into the next. Five parts add up (defaults, before your weight sliders):

| Part | Max | What it rewards |
|---|---|---|
| Harmonic | 40 | Compatible Camelot keys (clashing keys score **−20**) |
| Rhythm | 30 | A similar groove pattern |
| BPM | 25 | Close tempo — loses 4 points per BPM of difference |
| Onset | 10 | Similar percussive busyness |
| Energy | 10 | Similar loudness |

**Rule of thumb: 75+ seamless · 40–75 workable · below 40 tricky.**
Your weight sliders multiply each part, so custom weights shift these bands.
"""
        )


def analysis_column_config() -> dict:
    return {
        "file": st.column_config.TextColumn("File", help="Where this track lives on disk."),
        "title": st.column_config.TextColumn("Title"),
        "bpm": st.column_config.NumberColumn(
            "BPM", help="Tempo in beats per minute. Tracks within ~3 BPM blend easily."),
        "key": st.column_config.TextColumn(
            "Key", help="Detected musical key. Approximate — trust your ears for final calls."),
        "mode": st.column_config.TextColumn(
            "Mode", help="Major usually feels brighter; minor darker."),
        "key_strength": st.column_config.NumberColumn(
            "Key confidence",
            help="0–1: how certain the key detection is. Above 0.7 solid; below 0.5 double-check by ear."),
        "camelot": st.column_config.TextColumn(
            "Camelot",
            help="DJ key code. Compatible: same code, number ±1 with the same letter, or A↔B with the same number."),
        "onset_rate": st.column_config.NumberColumn(
            "Hits / sec", help="Percussive events per second — how busy the groove is. 1–2 sparse · 3–4 driving · 5+ very busy."),
        "energy": st.column_config.NumberColumn(
            "Energy (dB)",
            help="Average loudness. Negative scale — −25 mellow, −10 loud. Closer to 0 = more intense."),
    }


def render_suggestion_cards(suggestions: list[dict], note: str) -> None:
    if note:
        st.caption(note)
    if not suggestions:
        return
    for entry in suggestions:
        chips = []
        if entry.get("camelot"):
            chips.append(f'<span class="disc-chip">{entry["camelot"]}</span>')
        if entry.get("bpm"):
            chips.append(f'<span class="disc-chip">{entry["bpm"]:.0f} BPM</span>')
        verdict = entry.get("verdict") or ""
        if verdict:
            cls = "good" if verdict == "great match" else ("warn" if verdict == "clashes" else "")
            score = entry.get("score")
            text = verdict if score is None else f"{verdict} · {score}"
            chips.append(
                f'<span class="disc-chip {cls}" title="Key + BPM compatibility with your '
                f'seed track, out of 65 (rhythm/energy need the audio).">{text}</span>'
            )
        match = entry.get("match")
        match_html = f'<span class="a">{match}% similar</span>' if match is not None else ""
        link = f'<a href="{entry["url"]}" target="_blank">Listen ↗</a>' if entry.get("url") else ""

        st.markdown(
            f'<div class="disc-card">'
            f'<div class="grow"><div class="t">{entry["title"]}</div>'
            f'<div class="a">{entry["artist"]} {match_html}</div></div>'
            f'{"".join(chips)}'
            f'<span class="src">{entry["source"]}</span>'
            f'{link}'
            f'</div>',
            unsafe_allow_html=True,
        )


def playlist_column_config() -> dict:
    config = analysis_column_config()
    config.update({
        "order": st.column_config.NumberColumn("#", help="Position in the suggested set."),
        "transition_score_from_previous": st.column_config.NumberColumn(
            "Transition",
            help="How smoothly the previous track mixes into this one, out of ~115. 75+ seamless · 40–75 workable · <40 tricky."),
        "harmonic_score": st.column_config.NumberColumn(
            "Harmonic", help="Key compatibility on the Camelot wheel. Max 40; clashing keys score −20."),
        "bpm_score": st.column_config.NumberColumn(
            "BPM match", help="Tempo closeness. Max 25 — loses 4 points per BPM of difference."),
        "rhythm_score": st.column_config.NumberColumn(
            "Rhythm", help="Groove similarity between the two tracks. Max 30."),
        "onset_score": st.column_config.NumberColumn(
            "Onset", help="How closely the percussive busyness matches. Max 10."),
        "energy_score": st.column_config.NumberColumn(
            "Energy match", help="How closely the loudness matches. Max 10."),
    })
    return config


# --------------------------------------------------------------------------- #
# Metrics + playlist
# --------------------------------------------------------------------------- #

# Sidebar groups: sections encode intent (what you're trying to do), so the
# rail reads as a workflow instead of a flat list.
_NAV_GROUPS = [
    ("Start", ["Overview", "Analyze"]),
    ("Build", ["Set builder", "Inspector", "Discover"]),
    ("Review", ["Insights", "Data"]),
    ("Ship", ["Export"]),
]


def render_sidebar_nav(modules: list[str], active: str) -> None:
    """The app rail: brand, grouped module navigation, library status, Home."""
    with st.sidebar:
        st.markdown('<div class="sb-brand"><span class="disc"></span>Keyflow</div>',
                    unsafe_allow_html=True)
        for section, group in _NAV_GROUPS:
            st.markdown(f'<div class="sb-section">{section}</div>', unsafe_allow_html=True)
            for module in group:
                if module not in modules:
                    continue
                slug = module.replace(" ", "_")
                st.button(module, key=f"nv_{slug}", width="stretch",
                          on_click=state.goto_module, args=(module,))

        tracks = st.session_state.tracks
        if tracks:
            st.markdown(
                f'<div class="sb-status"><b>{len(tracks)}</b> tracks analyzed<br>'
                f'ready to shape &amp; export</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="sb-status">No analysis yet —<br>'
                'start in <b>Analyze</b></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sb-section">App</div>', unsafe_allow_html=True)
        from ui import auth

        user = auth.current_user()
        if user:
            st.markdown(
                f'<div class="sb-status">{user["name"]}<br>'
                f'<b>{auth.ROLE_LABELS[user["role"]]}</b> plan</div>',
                unsafe_allow_html=True,
            )
        st.button("Account", key="nv_Account", width="stretch",
                  on_click=state.goto_module, args=("Account",))
        if st.button("← Home page", key="nav_home", width="stretch"):
            st.switch_page(st.session_state["_home_page"])

    # Active item: filled row + flat mint bar. Selector mirrors the base rule's
    # specificity so this later-injected style wins the tie.
    active_slug = active.replace(" ", "_")
    st.markdown(
        f'<style>section[data-testid="stSidebar"] .st-key-nv_{active_slug} button,'
        f'section[data-testid="stSidebar"] .st-key-nv_{active_slug} button[kind="secondary"] {{'
        f"color: var(--ink) !important; background: rgba(94,234,212,0.08) !important;"
        f"box-shadow: inset 3px 0 0 0 var(--accent) !important;"
        f"border-radius: 4px 10px 10px 4px !important;"
        f"}}</style>",
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: str, sub: str = "") -> None:
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_pill(row: pd.Series) -> str:
    score = row.get("transition_score_from_previous")
    if score in ("", None) or pd.isna(score):
        return ""
    value = float(score)
    if value >= 75:
        cls, word = " good", "seamless"
    elif value >= 40:
        cls, word = "", "workable"
    else:
        cls, word = " warn", "tricky"
    return (
        f'<span class="score-pill{cls}" title="How smoothly the previous track mixes '
        f'into this one, out of ~115. 75+ seamless · 40–75 workable · below 40 tricky.">'
        f'Transition: {score} · {word}</span>'
    )


def render_playlist_editor(playlist_df: pd.DataFrame, show_audio: bool) -> None:
    """Playlist cards with per-row move buttons and optional audio preview."""
    for position, (_, row) in enumerate(playlist_df.iterrows()):
        camelot = row.get("camelot") or "?"
        badge_col, body_col, move_col = st.columns([0.1, 0.75, 0.15])

        with badge_col:
            st.markdown(
                f'<div class="playlist-order">{int(row["order"])}</div>',
                unsafe_allow_html=True,
            )

        with body_col:
            st.markdown(
                f"""
                <div class="playlist-card">
                    <p class="playlist-title">{row["title"]}</p>
                    <div class="playlist-meta">
                        <span class="camelot-pill {camelot_class(camelot)}">{camelot}</span>
                        {row["key"]} · {row["bpm"]} BPM · energy {row["energy"]}
                    </div>
                    {_score_pill(row)}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if show_audio:
                audio_path = Path(str(row["file"]))
                if audio_path.exists():
                    try:
                        st.audio(str(audio_path))
                    except Exception:  # noqa: BLE001 - preview is best-effort
                        st.caption("Preview unavailable for this file.")

        with move_col:
            last = len(playlist_df) - 1
            if st.button("▲", key=f"up_{position}", disabled=position == 0,
                         width="stretch", help="Move up"):
                state.move_track(position, -1)
                st.rerun()
            if st.button("▼", key=f"down_{position}", disabled=position == last,
                         width="stretch", help="Move down"):
                state.move_track(position, 1)
                st.rerun()


# --------------------------------------------------------------------------- #
# Setup panel (state 1: no tracks yet)
# --------------------------------------------------------------------------- #

def _apply_pending_folders() -> None:
    for pending, target in (
        ("pending_music_folder", "music_folder"),
        ("pending_output_folder", "output_folder"),
    ):
        value = st.session_state.pop(pending, None)
        if value:
            st.session_state[target] = value


def render_setup_panel() -> dict:
    _apply_pending_folders()

    st.markdown(
        '<div class="setup-kicker">Setup</div>'
        '<h2 class="setup-title">Analyze your library</h2>'
        '<p class="setup-sub">Point at a folder of songs and build a harmonic set. '
        'Nothing is uploaded — every track is analyzed locally and stays on your machine.</p>'
        '<div class="setup-steps">'
        '<span><b>1</b> Choose a folder</span>'
        '<span><b>2</b> Analyze</span>'
        '<span><b>3</b> Shape &amp; export your set</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        folder_tab, upload_tab = st.tabs(["Local folder", "Upload tracks"])

        with folder_tab:
            if folder_picker_available():
                folder_col, browse_col = st.columns([4, 1], vertical_alignment="bottom")
                with browse_col:
                    if st.button("Browse", width="stretch"):
                        selected = pick_folder("Select your music folder")
                        if selected:
                            st.session_state.pending_music_folder = selected
                            st.rerun()
            else:
                (folder_col,) = st.columns(1)
            with folder_col:
                st.text_input("Music folder", key="music_folder", placeholder=r"C:\Music\DJ Set")
            st.toggle("Include subfolders", key="recursive")

        with upload_tab:
            uploads = st.file_uploader(
                "Drop audio files here",
                type=[ext.lstrip(".") for ext in sorted(AUDIO_EXTENSIONS)],
                accept_multiple_files=True,
                key="uploads",
                help="Uploaded tracks are analyzed from a temporary folder for this session.",
            )
            if uploads:
                st.caption(f"{len(uploads)} file(s) ready — uploads take priority over the folder.")

        duration_mode = st.selectbox("Analysis length", list(DURATION_OPTIONS.keys()), index=0)

        output_default = st.session_state.music_folder or str(Path.cwd() / "output")
        if not st.session_state.output_folder:
            st.session_state.output_folder = output_default
        with st.expander("Output folder (optional)"):
            st.text_input("Output folder", key="output_folder", placeholder=output_default)

        run_clicked = st.button("Analyze & build set", type="primary", width="stretch")

    folder = Path(st.session_state.music_folder) if st.session_state.music_folder else None
    count = folder_audio_count(folder, st.session_state.recursive)
    if uploads:
        pass  # upload tab already confirms the count
    elif count:
        st.caption(f"✅ Found {count} audio files ready to analyze.")
    elif st.session_state.music_folder:
        st.caption("⚠️ No audio files found there yet — check the path, or turn on **Include subfolders**.")
    else:
        st.caption("Choose a folder or drop some tracks above to begin.")

    return {
        "folder": folder,
        "uploads": uploads or [],
        "output": Path(st.session_state.output_folder) if st.session_state.output_folder else Path("output"),
        "duration": DURATION_OPTIONS[duration_mode],
        "recursive": st.session_state.recursive,
        "run": run_clicked,
    }


# --------------------------------------------------------------------------- #
# Control bar (state 3: results) — live controls, no sidebar
# --------------------------------------------------------------------------- #

def render_control_bar() -> None:
    tracks = st.session_state.tracks or []
    titles = [track["title"] for track in tracks]

    with st.container(border=True):
        st.markdown('<div class="bar-label">Set controls · reorder instantly, no re-analysis</div>',
                    unsafe_allow_html=True)
        new_col, start_col, curve_col, excl_col, wts_col = st.columns(
            [1.1, 1.8, 1.8, 1.1, 1.1], vertical_alignment="bottom"
        )

        with new_col:
            st.button("New analysis", width="stretch", help="Analyze a different folder or new uploads",
                      on_click=state.goto_module, args=("Analyze",))

        with start_col:
            st.selectbox("Start track", ["Auto"] + titles, key="start_title")

        with curve_col:
            from ui import auth

            if auth.entitled("energy_curve"):
                st.segmented_control(
                    "Energy curve", options=["build_up", "plateau"],
                    format_func=lambda v: {"build_up": "Build-up", "plateau": "Plateau"}[v],
                    key="energy_curve",
                )
            else:
                st.session_state.energy_curve = "build_up"
                st.caption("Energy curve: Build-up · **Plateau is Pro**")

        with excl_col:
            with st.popover(f"Exclude ({len(st.session_state.exclude)})", width="stretch"):
                st.multiselect("Drop tracks from the set", titles, key="exclude")

        with wts_col:
            with st.popover("Weights", width="stretch"):
                st.caption("Emphasize what matters for your mix.")
                store = st.session_state.weights
                for key, label in _WEIGHT_LABELS.items():
                    # Explicit value= from the canonical store: if the frontend
                    # drops the closed-popover widget state on a rerun, the
                    # slider re-seeds from the last known value instead of 0.
                    store[key] = st.slider(
                        label, 0.0, 2.0, value=float(store[key]), step=0.1, key=f"w_{key}"
                    )
                if not state.weights_are_default():
                    st.button("Reset weights", width="stretch", on_click=state.reset_weights)


# --------------------------------------------------------------------------- #
# Track inspector (state 3) — explore + manual correction
# --------------------------------------------------------------------------- #

def render_track_inspector(matrix_df: pd.DataFrame) -> None:
    tracks = st.session_state.tracks or []
    if not tracks:
        return
    titles = [track["title"] for track in tracks]

    sel = st.selectbox("Inspect a track", titles, key="inspect_title")
    track = next((t for t in tracks if t["title"] == sel), tracks[0])

    info_col, mixes_col = st.columns([1, 1], gap="large")

    with info_col:
        camelot = track["camelot"] or "?"
        st.markdown(
            f'<div class="inspect-chips">'
            f'<span class="camelot-pill {camelot_class(camelot)}" title="Camelot code — mix with '
            f'the same code, number ±1 with the same letter, or A↔B with the same number.">{camelot}</span>'
            f'<span class="ic" title="Detected musical key (approximate — trust your ears).">{track["key"]}</span>'
            f'<span class="ic" title="Tempo in beats per minute.">{track["bpm"]} BPM</span>'
            f'<span class="ic" title="Average loudness in dB. −25 mellow · −10 loud; closer to 0 = more intense.">energy {track["energy"]}</span>'
            f'<span class="ic" title="Percussive hits per second. 1–2 sparse · 3–4 driving · 5+ very busy.">onset {track["onset_rate"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        audio_path = Path(str(track["file"]))
        if audio_path.exists():
            try:
                st.audio(str(audio_path))
            except Exception:  # noqa: BLE001
                st.caption("Preview unavailable for this file.")

        with st.expander("Correct this track’s analysis"):
            key_col, bpm_col = st.columns(2)
            with key_col:
                idx = KEY_OPTIONS.index(track["key"]) if track["key"] in KEY_OPTIONS else 0
                new_key = st.selectbox(
                    "Key", KEY_OPTIONS, index=idx, format_func=_key_label, key=f"ovkey_{sel}"
                )
            with bpm_col:
                new_bpm = st.number_input(
                    "BPM", min_value=40.0, max_value=250.0,
                    value=float(track["bpm"]), step=0.5, key=f"ovbpm_{sel}",
                )
            if st.button("Apply correction", key=f"ovapply_{sel}", width="stretch"):
                state.override_track(sel, new_key, new_bpm)
                st.toast(f"Updated {sel}", icon="✅")
                st.rerun()

    with mixes_col:
        st.markdown('<div class="inspect-h">Mixes well into</div>', unsafe_allow_html=True)
        if sel not in matrix_df.index:
            st.caption("This track is currently excluded from the set.")
            return
        scores = pd.to_numeric(matrix_df.loc[sel], errors="coerce").dropna()
        top = scores.sort_values(ascending=False).head(3)
        if top.empty:
            st.caption("Not enough tracks to compare.")
            return
        for name, score in top.items():
            other = next((t for t in tracks if t["title"] == name), None)
            cam = (other["camelot"] if other else None) or "?"
            st.markdown(
                f'<div class="mix-card" title="Transition score {score:.0f} out of ~115 — '
                f'75+ seamless · 40–75 workable · below 40 tricky.">'
                f'<span class="camelot-pill {camelot_class(cam)}">{cam}</span>'
                f'<span class="mix-name">{name}</span>'
                f'<span class="mix-score">{score:.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

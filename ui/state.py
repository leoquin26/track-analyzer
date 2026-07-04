"""Session state, cached analysis, and in-memory re-scoring.

The expensive step (loading + feature extraction per file) is cached so that
changing scoring weights or editing the order never re-reads audio. The full
track dicts — including the numpy ``rhythm_vector`` that is stripped from CSV
exports — live in ``st.session_state`` so re-ordering is a millisecond operation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pandas as pd
import streamlit as st

from harmonic_playlist import (
    DEFAULT_WEIGHTS,
    analyze_track,
    build_playlist,
    build_playlist_dataframe,
    build_transition_matrix,
    find_audio_files,
    key_to_camelot,
)

WEIGHT_KEYS = list(DEFAULT_WEIGHTS.keys())


def init_session_state() -> None:
    defaults = {
        "music_folder": "",
        "output_folder": "",
        "tracks": None,          # list[dict] of analyzed tracks (with rhythm_vector)
        "audio_file_count": 0,
        "failed_files": [],
        "order": None,           # list[str] of titles in current playlist order
        "_order_sig": None,      # signature of the controls that produced `order`
        "exclude": [],
        "start_title": "Auto",
        "energy_curve": "build_up",
        "recursive": False,
        # Canonical scoring weights. Deliberately a plain dict, NOT widget keys:
        # popover slider state can be dropped by the frontend on a rerun while the
        # popover is closed, so widget keys alone are not a safe store.
        "weights": dict(DEFAULT_WEIGHTS),
        "last_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --------------------------------------------------------------------------- #
# Analysis (cached)
# --------------------------------------------------------------------------- #

@st.cache_data(show_spinner=False)
def _cached_analyze(file_str: str, mtime: float, duration: float | None) -> dict:
    """Cache key is (path, mtime, duration); re-runs only when a file changes."""
    return analyze_track(Path(file_str), duration=duration)


def analyze_folder(
    folder: Path,
    duration: float | None,
    recursive: bool,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> tuple[list[dict], list[str], int]:
    audio_files = find_audio_files(folder, recursive)
    total = len(audio_files)
    tracks: list[dict] = []
    failed: list[str] = []

    for index, path in enumerate(audio_files, start=1):
        if progress_callback:
            progress_callback(path.name, index, total)
        try:
            tracks.append(_cached_analyze(str(path), path.stat().st_mtime, duration))
        except Exception as error:  # noqa: BLE001 - surfaced to the user, never fatal
            failed.append(f"{path.name}: {error}")

    return tracks, failed, total


def store_analysis(tracks: list[dict], failed: list[str], total: int) -> None:
    st.session_state.tracks = tracks
    st.session_state.failed_files = failed
    st.session_state.audio_file_count = total
    st.session_state.order = None
    st.session_state._order_sig = None
    st.session_state.exclude = []
    st.session_state.start_title = "Auto"


# --------------------------------------------------------------------------- #
# Controls + re-scoring (in memory)
# --------------------------------------------------------------------------- #

def current_weights() -> dict[str, float]:
    return {key: float(st.session_state.weights[key]) for key in WEIGHT_KEYS}


def weights_are_default() -> bool:
    return current_weights() == DEFAULT_WEIGHTS


def reset_weights() -> None:
    """Reset weights. Used as an ``on_click`` callback — the only safe place to
    write to the slider widget keys after they've been instantiated."""
    st.session_state.weights = dict(DEFAULT_WEIGHTS)
    for key in WEIGHT_KEYS:
        st.session_state[f"w_{key}"] = DEFAULT_WEIGHTS[key]


def _control_signature() -> tuple:
    weights = tuple(current_weights()[k] for k in WEIGHT_KEYS)
    exclude = tuple(sorted(st.session_state.exclude))
    return (weights, st.session_state.start_title, st.session_state.energy_curve, exclude)


def ensure_order() -> list[dict]:
    """Return the ordered, non-excluded track dicts for the current controls.

    Auto-regenerates the order whenever a control changes; otherwise preserves
    the existing order (which may carry manual up/down edits).
    """
    tracks = st.session_state.tracks or []
    if not tracks:
        return []

    sig = _control_signature()
    regenerate = st.session_state.order is None or st.session_state._order_sig != sig

    if regenerate:
        start = st.session_state.start_title
        playlist = build_playlist(
            tracks,
            weights=current_weights(),
            start_title=None if start == "Auto" else start,
            energy_curve=st.session_state.energy_curve,
            exclude_titles=st.session_state.exclude,
        )
        st.session_state.order = [track["title"] for track in playlist]
        st.session_state._order_sig = sig

    by_title = {track["title"]: track for track in tracks}
    excluded = set(st.session_state.exclude)
    return [
        by_title[title]
        for title in st.session_state.order
        if title in by_title and title not in excluded
    ]


def move_track(index: int, delta: int) -> None:
    order = st.session_state.order
    target = index + delta
    if order is None or not (0 <= index < len(order)) or not (0 <= target < len(order)):
        return
    order[index], order[target] = order[target], order[index]


def invalidate_order() -> None:
    """Force ensure_order() to regenerate on the next run (after a data change)."""
    st.session_state._order_sig = None


def override_track(title: str, key: str, bpm: float) -> bool:
    """Apply a manual key/BPM correction to an analyzed track and re-score.

    The rhythm fingerprint is untouched; only the corrected fields change. Camelot
    is recomputed from the new key. Returns True if a track matched.
    """
    for track in st.session_state.tracks or []:
        if track["title"] == title:
            track["key"] = key
            track["camelot"] = key_to_camelot(key)
            track["bpm"] = round(float(bpm), 2)
            invalidate_order()
            return True
    return False


def get_secret(name: str, env: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:  # noqa: BLE001 - no secrets file configured
        pass
    return os.environ.get(env, "")


@st.cache_data(ttl=86400, show_spinner=False)
def _cached_suggestions(ref: dict, lastfm_key: str, gsb_key: str) -> tuple[list[dict], str]:
    from track_suggest import find_similar

    return find_similar(ref, lastfm_key=lastfm_key, getsongbpm_key=gsb_key)


def fetch_suggestions(track: dict) -> tuple[list[dict], str]:
    """Discover suggestions for one track, cached for a day per (track, keys)."""
    ref = {key: track.get(key) for key in ("title", "file", "camelot", "bpm", "key")}
    return _cached_suggestions(
        ref,
        get_secret("lastfm_api_key", "TA_LASTFM_API_KEY"),
        get_secret("getsongbpm_api_key", "TA_GETSONGBPM_KEY"),
    )


def build_result_frames(ordered: list[dict]) -> dict[str, pd.DataFrame | str]:
    weights = current_weights()
    analysis_df = pd.DataFrame(
        [{k: v for k, v in track.items() if k != "rhythm_vector"}
         for track in (st.session_state.tracks or [])]
    )
    playlist_df = build_playlist_dataframe(ordered, weights)
    matrix_df = build_transition_matrix(ordered, weights)
    from harmonic_playlist import build_m3u_content

    return {
        "analysis_df": analysis_df,
        "playlist_df": playlist_df,
        "matrix_df": matrix_df,
        "m3u_content": build_m3u_content(ordered),
    }

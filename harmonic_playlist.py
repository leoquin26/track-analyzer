"""
Analyze a folder of audio tracks and suggest a DJ-friendly playlist order.

Uses BPM, key/Camelot, rhythm fingerprint, onset density, and energy to score
transitions between tracks.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import librosa
import numpy as np
import pandas as pd

ProgressCallback = Callable[[str, int, int], None]

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

CAMELOT_MAJOR = {
    "B": "1B",
    "F#": "2B",
    "C#": "3B",
    "G#": "4B",
    "D#": "5B",
    "A#": "6B",
    "F": "7B",
    "C": "8B",
    "G": "9B",
    "D": "10B",
    "A": "11B",
    "E": "12B",
}

CAMELOT_MINOR = {
    "G#m": "1A",
    "D#m": "2A",
    "A#m": "3A",
    "Fm": "4A",
    "Cm": "5A",
    "Gm": "6A",
    "Dm": "7A",
    "Am": "8A",
    "Em": "9A",
    "Bm": "10A",
    "F#m": "11A",
    "C#m": "12A",
}

# Multipliers applied to each transition-score component. 1.0 reproduces the
# original hardcoded scoring; the dashboard exposes these as live sliders.
DEFAULT_WEIGHTS = {
    "harmonic": 1.0,
    "bpm": 1.0,
    "rhythm": 1.0,
    "onset": 1.0,
    "energy": 1.0,
}


def estimate_key(y: np.ndarray, sr: int) -> tuple[str, str, float]:
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    major_profile = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    minor_profile = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )

    candidates: list[tuple[str, str, float]] = []

    for i, note in enumerate(NOTE_NAMES):
        major_score = np.corrcoef(chroma_mean, np.roll(major_profile, i))[0, 1]
        minor_score = np.corrcoef(chroma_mean, np.roll(minor_profile, i))[0, 1]

        candidates.append((note, "major", major_score))
        candidates.append((note + "m", "minor", minor_score))

    best_key, mode, strength = max(candidates, key=lambda x: x[2])
    return best_key, mode, float(strength)


def key_to_camelot(key: str) -> str | None:
    if key.endswith("m"):
        return CAMELOT_MINOR.get(key)
    return CAMELOT_MAJOR.get(key)


def camelot_harmonic_score(current: str | None, candidate: str | None) -> int:
    if not current or not candidate:
        return 0

    current_num = int(current[:-1])
    current_letter = current[-1]

    candidate_num = int(candidate[:-1])
    candidate_letter = candidate[-1]

    if current == candidate:
        return 40

    if current_num == candidate_num and current_letter != candidate_letter:
        return 32

    previous_num = 12 if current_num == 1 else current_num - 1
    next_num = 1 if current_num == 12 else current_num + 1

    if candidate_letter == current_letter and candidate_num in {previous_num, next_num}:
        return 35

    return -20


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a)
    b = np.asarray(b)

    denominator = np.linalg.norm(a) * np.linalg.norm(b)

    if denominator == 0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def analyze_track(file_path: Path, duration: float | None = 180) -> dict:
    y, sr = librosa.load(file_path, mono=True, duration=duration)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    tempo, _beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    bpm = float(np.ravel(tempo)[0])

    key, mode, key_strength = estimate_key(y, sr)
    camelot = key_to_camelot(key)

    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)
    rhythm_vector = tempogram.mean(axis=1)

    if np.linalg.norm(rhythm_vector) > 0:
        rhythm_vector = rhythm_vector / np.linalg.norm(rhythm_vector)

    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    track_duration = len(y) / sr
    onset_rate = len(onsets) / track_duration if track_duration > 0 else 0.0

    rms = librosa.feature.rms(y=y)[0]
    energy = float(np.mean(librosa.amplitude_to_db(rms + 1e-9)))

    return {
        "file": str(file_path),
        "title": file_path.stem,
        "bpm": round(bpm, 2),
        "key": key,
        "mode": mode,
        "key_strength": round(key_strength, 3),
        "camelot": camelot,
        "onset_rate": round(onset_rate, 3),
        "energy": round(energy, 2),
        "rhythm_vector": rhythm_vector,
    }


def transition_score(
    current: dict, candidate: dict, weights: dict[str, float] | None = None
) -> float:
    return transition_score_breakdown(current, candidate, weights)["total_score"]


def transition_score_breakdown(
    current: dict, candidate: dict, weights: dict[str, float] | None = None
) -> dict[str, float]:
    weights = weights or DEFAULT_WEIGHTS

    harmonic = (
        camelot_harmonic_score(current["camelot"], candidate["camelot"])
        * weights["harmonic"]
    )

    bpm_difference = abs(current["bpm"] - candidate["bpm"])
    bpm_score = max(0, 25 - bpm_difference * 4) * weights["bpm"]

    rhythm_similarity = cosine_similarity(
        current["rhythm_vector"], candidate["rhythm_vector"]
    )
    rhythm_score = rhythm_similarity * 30 * weights["rhythm"]

    onset_difference = abs(current["onset_rate"] - candidate["onset_rate"])
    onset_score = max(0, 10 - onset_difference * 4) * weights["onset"]

    energy_difference = abs(current["energy"] - candidate["energy"])
    energy_score = max(0, 10 - energy_difference * 0.8) * weights["energy"]

    total = harmonic + bpm_score + rhythm_score + onset_score + energy_score

    return {
        "harmonic_score": round(harmonic, 2),
        "bpm_score": round(bpm_score, 2),
        "rhythm_score": round(rhythm_score, 2),
        "onset_score": round(onset_score, 2),
        "energy_score": round(energy_score, 2),
        "total_score": round(total, 2),
    }


def _pick_start_track(
    tracks: list[dict], start_title: str | None, energy_curve: str
) -> dict:
    if start_title:
        for track in tracks:
            if track["title"] == start_title:
                return track

    if energy_curve == "plateau":
        mean_energy = sum(track["energy"] for track in tracks) / len(tracks)
        return min(tracks, key=lambda t: abs(t["energy"] - mean_energy))

    # build_up (default): open on the lowest-energy track.
    return min(tracks, key=lambda t: t["energy"])


def build_playlist(
    tracks: list[dict],
    weights: dict[str, float] | None = None,
    start_title: str | None = None,
    energy_curve: str = "build_up",
    exclude_titles: list[str] | None = None,
) -> list[dict]:
    excluded = set(exclude_titles or [])
    pool = [track for track in tracks if track["title"] not in excluded]

    if not pool:
        return []

    start = _pick_start_track(pool, start_title, energy_curve)
    playlist = [start]
    remaining = [track for track in pool if track["title"] != start["title"]]

    while remaining:
        current = playlist[-1]

        def rank(candidate: dict) -> tuple[float, float]:
            score = transition_score(current, candidate, weights)
            # For a build-up, gently prefer the next track to rise in energy
            # when transition scores are close.
            energy_bias = (
                candidate["energy"] if energy_curve == "build_up" else 0.0
            )
            return (score, energy_bias)

        next_track = max(remaining, key=rank)
        playlist.append(next_track)
        remaining.remove(next_track)

    return playlist


def build_transition_matrix(
    tracks: list[dict], weights: dict[str, float] | None = None
) -> pd.DataFrame:
    titles = [track["title"] for track in tracks]
    matrix = pd.DataFrame(index=titles, columns=titles, dtype=object)

    for from_track in tracks:
        for to_track in tracks:
            if from_track["title"] == to_track["title"]:
                matrix.loc[from_track["title"], to_track["title"]] = None
            else:
                matrix.loc[from_track["title"], to_track["title"]] = transition_score(
                    from_track, to_track, weights
                )

    return matrix


def write_m3u_playlist(playlist: list[dict], output_path: Path) -> None:
    lines = ["#EXTM3U"]

    for track in playlist:
        lines.append(f"#EXTINF:-1,{track['title']}")
        lines.append(track["file"])

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@dataclass
class AnalysisResult:
    analysis_df: pd.DataFrame
    playlist_df: pd.DataFrame
    matrix_df: pd.DataFrame
    m3u_content: str
    output_dir: Path
    analyzed_count: int
    failed_files: list[str] = field(default_factory=list)
    audio_file_count: int = 0


def build_playlist_dataframe(
    playlist: list[dict], weights: dict[str, float] | None = None
) -> pd.DataFrame:
    playlist_rows = []

    for index, track in enumerate(playlist):
        previous = playlist[index - 1] if index > 0 else None
        row = {
            "order": index + 1,
            "title": track["title"],
            "file": track["file"],
            "bpm": track["bpm"],
            "key": track["key"],
            "camelot": track["camelot"],
            "energy": track["energy"],
            "onset_rate": track["onset_rate"],
        }

        if previous:
            breakdown = transition_score_breakdown(previous, track, weights)
            row["transition_score_from_previous"] = breakdown["total_score"]
            row["harmonic_score"] = breakdown["harmonic_score"]
            row["bpm_score"] = breakdown["bpm_score"]
            row["rhythm_score"] = breakdown["rhythm_score"]
            row["onset_score"] = breakdown["onset_score"]
            row["energy_score"] = breakdown["energy_score"]
        else:
            # NaN (not "") keeps these columns numeric so they serialize cleanly
            # to Arrow for st.dataframe; pandas still writes them as blank in CSV.
            row["transition_score_from_previous"] = np.nan
            row["harmonic_score"] = np.nan
            row["bpm_score"] = np.nan
            row["rhythm_score"] = np.nan
            row["onset_score"] = np.nan
            row["energy_score"] = np.nan

        playlist_rows.append(row)

    return pd.DataFrame(playlist_rows)


def build_m3u_content(playlist: list[dict]) -> str:
    lines = ["#EXTM3U"]

    for track in playlist:
        lines.append(f"#EXTINF:-1,{track['title']}")
        lines.append(track["file"])

    return "\n".join(lines) + "\n"


def run_analysis(
    folder: Path,
    output_dir: Path,
    duration: float | None = 180,
    recursive: bool = False,
    progress_callback: ProgressCallback | None = None,
    save_files: bool = True,
) -> AnalysisResult | None:
    tracks: list[dict] = []
    failed_files: list[str] = []
    audio_files = find_audio_files(folder, recursive)
    total_files = len(audio_files)

    if not audio_files:
        return None

    for index, file_path in enumerate(audio_files, start=1):
        if progress_callback:
            progress_callback(file_path.name, index, total_files)

        try:
            tracks.append(analyze_track(file_path, duration=duration))
        except Exception as error:
            failed_files.append(f"{file_path.name}: {error}")

    if not tracks:
        return None

    analysis_df = pd.DataFrame(
        [{k: v for k, v in track.items() if k != "rhythm_vector"} for track in tracks]
    )
    playlist = build_playlist(tracks)
    playlist_df = build_playlist_dataframe(playlist)
    matrix_df = build_transition_matrix(tracks)
    m3u_content = build_m3u_content(playlist)

    if save_files:
        output_dir.mkdir(parents=True, exist_ok=True)
        analysis_df.to_csv(output_dir / "track_analysis.csv", index=False)
        playlist_df.to_csv(output_dir / "playlist_order.csv", index=False)
        matrix_df.to_csv(output_dir / "transition_matrix.csv")
        (output_dir / "playlist.m3u").write_text(m3u_content, encoding="utf-8")

    return AnalysisResult(
        analysis_df=analysis_df,
        playlist_df=playlist_df,
        matrix_df=matrix_df,
        m3u_content=m3u_content,
        output_dir=output_dir,
        analyzed_count=len(tracks),
        failed_files=failed_files,
        audio_file_count=total_files,
    )


def find_audio_files(folder: Path, recursive: bool) -> list[Path]:
    if recursive:
        files = folder.rglob("*")
    else:
        files = folder.iterdir()

    return sorted(
        path
        for path in files
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def main(folder: Path, output_dir: Path, duration: float | None, recursive: bool) -> None:
    def on_progress(name: str, index: int, total: int) -> None:
        print(f"Analyzing ({index}/{total}): {name}")

    result = run_analysis(
        folder=folder,
        output_dir=output_dir,
        duration=duration,
        recursive=recursive,
        progress_callback=on_progress,
        save_files=True,
    )

    if result is None:
        print(f"No audio files found in {folder}" if not find_audio_files(folder, recursive) else "No tracks were successfully analyzed.")
        return

    for failure in result.failed_files:
        print(f"Could not analyze {failure}")

    print("Done.")
    print(f"Created: {result.output_dir / 'track_analysis.csv'}")
    print(f"Created: {result.output_dir / 'playlist_order.csv'}")
    print(f"Created: {result.output_dir / 'transition_matrix.csv'}")
    print(f"Created: {result.output_dir / 'playlist.m3u'}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze tracks and build a harmonic playlist order."
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing audio files to analyze",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for CSV output (defaults to the music folder)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=180,
        help="Seconds of each track to analyze (default: 180). Use 0 for full track.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Scan subfolders for audio files",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    if not args.folder.is_dir():
        print(f"Error: {args.folder} is not a valid folder.")
        sys.exit(1)

    duration = None if args.duration == 0 else args.duration
    output_dir = args.output_dir or args.folder

    main(args.folder, output_dir, duration, args.recursive)

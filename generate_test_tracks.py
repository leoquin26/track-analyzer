"""Generate short synthetic WAV files for smoke-testing harmonic_playlist.py."""

from pathlib import Path

import numpy as np
import soundfile as sf

SR = 22050
DURATION = 30


def make_track(path: Path, bpm: float, root_hz: float, amplitude: float) -> None:
    t = np.linspace(0, DURATION, int(SR * DURATION), endpoint=False)
    kick = (np.sin(2 * np.pi * (bpm / 60) * t) > 0.9).astype(float)
    tone = amplitude * np.sin(2 * np.pi * root_hz * t)
    audio = 0.6 * kick + 0.4 * tone
    sf.write(path, audio, SR)


def main() -> None:
    out = Path(__file__).parent / "test_tracks"
    out.mkdir(exist_ok=True)

    make_track(out / "track_a_124_am.wav", bpm=124, root_hz=220.0, amplitude=0.3)
    make_track(out / "track_b_125_em.wav", bpm=125, root_hz=329.63, amplitude=0.35)
    make_track(out / "track_c_128_cmaj.wav", bpm=128, root_hz=261.63, amplitude=0.5)

    print(f"Created test tracks in {out}")


if __name__ == "__main__":
    main()

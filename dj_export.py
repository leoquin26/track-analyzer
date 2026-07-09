"""DJ-software exporters and tag write-back (Premium feature).

Pure, engine-side builders — no Streamlit. Each takes the playlist DataFrame
(columns: title, file, bpm, key, camelot) and returns file content. ``write_tags``
writes detected key/BPM into the audio files themselves via mutagen.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

import pandas as pd

from harmonic_playlist import NOTE_NAMES

PLAYLIST_NAME = "Keyflow Set"
SUPPORTED_TAG_TYPES = {".mp3", ".flac", ".ogg", ".m4a", ".aac"}


# --------------------------------------------------------------------------- #
# rekordbox XML
# --------------------------------------------------------------------------- #

def _rekordbox_location(path: str) -> str:
    # rekordbox wants a file URI like file://localhost/C:/Music/x.mp3
    posix = Path(path).as_posix()
    return "file://localhost/" + quote(posix, safe="/:")


def rekordbox_xml(playlist_df: pd.DataFrame) -> str:
    rows = list(playlist_df.itertuples(index=False))
    collection = []
    playlist_refs = []
    for i, row in enumerate(rows, start=1):
        collection.append(
            f'      <TRACK TrackID="{i}" Name="{escape(str(row.title))}" '
            f'Artist="" AverageBpm="{float(row.bpm):.2f}" '
            f'Tonality="{escape(str(row.key))}" '
            f'Location="{_rekordbox_location(str(row.file))}" TotalTime="0"/>'
        )
        playlist_refs.append(f'        <TRACK Key="{i}"/>')

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<DJ_PLAYLISTS Version="1.0.0">\n'
        '  <PRODUCT Name="Keyflow" Version="1.0" Company="Keyflow"/>\n'
        f'  <COLLECTION Entries="{len(rows)}">\n'
        + "\n".join(collection) + "\n"
        "  </COLLECTION>\n"
        "  <PLAYLISTS>\n"
        '    <NODE Type="0" Name="ROOT" Count="1">\n'
        f'      <NODE Name="{escape(PLAYLIST_NAME)}" Type="1" KeyType="0" Entries="{len(rows)}">\n'
        + "\n".join(playlist_refs) + "\n"
        "      </NODE>\n"
        "    </NODE>\n"
        "  </PLAYLISTS>\n"
        "</DJ_PLAYLISTS>\n"
    )


# --------------------------------------------------------------------------- #
# Serato crate (binary)
# --------------------------------------------------------------------------- #

def _serato_chunk(tag: bytes, data: bytes) -> bytes:
    return tag + len(data).to_bytes(4, "big") + data


def serato_crate(playlist_df: pd.DataFrame) -> bytes:
    out = _serato_chunk(b"vrsn", "1.0/Serato ScratchLive Crate".encode("utf-16-be"))
    for row in playlist_df.itertuples(index=False):
        # Serato stores a path relative to the volume root, forward slashes.
        p = Path(str(row.file))
        rel = p.as_posix()
        if p.drive:
            rel = rel[len(p.drive):].lstrip("/")
        ptrk = _serato_chunk(b"ptrk", rel.encode("utf-16-be"))
        out += _serato_chunk(b"otrk", ptrk)
    return out


# --------------------------------------------------------------------------- #
# Traktor NML
# --------------------------------------------------------------------------- #

def _traktor_key_value(key: str) -> int | None:
    is_minor = key.endswith("m")
    note = key[:-1] if is_minor else key
    if note not in NOTE_NAMES:
        return None
    return NOTE_NAMES.index(note) + (12 if is_minor else 0)


def _traktor_location(path: str) -> tuple[str, str, str]:
    p = Path(str(path))
    volume = p.drive or ""
    segments = p.parent.parts
    if p.drive and segments and segments[0] == p.anchor:
        segments = segments[1:]
    directory = "".join(f"/:{seg}" for seg in segments) + "/:"
    return volume, directory, p.name


def traktor_nml(playlist_df: pd.DataFrame) -> str:
    rows = list(playlist_df.itertuples(index=False))
    entries = []
    refs = []
    for row in rows:
        volume, directory, filename = _traktor_location(str(row.file))
        key_val = _traktor_key_value(str(row.key))
        key_xml = f'\n      <MUSICAL_KEY VALUE="{key_val}"/>' if key_val is not None else ""
        entries.append(
            f'    <ENTRY TITLE="{escape(str(row.title))}" ARTIST="">\n'
            f'      <LOCATION DIR="{escape(directory)}" FILE="{escape(filename)}" '
            f'VOLUME="{escape(volume)}" VOLUMEID="{escape(volume)}"/>\n'
            f'      <TEMPO BPM="{float(row.bpm):.2f}" BPM_QUALITY="100"/>'
            f'{key_xml}\n'
            f'    </ENTRY>'
        )
        refs.append(
            f'        <ENTRY><PRIMARYKEY TYPE="TRACK" '
            f'KEY="{escape(volume + directory + filename)}"/></ENTRY>'
        )

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<NML VERSION="19">\n'
        '  <HEAD COMPANY="Keyflow" PROGRAM="Keyflow"/>\n'
        f'  <COLLECTION ENTRIES="{len(rows)}">\n'
        + "\n".join(entries) + "\n"
        "  </COLLECTION>\n"
        "  <PLAYLISTS>\n"
        '    <NODE TYPE="FOLDER" NAME="$ROOT">\n'
        '      <SUBNODES COUNT="1">\n'
        f'        <NODE TYPE="PLAYLIST" NAME="{escape(PLAYLIST_NAME)}">\n'
        f'          <PLAYLIST ENTRIES="{len(rows)}" TYPE="LIST">\n'
        + "\n".join(refs) + "\n"
        "          </PLAYLIST>\n"
        "        </NODE>\n"
        "      </SUBNODES>\n"
        "    </NODE>\n"
        "  </PLAYLISTS>\n"
        "</NML>\n"
    )


# --------------------------------------------------------------------------- #
# Tag write-back (mutagen)
# --------------------------------------------------------------------------- #

def write_tags(tracks: list[dict]) -> list[str]:
    """Write key + BPM into each file's tags. Returns a per-file status list."""
    results: list[str] = []
    for track in tracks:
        path = Path(str(track["file"]))
        name = path.name
        if not path.exists():
            results.append(f"{name}: missing file")
            continue
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_TAG_TYPES:
            results.append(f"{name}: skipped ({suffix or 'no ext'} unsupported)")
            continue
        try:
            _write_one(path, suffix, str(track["key"]), float(track["bpm"]))
            results.append(f"{name}: ✓ {track['key']} / {track['bpm']} BPM")
        except Exception as error:  # noqa: BLE001 - reported, never fatal
            results.append(f"{name}: failed ({error})")
    return results


def _write_one(path: Path, suffix: str, key: str, bpm: float) -> None:
    bpm_str = str(int(round(bpm)))
    if suffix == ".mp3":
        from mutagen.id3 import ID3, TKEY, TBPM
        try:
            tags = ID3(path)
        except Exception:  # noqa: BLE001 - no existing tags
            tags = ID3()
        tags.setall("TKEY", [TKEY(encoding=3, text=[key])])
        tags.setall("TBPM", [TBPM(encoding=3, text=[bpm_str])])
        tags.save(path)
    elif suffix in {".flac", ".ogg"}:
        from mutagen import File as MutagenFile
        audio = MutagenFile(path)
        audio["initialkey"] = key
        audio["bpm"] = bpm_str
        audio.save()
    else:  # .m4a / .aac (MP4 container)
        from mutagen.mp4 import MP4
        audio = MP4(path)
        audio["tmpo"] = [int(round(bpm))]
        audio["----:com.apple.iTunes:initialkey"] = key.encode("utf-8")
        audio.save()

"""Track suggestions from external sources (the Discover feature).

Sources, in order of preference:
- Last.fm ``track.getSimilar`` (best quality; needs a free API key)
- ListenBrainz similar-recordings via MusicBrainz lookup (open data, no key)
- GetSongBPM enrichment (key + BPM for suggested tracks; optional key)

Engine-side: no Streamlit. All network calls go through ``_get_json`` with a
timeout and return ``None`` on any failure — a suggestion source that's down
degrades to an empty list, never an exception.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from harmonic_playlist import camelot_harmonic_score, key_to_camelot

USER_AGENT = "Keyflow/1.0 (harmonic set builder; keyflow.dj)"
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
LB_SEARCH_URL = "https://labs.api.listenbrainz.org/recording-search/json"
LISTENBRAINZ_URL = "https://labs.api.listenbrainz.org/similar-recordings/json"
GETSONGBPM_URL = "https://api.getsong.co/search/"

# ListenBrainz labs requires an algorithm from its published enum (the API's
# 400 response lists valid values). Widest listening window = best coverage.
LB_ALGORITHM = "session_based_days_9000_session_300_contribution_5_threshold_15_limit_50_skip_30"


def _get_json(url: str, params: dict, timeout: int = 10) -> dict | list | None:
    try:
        query = urllib.parse.urlencode(params)
        request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception:  # noqa: BLE001 - a down source is an empty source
        return None


# --------------------------------------------------------------------------- #
# Identifying the local track (filenames/tags -> artist + title)
# --------------------------------------------------------------------------- #

def parse_artist_title(track: dict) -> tuple[str | None, str]:
    """Best-effort (artist, title) for a local track: tags first, then a
    ``Artist - Title`` filename split, else no artist."""
    path = Path(str(track.get("file", "")))
    if path.exists():
        try:
            from mutagen import File as MutagenFile

            audio = MutagenFile(path, easy=True)
            if audio and audio.tags:
                artists = audio.tags.get("artist") or []
                titles = audio.tags.get("title") or []
                if artists and titles:
                    return str(artists[0]), str(titles[0])
        except Exception:  # noqa: BLE001 - tags are a best-effort source
            pass

    stem = str(track.get("title", path.stem))
    match = re.match(r"^(.{2,60}?)\s*[-–—]\s+(.{2,})$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, stem


# --------------------------------------------------------------------------- #
# Suggestion sources
# --------------------------------------------------------------------------- #

def lastfm_similar(artist: str, title: str, api_key: str, limit: int = 8) -> list[dict]:
    data = _get_json(LASTFM_URL, {
        "method": "track.getsimilar",
        "artist": artist,
        "track": title,
        "api_key": api_key,
        "format": "json",
        "limit": limit,
        "autocorrect": 1,
    })
    if not isinstance(data, dict):
        return []
    tracks = (data.get("similartracks") or {}).get("track") or []
    results = []
    for entry in tracks:
        name = entry.get("name")
        artist_name = (entry.get("artist") or {}).get("name")
        if not name or not artist_name:
            continue
        results.append({
            "title": name,
            "artist": artist_name,
            "match": round(float(entry.get("match", 0)) * 100),
            "url": entry.get("url", ""),
            "source": "Last.fm",
        })
    return results


def _canonical_mbid(artist: str | None, title: str) -> str | None:
    """ListenBrainz's own search returns the *canonical* recording MBID —
    the one its similarity index is keyed on. (Plain MusicBrainz search
    returns arbitrary release recordings that mostly have no similarity data.)"""
    query = f"{artist} {title}" if artist else title
    data = _get_json(LB_SEARCH_URL, {"query": query})
    if not isinstance(data, list) or not data:
        return None
    return data[0].get("recording_mbid")


def listenbrainz_similar(artist: str | None, title: str, limit: int = 8) -> list[dict]:
    mbid = _canonical_mbid(artist, title)
    if not mbid:
        return []
    data = _get_json(LISTENBRAINZ_URL, {
        "recording_mbids": mbid,
        "algorithm": LB_ALGORITHM,
    })
    if not isinstance(data, list):
        return []
    results = []
    for entry in data[:limit]:
        name = entry.get("recording_name")
        artist_name = entry.get("artist_credit_name")
        if not name or not artist_name:
            continue
        results.append({
            "title": name,
            "artist": artist_name,
            "match": None,
            "url": f"https://musicbrainz.org/recording/{entry.get('recording_mbid', '')}",
            "source": "ListenBrainz",
        })
    return results


def getsongbpm_lookup(artist: str, title: str, api_key: str) -> dict | None:
    """Fetch key/BPM for a suggested (remote) track. Returns
    ``{"bpm": float|None, "key": str|None, "camelot": str|None}`` or None."""
    data = _get_json(GETSONGBPM_URL, {
        "api_key": api_key,
        "type": "both",
        "lookup": f"song:{title} artist:{artist}",
    })
    if not isinstance(data, dict):
        return None
    hits = data.get("search")
    if not isinstance(hits, list) or not hits:
        return None
    hit = hits[0]
    bpm = hit.get("tempo") or hit.get("bpm")
    key = hit.get("key_of") or hit.get("key")
    try:
        bpm = float(bpm) if bpm else None
    except (TypeError, ValueError):
        bpm = None
    key = _normalize_key(key) if key else None
    return {
        "bpm": bpm,
        "key": key,
        "camelot": key_to_camelot(key) if key else None,
    }


def _normalize_key(raw: str) -> str | None:
    """Map notations like 'A min', 'Ebm', 'F♯ Major' onto our key names."""
    text = raw.strip().replace("♯", "#").replace("♭", "b")
    match = re.match(r"^([A-Ga-g])([#b]?)\s*(.*)$", text)
    if not match:
        return None
    note = match.group(1).upper()
    accidental = match.group(2)
    rest = match.group(3).strip().lower()

    flats = {"Ab": "G#", "Bb": "A#", "Cb": "B", "Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#"}
    name = note + ("#" if accidental == "#" else "")
    if accidental == "b":
        name = flats.get(note + "b", note)

    minor = rest.startswith("m") and not rest.startswith("maj")
    return name + ("m" if minor else "")


# --------------------------------------------------------------------------- #
# Compatibility of a suggestion against a local reference track
# --------------------------------------------------------------------------- #

def suggestion_compatibility(reference: dict, info: dict | None) -> dict:
    """Partial transition score (harmonic 40 + BPM 25 = 65 max) for a remote
    suggestion; rhythm/energy need audio we don't have."""
    if not info or (info.get("camelot") is None and info.get("bpm") is None):
        return {"score": None, "verdict": "no key data"}

    score = 0.0
    if info.get("camelot"):
        score += camelot_harmonic_score(reference.get("camelot"), info["camelot"])
    if info.get("bpm"):
        score += max(0, 25 - abs(float(reference["bpm"]) - info["bpm"]) * 4)

    if score >= 45:
        verdict = "great match"
    elif score >= 20:
        verdict = "workable"
    else:
        verdict = "clashes"
    return {"score": round(score), "verdict": verdict}


def find_similar(
    reference: dict,
    lastfm_key: str = "",
    getsongbpm_key: str = "",
    limit: int = 8,
) -> tuple[list[dict], str]:
    """Suggestions for one local track. Returns (suggestions, source_note).

    Each suggestion: title, artist, match, url, source, plus key/bpm/camelot
    and a compatibility verdict when enrichment data is available.
    """
    artist, title = parse_artist_title(reference)

    suggestions: list[dict] = []
    note = ""
    if lastfm_key and artist:
        suggestions = lastfm_similar(artist, title, lastfm_key, limit)
    if not suggestions:
        suggestions = listenbrainz_similar(artist, title, limit)
        if suggestions:
            note = "Powered by open ListenBrainz data."
    if not suggestions:
        if not artist and not lastfm_key:
            note = ("Couldn't identify an artist for this track — name files like "
                    "'Artist - Title' or add artist tags for better matches.")
        else:
            note = "No similar tracks found for this one."
        return [], note

    for suggestion in suggestions:
        info = None
        if getsongbpm_key:
            info = getsongbpm_lookup(suggestion["artist"], suggestion["title"], getsongbpm_key)
        if info:
            suggestion.update(info)
        suggestion.update(suggestion_compatibility(reference, info))

    # Most compatible first when we have scores; otherwise keep source order.
    suggestions.sort(key=lambda s: (s["score"] is None, -(s["score"] or 0)))
    return suggestions, note

"""Keyflow API — SaaS Fase 1: the engine behind HTTP, with real auth and plans.

    uvicorn api.main:app --port 8000

Design (mirrors docs/planning/track-analyzer-roadmap-saas.md):
- Auth shares ``authcore`` with the Streamlit UI: opaque revocable session
  tokens double as Bearer credentials, so a login works on both surfaces.
- ``POST /v1/analyze`` accepts uploads, enforces the caller's plan limits
  server-side, and runs as a background **job** (in-process worker pool for
  the MVP; the jobs table keeps the contract so RQ/Redis can slot in later).
- **Content-hash cache**: a file already analyzed (same sha256, same duration)
  is served from cache without touching librosa.
- **Audio is deleted** right after analysis — only the feature JSON survives.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import authcore
from harmonic_playlist import (
    AUDIO_EXTENSIONS,
    DEFAULT_WEIGHTS,
    analyze_track,
    build_playlist,
    build_playlist_dataframe,
    build_m3u_content,
)

app = FastAPI(title="Keyflow API", version="1.0.0",
              description="Harmonic set building over HTTP. Sets that flow in key.")

_bearer = HTTPBearer(auto_error=False)
_executor = ThreadPoolExecutor(max_workers=2)

ANALYSIS_DURATION_MAX = 300.0  # cost control: cap per-track seconds analyzed


# --------------------------------------------------------------------------- #
# Storage: jobs + feature cache live next to the auth tables
# --------------------------------------------------------------------------- #

def _db() -> sqlite3.Connection:
    conn = authcore._connect()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,            -- queued | running | done | error
            progress REAL NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            cached INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            result_json TEXT,
            created_at REAL NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS feature_cache (
            content_hash TEXT NOT NULL,
            duration REAL NOT NULL,
            features_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            PRIMARY KEY (content_hash, duration)
        )"""
    )
    return conn


# --------------------------------------------------------------------------- #
# Auth dependency
# --------------------------------------------------------------------------- #

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    user = authcore.restore_session(credentials.credentials if credentials else None)
    if not user:
        raise HTTPException(401, "Sign in first — send 'Authorization: Bearer <token>'.")
    return user


def _cap(user: dict, capability: str):
    return authcore.ENTITLEMENTS[user["role"]].get(capability)


# --------------------------------------------------------------------------- #
# Auth endpoints
# --------------------------------------------------------------------------- #

class Credentials(BaseModel):
    email: str
    password: str
    name: str | None = None


@app.post("/v1/auth/register")
def api_register(body: Credentials):
    user, error = authcore.register(body.email, body.name or body.email.split("@")[0],
                                    body.password)
    if not user:
        raise HTTPException(400, error)
    return {"token": authcore.issue_session(user["id"]), "user": user}


@app.post("/v1/auth/login")
def api_login(body: Credentials):
    user, error = authcore.login(body.email, body.password)
    if not user:
        raise HTTPException(401, error)
    return {"token": authcore.issue_session(user["id"]), "user": user}


@app.post("/v1/auth/logout")
def api_logout(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
               user: dict = Depends(current_user)):
    authcore.revoke_session(credentials.credentials if credentials else None)
    return {"ok": True}


@app.get("/v1/me")
def api_me(user: dict = Depends(current_user)):
    return {"user": user, "plan": authcore.ROLE_LABELS[user["role"]],
            "entitlements": authcore.ENTITLEMENTS[user["role"]]}


# --------------------------------------------------------------------------- #
# Analysis jobs
# --------------------------------------------------------------------------- #

def _set_job(job_id: str, **fields) -> None:
    keys = ", ".join(f"{k}=?" for k in fields)
    with _db() as conn:
        conn.execute(f"UPDATE jobs SET {keys} WHERE id=?", (*fields.values(), job_id))


def _run_job(job_id: str, job_dir: Path, duration: float) -> None:
    try:
        _set_job(job_id, status="running")
        files = sorted(p for p in job_dir.iterdir()
                       if p.suffix.lower() in AUDIO_EXTENSIONS)
        tracks, failed, cached_hits = [], [], 0

        for index, path in enumerate(files, start=1):
            content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            with _db() as conn:
                row = conn.execute(
                    "SELECT features_json FROM feature_cache"
                    " WHERE content_hash=? AND duration=?",
                    (content_hash, duration),
                ).fetchone()
            if row:
                features = json.loads(row["features_json"])
                features["title"] = path.stem  # the uploader's name wins
                cached_hits += 1
            else:
                try:
                    features = analyze_track(path, duration=duration)
                    features["rhythm_vector"] = [float(x) for x in features["rhythm_vector"]]
                    with _db() as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO feature_cache"
                            " (content_hash, duration, features_json, created_at)"
                            " VALUES (?,?,?,?)",
                            (content_hash, duration,
                             json.dumps({**features, "file": path.name}), time.time()),
                        )
                except Exception as error:  # noqa: BLE001 - per-file, never fatal
                    failed.append(f"{path.name}: {error}")
                    _set_job(job_id, progress=index / max(len(files), 1))
                    continue
            features["file"] = path.name
            tracks.append(features)
            _set_job(job_id, progress=index / max(len(files), 1))

        result = {"tracks": tracks, "failed": failed}
        _set_job(job_id, status="done", progress=1.0, cached=cached_hits,
                 result_json=json.dumps(result))
    except Exception as error:  # noqa: BLE001 - job-level failure
        _set_job(job_id, status="error", error=str(error))
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)  # audio never outlives the job


@app.post("/v1/analyze")
def api_analyze(files: list[UploadFile] = File(...),
                duration: float = Form(180.0),
                user: dict = Depends(current_user)):
    duration = min(max(duration, 30.0), ANALYSIS_DURATION_MAX)

    audio = [f for f in files
             if Path(f.filename or "").suffix.lower() in AUDIO_EXTENSIONS]
    if not audio:
        raise HTTPException(400, f"No audio files. Supported: {sorted(AUDIO_EXTENSIONS)}")

    max_tracks = _cap(user, "max_tracks")
    if max_tracks is not None and len(audio) > max_tracks:
        raise HTTPException(
            403, f"Your {authcore.ROLE_LABELS[user['role']]} plan analyzes up to "
                 f"{max_tracks} tracks per request (you sent {len(audio)}). "
                 f"Upgrade to Pro for unlimited tracks.")

    job_id = uuid.uuid4().hex
    job_dir = Path(tempfile.mkdtemp(prefix=f"kf_job_{job_id[:8]}_"))
    for upload in audio:
        (job_dir / Path(upload.filename).name).write_bytes(upload.file.read())

    with _db() as conn:
        conn.execute(
            "INSERT INTO jobs (id, user_id, status, total, created_at) VALUES (?,?,?,?,?)",
            (job_id, user["id"], "queued", len(audio), time.time()),
        )
    _executor.submit(_run_job, job_id, job_dir, duration)
    return {"job_id": job_id, "tracks_accepted": len(audio), "duration": duration}


def _get_job(job_id: str, user: dict) -> sqlite3.Row:
    with _db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row or row["user_id"] != user["id"]:
        raise HTTPException(404, "No such job.")
    return row


@app.get("/v1/jobs/{job_id}")
def api_job(job_id: str, user: dict = Depends(current_user)):
    row = _get_job(job_id, user)
    return {"job_id": job_id, "status": row["status"], "progress": row["progress"],
            "total": row["total"], "cached_hits": row["cached"], "error": row["error"]}


def _job_tracks(job_id: str, user: dict) -> tuple[list[dict], list[str]]:
    row = _get_job(job_id, user)
    if row["status"] != "done":
        raise HTTPException(409, f"Job is {row['status']} — poll /v1/jobs/{job_id} until done.")
    result = json.loads(row["result_json"])
    tracks = result["tracks"]
    for track in tracks:  # numpy back for the scoring engine
        track["rhythm_vector"] = np.array(track["rhythm_vector"], dtype=float)
    return tracks, result["failed"]


@app.get("/v1/jobs/{job_id}/result")
def api_job_result(job_id: str, user: dict = Depends(current_user)):
    tracks, failed = _job_tracks(job_id, user)
    slim = [{k: v for k, v in t.items() if k != "rhythm_vector"} for t in tracks]
    return {"tracks": slim, "failed": failed}


# --------------------------------------------------------------------------- #
# Playlist + exports
# --------------------------------------------------------------------------- #

class PlaylistRequest(BaseModel):
    job_id: str
    weights: dict[str, float] | None = None
    start_title: str | None = None
    energy_curve: str = "build_up"
    exclude_titles: list[str] = []


def _build(body: PlaylistRequest, user: dict):
    if body.energy_curve not in ("build_up", "plateau"):
        raise HTTPException(400, "energy_curve must be 'build_up' or 'plateau'.")
    if body.energy_curve == "plateau" and not _cap(user, "energy_curve"):
        raise HTTPException(403, "The plateau energy curve is a Pro feature.")
    weights = {**DEFAULT_WEIGHTS, **(body.weights or {})}
    if set(weights) != set(DEFAULT_WEIGHTS):
        raise HTTPException(400, f"weights keys must be {sorted(DEFAULT_WEIGHTS)}.")

    tracks, _failed = _job_tracks(body.job_id, user)
    playlist = build_playlist(tracks, weights=weights, start_title=body.start_title,
                              energy_curve=body.energy_curve,
                              exclude_titles=body.exclude_titles)
    if not playlist:
        raise HTTPException(400, "Every track was excluded — nothing to order.")
    return playlist, weights


@app.post("/v1/playlist")
def api_playlist(body: PlaylistRequest, user: dict = Depends(current_user)):
    playlist, weights = _build(body, user)
    frame = build_playlist_dataframe(playlist, weights)
    records = json.loads(frame.to_json(orient="records"))
    return {"playlist": records}


EXPORT_FORMATS = {"csv", "m3u", "rekordbox", "serato", "traktor"}
FREE_FORMATS = {"csv", "m3u"}


@app.post("/v1/export/{fmt}")
def api_export(fmt: str, body: PlaylistRequest, user: dict = Depends(current_user)):
    if fmt not in EXPORT_FORMATS:
        raise HTTPException(404, f"Unknown format. Use one of {sorted(EXPORT_FORMATS)}.")
    if fmt not in FREE_FORMATS and not _cap(user, "dj_export"):
        raise HTTPException(403, f"'{fmt}' export is a Pro feature — CSV and M3U are free.")

    playlist, weights = _build(body, user)
    frame = build_playlist_dataframe(playlist, weights)

    if fmt == "csv":
        return Response(frame.to_csv(index=False), media_type="text/csv")
    if fmt == "m3u":
        return Response(build_m3u_content(playlist), media_type="audio/x-mpegurl")

    import dj_export as dx

    if fmt == "rekordbox":
        return Response(dx.rekordbox_xml(frame), media_type="application/xml")
    if fmt == "serato":
        return Response(dx.serato_crate(frame), media_type="application/octet-stream")
    return Response(dx.traktor_nml(frame), media_type="application/xml")


@app.get("/v1/health")
def api_health():
    return {"ok": True, "service": "keyflow-api", "version": app.version}

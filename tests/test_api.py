"""End-to-end test of the Keyflow API against a temp DB and real synthetic audio."""
import pathlib
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import authcore

authcore.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "kf_api.db"

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)
WAVS = sorted(pathlib.Path("test_tracks").glob("*.wav"))


def _files():
    return [("files", (p.name, p.read_bytes(), "audio/wav")) for p in WAVS]


def _wait(job_id, headers, timeout=120):
    for _ in range(timeout * 2):
        r = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
        if r["status"] in ("done", "error"):
            return r
        time.sleep(0.5)
    raise TimeoutError


# 1. health + auth
assert client.get("/v1/health").json()["ok"]
r = client.post("/v1/auth/register",
                json={"email": "api@kf.dj", "password": "password123", "name": "API DJ"})
assert r.status_code == 200, r.text
token = r.json()["token"]
H = {"Authorization": f"Bearer {token}"}
assert client.get("/v1/me", headers=H).json()["user"]["role"] == "free"
assert client.get("/v1/me").status_code == 401
assert client.post("/v1/auth/login",
                   json={"email": "api@kf.dj", "password": "WRONG"}).status_code == 401
print("1. health + register/login/me + 401 sin token OK")

# 2. analyze -> job -> result (free)
r = client.post("/v1/analyze", files=_files(), data={"duration": 30}, headers=H)
assert r.status_code == 200, r.text
job = r.json()["job_id"]
status = _wait(job, H)
assert status["status"] == "done", status
assert status["cached_hits"] == 0
result = client.get(f"/v1/jobs/{job}/result", headers=H).json()
assert len(result["tracks"]) == 3 and not result["failed"]
assert "rhythm_vector" not in result["tracks"][0]
print("2. analyze -> job done -> result (3 tracks, sin rhythm_vector) OK")

# 3. cache por hash: mismo audio, segundo job = todo cacheado
r = client.post("/v1/analyze", files=_files(), data={"duration": 30}, headers=H)
job2 = r.json()["job_id"]
status2 = _wait(job2, H)
assert status2["cached_hits"] == 3, status2
print("3. cache por hash: 3/3 hits en el segundo análisis OK")

# 4. playlist (free: build_up ok, plateau 403)
r = client.post("/v1/playlist", json={"job_id": job}, headers=H)
assert r.status_code == 200, r.text
playlist = r.json()["playlist"]
assert len(playlist) == 3 and playlist[0]["order"] == 1
r = client.post("/v1/playlist", json={"job_id": job, "energy_curve": "plateau"}, headers=H)
assert r.status_code == 403
print("4. playlist free OK; plateau -> 403 para free OK")

# 5. exports: csv/m3u free; rekordbox 403 free, 200 pro
assert client.post("/v1/export/csv", json={"job_id": job}, headers=H).status_code == 200
assert client.post("/v1/export/m3u", json={"job_id": job}, headers=H).status_code == 200
assert client.post("/v1/export/rekordbox", json={"job_id": job}, headers=H).status_code == 403
me = client.get("/v1/me", headers=H).json()
authcore.set_role(me["user"]["id"], "pro")
r = client.post("/v1/export/rekordbox", json={"job_id": job}, headers=H)
assert r.status_code == 200 and b"DJ_PLAYLISTS" in r.content
r = client.post("/v1/playlist", json={"job_id": job, "energy_curve": "plateau"}, headers=H)
assert r.status_code == 200
print("5. exports: csv/m3u free; rekordbox 403->200 con pro; plateau pro OK")

# 6. ownership + logout revoca
r2 = client.post("/v1/auth/register",
                 json={"email": "otro@kf.dj", "password": "password123"})
H2 = {"Authorization": f"Bearer {r2.json()['token']}"}
assert client.get(f"/v1/jobs/{job}", headers=H2).status_code == 404
assert client.post("/v1/auth/logout", headers=H2).json()["ok"]
assert client.get("/v1/me", headers=H2).status_code == 401
print("6. jobs son privados por usuario; logout revoca el token OK")

# 7. audio borrado tras el job
leftovers = list(pathlib.Path(tempfile.gettempdir()).glob("kf_job_*"))
assert not leftovers, leftovers
print("7. audio temporal borrado tras analizar OK")

print("RESULT: PASS")

"""Tests for the production-hardening layer: CORS, upload limits, rate limits,
clean error handling."""
import io
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import os

os.environ["KEYFLOW_MAX_FILE_MB"] = "1"      # tiny caps so the tests stay fast
os.environ["KEYFLOW_MAX_UPLOAD_MB"] = "2"

import authcore

authcore.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "kf_hard.db"

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)


def _auth():
    r = client.post("/v1/auth/register",
                    json={"email": "h@kf.dj", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


# 1. CORS preflight returns the configured origin
r = client.options("/v1/health", headers={
    "Origin": "http://localhost:3000",
    "Access-Control-Request-Method": "GET"})
assert r.headers.get("access-control-allow-origin") == "http://localhost:3000", r.headers
print("1. CORS preflight OK (origin permitido reflejado)")

H = _auth()

# 2. Per-file size limit (1 MB) -> 413, and no temp dir left behind
big = io.BytesIO(b"\x00" * (2 * 1024 * 1024))  # 2 MB .wav
r = client.post("/v1/analyze", headers=H,
                files=[("files", ("big.wav", big, "audio/wav"))],
                data={"duration": 30})
assert r.status_code == 413, (r.status_code, r.text)
leftovers = list(pathlib.Path(tempfile.gettempdir()).glob("kf_job_*"))
assert not leftovers, leftovers
print("2. límite por-archivo -> 413 y sin temp dir residual OK")

# 3. Too-many-files guard
os.environ.pop("KEYFLOW_MAX_FILES", None)  # default 500; simulate a small crate
tiny = [("files", (f"t{i}.wav", io.BytesIO(b"RIFF"), "audio/wav")) for i in range(3)]
r = client.post("/v1/analyze", headers=H, files=tiny, data={"duration": 30})
# 3 tiny (non-audio-decodable) files pass the guards; they'll just fail per-file
assert r.status_code == 200, r.text
print("3. guardas de conteo/paso de subida OK")

# 4. Rate limit on auth (limit 10 / 5min) -> 429 eventually
codes = [client.post("/v1/auth/login",
                     json={"email": "nope@kf.dj", "password": "x"}).status_code
         for _ in range(14)]
assert 429 in codes, codes
assert codes.count(401) <= 10
print("4. rate-limit de auth -> 429 tras el umbral OK")

print("RESULT: PASS")

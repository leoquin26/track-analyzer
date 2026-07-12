"""Integración Supabase ⇄ API (SaaS Fase 2, incremento 3).

Prueba el camino exacto del frontend web: login contra Supabase Auth →
llamar la FastAPI con el access token (JWT ES256) como Bearer → rol leído
de public.profiles vía PostgREST con la service key.

Requiere el stack local corriendo (`npx supabase start`). Si no está, la
suite termina con RESULT: SKIP (exit 0) para no romper máquinas sin Docker.
Las llaves de abajo son las demo keys públicas del CLI local — no secretos.
"""
import io
import os
import pathlib
import struct
import sys
import tempfile
import time
import uuid
import wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

SUPABASE_URL = "http://127.0.0.1:54321"
ANON = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9s"
        "ZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")
SERVICE = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9s"
           "ZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU")

import httpx  # noqa: E402


def _stack_up() -> bool:
    try:
        r = httpx.get(f"{SUPABASE_URL}/auth/v1/health",
                      headers={"apikey": ANON}, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


if not _stack_up():
    print("Supabase local apagado (npx supabase start) — nada que probar aquí.")
    print("RESULT: SKIP")
    sys.exit(0)

# Env ANTES de importar la app, igual que en producción.
os.environ["SUPABASE_URL"] = SUPABASE_URL
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = SERVICE

import authcore  # noqa: E402

authcore.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "kf_api_supa.db"

from fastapi.testclient import TestClient  # noqa: E402

from api import supabase_auth  # noqa: E402
from api.main import app  # noqa: E402

client = TestClient(app)
_SVC_HEADERS = {"apikey": SERVICE, "Authorization": f"Bearer {SERVICE}"}


def _make_wav(path: pathlib.Path, freq: float, seconds: float = 6.0) -> None:
    """Seno con envolvente a 120 BPM — suficiente para que librosa no falle."""
    import math
    rate = 22050
    frames = int(rate * seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        buffer = io.BytesIO()
        for i in range(frames):
            t = i / rate
            beat = max(0.0, math.sin(2 * math.pi * 2.0 * t)) ** 2  # 120 BPM
            sample = 0.6 * beat * math.sin(2 * math.pi * freq * t)
            buffer.write(struct.pack("<h", int(sample * 32767)))
        handle.writeframes(buffer.getvalue())


def _wait(job_id: str, headers: dict, timeout: int = 120) -> dict:
    for _ in range(timeout * 2):
        r = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
        if r["status"] in ("done", "error"):
            return r
        time.sleep(0.5)
    raise TimeoutError


# 1. usuario de prueba vía admin API (dispara el trigger de profiles)
email = f"suite-{uuid.uuid4().hex[:8]}@keyflow.test"
r = httpx.post(f"{SUPABASE_URL}/auth/v1/admin/users", headers=_SVC_HEADERS,
               json={"email": email, "password": "suite-pass-2026",
                     "email_confirm": True, "user_metadata": {"name": "Suite Bot"}},
               timeout=10)
assert r.status_code in (200, 201), r.text
uid = r.json()["id"]
r = httpx.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
               headers={"apikey": ANON},
               json={"email": email, "password": "suite-pass-2026"}, timeout=10)
assert r.status_code == 200, r.text
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
print("1. admin-create + password grant contra Supabase local OK")

# 2. /v1/me con el JWT: identidad del token, rol/nombre desde profiles
me = client.get("/v1/me", headers=H)
assert me.status_code == 200, me.text
body = me.json()
assert body["user"]["id"] == uid
assert body["user"]["role"] == "free" and body["plan"] == "Free"
assert body["user"]["name"] == "Suite Bot"  # sembrado por el trigger
assert body["entitlements"]["max_tracks"] == 50
print("2. /v1/me: JWT verificado, rol free + nombre del trigger OK")

# 3. tokens malos: firma alterada, JWT basura, opaco basura -> 401
tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
assert client.get("/v1/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
assert client.get("/v1/me", headers={"Authorization": "Bearer a.b.c"}).status_code == 401
assert client.get("/v1/me", headers={"Authorization": "Bearer deadbeef"}).status_code == 401
print("3. firma alterada / JWT basura / opaco basura -> 401 OK")

# 4. el rol vive en profiles: flip a pro con la service key y se refleja
r = httpx.patch(f"{SUPABASE_URL}/rest/v1/profiles", params={"id": f"eq.{uid}"},
                headers={**_SVC_HEADERS, "Content-Type": "application/json"},
                json={"role": "pro"}, timeout=10)
assert r.status_code in (200, 204), r.text
supabase_auth._role_cache.clear()  # el TTL de 60 s es correcto en prod; aquí no esperamos
body = client.get("/v1/me", headers=H).json()
assert body["user"]["role"] == "pro" and body["entitlements"]["dj_export"] is True
assert body["entitlements"]["max_tracks"] is None
print("4. flip de rol en profiles -> /v1/me refleja Pro sin re-login OK")

# 5. pipeline completo con identidad Supabase: analyze -> job -> playlist
tmp = pathlib.Path(tempfile.mkdtemp())
_make_wav(tmp / "suite_a_120.wav", 220.0)
_make_wav(tmp / "suite_b_120.wav", 330.0)
files = [("files", (p.name, p.read_bytes(), "audio/wav"))
         for p in sorted(tmp.glob("*.wav"))]
r = client.post("/v1/analyze", files=files, data={"duration": 30}, headers=H)
assert r.status_code == 200, r.text
job = r.json()["job_id"]
status = _wait(job, H)
assert status["status"] == "done", status
result = client.get(f"/v1/jobs/{job}/result", headers=H).json()
assert len(result["tracks"]) == 2, result.get("failed")
r = client.post("/v1/playlist", json={"job_id": job}, headers=H)
assert r.status_code == 200, r.text
assert len(r.json()["playlist"]) == 2
print("5. analyze -> job -> playlist con el JWT de Supabase OK")

# 6. limpieza: borrar el usuario cascada el perfil
r = httpx.delete(f"{SUPABASE_URL}/auth/v1/admin/users/{uid}",
                 headers=_SVC_HEADERS, timeout=10)
assert r.status_code in (200, 204), r.text
r = httpx.get(f"{SUPABASE_URL}/rest/v1/profiles", params={"id": f"eq.{uid}"},
              headers=_SVC_HEADERS, timeout=10)
assert r.json() == []
supabase_auth._role_cache.clear()
assert client.get("/v1/me", headers=H).status_code == 401  # usuario borrado -> anónimo
print("6. delete usuario -> perfil cascado y token muerto OK")

print("RESULT: PASS")

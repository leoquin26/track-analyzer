# Track Analyzer — Roadmap de "código" a SaaS (100% web, nativo después)

**Modelo elegido:** producto **100% web** primero; una vez consolidado, **app nativa Windows/Mac** (vía Tauri, reutilizando el mismo frontend web). Consecuencia clave: en web **tú pagas el cómputo y el ancho de banda** de analizar audio, así que control de costos + un componente de **créditos/cuota** dejan de ser opcionales.

**Ventaja que ya tienes:** tu motor (`harmonic_playlist.py`, `dj_export.py`, `track_suggest.py`) **no importa Streamlit** — se porta directo a un backend FastAPI sin reescribir la lógica de análisis. El `CLAUDE.md` ya trata el motor como "impórtalo, no lo reimplementes"; eso paga ahora.

---

## 1. Diagnóstico: qué tienes vs. qué falta

**Ya construido y sólido**
- Motor de análisis puro (sin Streamlit): BPM, key, Camelot, `rhythm_vector`, `onset_rate`, energía; `run_analysis()` como único punto de orquestación; `build_playlist()` greedy con `energy_curve`.
- Export DJ (`dj_export.py`) y Discover (`track_suggest.py`) también engine-side, portables.
- Dashboard Streamlit (`dashboard.py` + `ui/`) — servirá como **prototipo/validación**, no como el SaaS final.
- Gating premium (`ui/premium.py`) con verificación de licencia que ya soporta campos de suscripción.

**Lo que falta para SaaS 100% web**
1. **Frontend web real** multi-tenant (no Streamlit): cuentas, marketing, responsive, base para Tauri.
2. **Backend API** que envuelva tu motor y procese análisis como *jobs* en la nube.
3. **Cobro recurrente + créditos** (compute es tu costo ahora).
4. **Almacenamiento y ciclo de vida del audio** (subir → analizar → borrar), + DB de features/sets por usuario.

---

## 2. La decisión técnica crítica: ¿dónde se extraen los features?

En web tienes dos caminos. Define tu costo a escala:

| | **A. Servidor (recomendado para MVP)** | **B. Navegador (WASM)** |
|---|---|---|
| Cómo | Sube audio → FastAPI + worker con tu motor librosa | Decodifica y extrae features en el browser (Web Audio + essentia.js/WASM) |
| Reúso de tu código | **Directo** (tu motor tal cual) | Requiere reimplementar el análisis en JS/WASM |
| Costo servidor | Cómputo + **ancho de banda de subida** (el driver real) | Casi cero (solo viaja el JSON de features) |
| Tiempo a lanzar | Rápido | Lento (proyecto de I+D) |
| Escala | Cara si crece | Barata |

**Estrategia recomendada (evolución en dos tiempos):**
- **MVP:** camino **A** — reutiliza tu motor Python detrás de FastAPI. Lanza rápido, controla costo con cuotas bajas y borrado de audio.
- **Escala + Nativo:** mueve la extracción al **navegador (B)**. Elimina ancho de banda y cómputo de servidor, y **prepara el terreno para la app nativa** (que analiza local por definición). Así, Tauri reutiliza el mismo frontend y el análisis local ya existe.

---

## 3. Arquitectura objetivo (100% web, MVP con análisis en servidor)

```
┌──────────────── Browser (Next.js) ────────────────┐
│  Marketing + App SPA                               │
│  Auth (Supabase/Clerk)                             │
│  Sube tracks (o carpeta) → llama API               │
│  Renderiza playlist/heatmap/Camelot (Plotly.js)    │
└───────────────┬───────────────────────────────────┘
                │ JWT + REST
┌───────────────▼───────────── Backend ─────────────┐
│  FastAPI (envuelve tu motor)                       │
│  Cola de jobs (RQ/Celery o serverless)             │
│  Worker: librosa analiza → features JSON           │
│  Object storage (Cloudflare R2) para audio TEMP    │
│    → se BORRA tras analizar (solo guardas features)│
│  Postgres: users, tracks(features), sets, overrides│
│  Billing webhook (Stripe/LemonSqueezy) + créditos  │
│  Discover: keys proxied server-side                │
└────────────────────────────────────────────────────┘
```

Reglas de diseño:
- **Borra el audio tras analizar**; guarda solo el JSON de features. Baja costo de storage y riesgo legal.
- **Caché por hash de contenido**: si un archivo (mismo hash) ya se analizó, reutiliza features → ahorro grande en tracks populares. (Cachea por hash del audio, no por nombre.)
- **Cap de duración** ya lo tienes (3/5 min); manténlo bajo por defecto para abaratar.
- **Pre-procesa en el navegador** antes de subir (decodificar → mono → downsample) para recortar ancho de banda incluso en el camino A.

---

## 4. Stack sugerido
- **Frontend:** Next.js (React) + Tailwind. Es el mismo que luego empaqueta **Tauri** para Win/Mac → tu inversión web no se tira.
- **Charts:** Plotly.js (ya usas Plotly en `ui/charts.py`, la lógica se traduce).
- **Backend:** FastAPI + tu motor actual. Cola: RQ (Redis) para empezar.
- **Auth + DB:** Supabase (Postgres + Auth + storage) o Clerk (auth) + Neon (Postgres).
- **Audio temp:** Cloudflare R2 (egress barato) o Supabase Storage.
- **Billing:** LemonSqueezy o Paddle (Merchant of Record: manejan IVA global, ideal si estás fuera de EE.UU.); Stripe cuando tengas entidad US.
- **Deploy:** Vercel (frontend) + Render/Fly.io/Railway (API + workers).

---

## 5. Cobro: suscripción **+ créditos** (obligatorio en web)

Con compute como tu costo, "ilimitado plano" es riesgoso — un DJ con 5.000 tracks te cuesta dinero real (sobre todo el **primer import**). Modelo mixto:

| Plan | Precio | Cuota de análisis | Extras |
|---|---|---|---|
| **Free** | $0 | ~25 tracks/mes | Orden básico, sin export |
| **Pro** | **$15/mes** o **$120/año** | ~500 tracks/mes | Exports DJ, sets por evento, sync, Discover |
| **Créditos extra** | packs (p.ej. $5 = 300 tracks) | — | Para el import inicial grande de biblioteca |

Notas:
- El **primer import** es el pico de costo. Ofrece un "bono de bienvenida" de créditos o un pack de import para no ahogar al usuario nuevo.
- El anual mejora retención y cash-flow.
- Considera **lifetime early-bird** limitado ($199) para capital inicial y fans — ciérralo pronto.
- Benchmark: te posicionas como **"Mixed In Key + AI set builder, en la nube"**.

---

## 6. Plan por fases

### Fase 0 — Validar en tu Streamlit actual (1–2 semanas)
- Hospeda el Streamlit que ya tienes (Streamlit Community Cloud) como **demo pública** y pon una **waitlist + pricing**.
- Convierte tu producto Gumroad en **membership** para cobrar a los primeros mientras construyes el web real.
- **Meta:** validar que DJs de tu red pagarían; recoger emails.

### Fase 1 — Backend API (2–4 semanas)
- Envuelve `run_analysis()` en **FastAPI**; endpoints: `POST /analyze` (job), `GET /jobs/{id}`, `POST /playlist`, `POST /export/{format}`.
- Cola de jobs + worker con tu motor. Object storage temporal + **borrado post-análisis** + **caché por hash**.
- Sin UI todavía: prueba con Postman/curl.

### Fase 2 — Frontend web + cuentas (3–6 semanas)
- Next.js: auth (Supabase/Clerk), subida de tracks, vista de playlist + charts (Plotly.js), editor de orden.
- Gating **Free vs Pro** + medidor de **créditos/cuota**.
- Persistencia: `users`, `tracks(features JSON)`, `sets`, `overrides` en Postgres.

### Fase 3 — Billing + features Pro (2–4 semanas)
- LemonSqueezy/Stripe: suscripción + packs de créditos + webhooks que actualizan entitlement.
- Generador de **sets por evento** (curvas de energía sobre tu `energy_curve` + duración objetivo).
- Discover como feature Pro; **sets compartibles** (link público) para viralidad.
- Onboarding de primer uso ("analiza esta carpeta demo → mira el aha").

### Fase 4 — Optimización de costo a escala (continuo)
- Mueve extracción de features al **navegador (WASM/essentia.js)** → mata ancho de banda y cómputo.
- Esto **habilita directamente la Fase 5**.

### Fase 5 — App nativa Win/Mac (cuando esté consolidado)
- **Tauri** envuelve el mismo frontend Next.js → binario nativo pequeño.
- En nativo, análisis **local** (acceso a filesystem, sin subir audio, sin costo para ti) — mejor margen y mejor UX (bibliotecas gigantes).
- Sync con la cuenta cloud para features/sets.

---

## 7. Riesgos y mitigaciones
- **Ancho de banda del import inicial** = tu mayor costo en web. Mitiga con pre-proceso en navegador, cap de duración, caché por hash y packs de crédito para el import.
- **Streamlit no es el producto final** — úsalo solo para validar; el SaaS real es Next.js + FastAPI (tu motor se reusa).
- **Precisión de key** — ya es aproximada; conserva el override manual (Inspector) y no lo vendas como perfecto.
- **Churn** — sin sync/valor recurrente cancelan tras el primer análisis; sets por evento + Discover + sync sostienen la suscripción.
- **Legal/audio** — solo analizas y borras; no redistribuyes audio.

---

## 8. Primeros pasos concretos en el código
1. **FastAPI wrapper** de `run_analysis()` (nuevo `api/main.py`) — reusa el motor tal cual.
2. **Job queue** (RQ + Redis) + worker que corre `analyze_track()` y guarda features.
3. **Storage temporal + borrado + caché por hash** del audio.
4. **Esquema Postgres** (users/tracks/sets/overrides) en Supabase.
5. **Next.js** con auth + subida + vista de playlist (portando `ui/charts.py` a Plotly.js).
6. **Billing** LemonSqueezy con cuota + créditos.

---

### Siguiente paso sugerido
Arrancar por la **Fase 1 (backend FastAPI)**, porque desbloquea todo lo demás y aprovecha que tu motor ya es portable. Puedo empezar ahora: (a) montar el **esqueleto FastAPI** que envuelve `run_analysis()` con endpoints y cola de jobs, (b) diseñar el **esquema de base de datos** completo, o (c) definir la **API contract** (endpoints + payloads) para que frontend y backend avancen en paralelo. Dime por dónde.

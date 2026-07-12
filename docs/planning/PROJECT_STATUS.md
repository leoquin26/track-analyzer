# Estado del proyecto y próximos pasos

> Léelo al abrir el repo. Resume la dirección del producto y qué sigue.
> Detalle completo en `docs/planning/track-analyzer-roadmap-saas.md`
> (negocio/arquitectura) y `docs/planning/track-analyzer-ui-plan.md` (UI).

## Dirección del producto
- Convertir el proyecto de **app local** a **SaaS de suscripción**, **100% web
  primero** y luego **app nativa Windows/Mac con Tauri** (reutilizando el mismo
  frontend web).
- El análisis (`harmonic_playlist.py`) corre en el servidor en el MVP web; a
  escala se mueve a extracción de features **en el navegador (WASM)** para matar
  costo de cómputo y ancho de banda, lo que además habilita la app nativa.
- Monetización: **suscripción + créditos** (compute es costo en web). Planes
  Free / Pro / Lifetime ya reflejados en la landing.
- Ventaja clave: el motor (`harmonic_playlist.py`, `dj_export.py`,
  `track_suggest.py`) **no importa Streamlit** → se porta directo a FastAPI.

## Hecho recientemente (SaaS Fase 2 — web)
- **Arrancó el frontend Next.js** en `web/` (Next 16 + React 19 + Tailwind v4 +
  TS). Sistema de diseño portado: Outfit/Inter/DM Mono (next/font), paleta
  warm-dark + menta/lavanda como tokens `@theme`, y la **rueda Camelot** como
  componente TSX. **Landing completa** portada del Streamlit (navbar píldora,
  hero, stats, capabilities, how-it-works, pricing, footer). Build de prod
  limpio, verificada en navegador. Correr: `cd web && npm run dev` (:3000).
- **Decisión de arquitectura** (spec `2026-07-11-...`): usar **Supabase Auth**
  (no nuestras sesiones authcore) — trae verificación de email, reset, sesiones
  SSR y social gratis; la FastAPI validará el JWT de Supabase y leerá el rol de
  una tabla `profiles`. Entitlements siguen siendo la fuente única.
- **Incremento 2 HECHO con Supabase LOCAL** (`npx supabase start`, Docker):
  migración `0001` (profiles con rol + trigger de signup + lockdown por
  columnas — el usuario NO puede auto-subirse el rol, verificado con 42501 —,
  sets con RLS owner, feature_cache service-only), clientes `@supabase/ssr`
  (browser/server), **`proxy.ts`** (Next 16 renombró middleware→proxy) con
  refresh de sesión + guardas de ruta, páginas `/login` `/signup` `/reset`,
  shell `/app` (server component: gate + nombre + plan desde profiles) y
  signout. **E2E verificado en navegador**: signup→trigger crea perfil free→
  /app muestra plan→rol a pro via SQL→UI refleja "unlimited"→signout→/app
  rebota a login. `web/.env.local` (gitignored) apunta al stack local.
- **Incremento 3 HECHO — el web analiza de verdad.** (a) `api/supabase_auth.py`:
  la FastAPI acepta el access token de Supabase como Bearer (dual auth en
  `current_user`: JWT con 2 puntos → Supabase, opaco → authcore). Verificación
  **offline** vía JWKS público (`/auth/v1/.well-known/jwks.json`, ES256 — lo
  que firma el stack actual; fallback HS256 con `SUPABASE_JWT_SECRET` para
  proyectos legacy). El rol NO se confía del token: se lee de `profiles` vía
  PostgREST con la service key (cache 60 s); perfil inexistente = cuenta
  borrada → 401 (revocación casi inmediata pese a JWTs stateless). Env:
  `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. (b) **Migración `0002`**:
  grants explícitos de tabla — descubrimos que el stack local NO auto-otorga
  select/insert/update/delete a los roles de API (solo llegaba Dxtm), así que
  el service_role no podía leer profiles (42501, fallback silencioso a free) y
  las políticas RLS de sets eran inutilizables. Con 0002: CRUD de sets como
  owner verificado, role sigue intocable para el usuario (42501). (c) Suite
  `tests/test_api_supabase.py` (PASS; SKIP limpio sin stack): admin-create →
  login → /v1/me, firmas alteradas 401, flip de rol reflejado sin re-login,
  pipeline analyze→job→playlist con el JWT, delete usuario → token muerto.
  Las suites previas siguen PASS. (d) **Módulo Analyze en el web**
  (`/app/analyze`): drag&drop + browse, límites del plan visibles, profundidad
  60/180/300 s, upload multipart a `/v1/analyze` con el token de Supabase,
  polling con barra (progress/total + cache hits), y al terminar: métricas del
  set, curva de energía SVG, tabla con chips Camelot (mismo mapeo de hue que
  la rueda), exports CSV/M3U libres y rekordbox/serato/traktor con candado
  "· Pro" → pricing para free. Errores con cara: 403 plan (CTA upgrade), 429,
  API caída. `web/lib/api.ts` (cliente tipado, `NEXT_PUBLIC_API_URL`),
  `WorkspaceNav` compartido, card Analyze del workspace ahora "Live".
  **E2E verificado en navegador con ambos roles** (pro: exports abiertos;
  free: hint de 50 tracks + candados; cache por hash: 2.º análisis instantáneo).
  Correr: API `SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... uvicorn
  api.main:app --port 8000` + `cd web && npm run dev`.
- **Para producción**: crear el proyecto Supabase cloud y poner sus llaves en
  `web/.env.local` / Vercel — el mismo código funciona sin cambios; correr
  `npx supabase db push` para aplicar **ambas** migraciones (0001+0002) al
  cloud y verificar con una lectura PostgREST usando la service key (la web
  lee como authenticated y no destapa huecos de grants del service_role).
- **Siguiente incremento (4)**: persistir sets en Supabase (`sets` ya tiene
  grants+RLS listos) + módulo Set builder en el web (reorder, start track,
  energy curve gated); luego Insights/Inspector/Discover.

## Hecho recientemente (API / producción)
- **Endurecimiento de la API para SaaS** (`api/main.py`): CORS con orígenes
  explícitos (`KEYFLOW_CORS_ORIGINS`, Bearer no cookies), **límites de upload**
  por-archivo/total/conteo con lectura en streaming (413 sin cargar en RAM),
  **rate limiting** por IP en auth (10/5min) y analyze (20/h), reaper de jobs
  huérfanos al arrancar (lifespan), y handler 500 que no filtra stack traces.
  Suites `tests/test_api.py` + `tests/test_api_hardening.py` (todas PASS).
- **Pendiente para el deploy SaaS**: SQLite→Postgres/Supabase (cuentas efímeras
  en cloud), storage de objetos (R2) para uploads grandes, worker durable
  (RQ/Redis), CSP para el token en cookie, email SMTP real, monitoreo (Sentry).

## Hecho recientemente (UI)
- **Límites de auth resueltos**: sesión persistente por cookie (`kf_session`,
  token hasheado en DB, TTL 30 días, escritura diferida al run siguiente para
  sobrevivir al `st.rerun`), reset de contraseña y verificación de email con
  códigos de un solo uso vía SMTP (`ui/mailer.py`, secrets `smtp_*`; degrada
  con mensaje claro si no está configurado). Verificado en navegador: login →
  refresh duro → sigue dentro.
- **Cuentas + roles free/pro/lifetime** (`ui/auth.py`): registro/login (SQLite
  local + scrypt), gate de login en el analyzer, módulo Account (perfil, plan,
  upgrade, vincular licencia Gumroad → pro/lifetime, re-check semanal de Pro),
  y restricciones aplicadas: free = 50 tracks/análisis, sin plateau, sin
  Discover, sin exports DJ. `auth.ENTITLEMENTS` es la fuente única de límites.
  Migra a Supabase en Fase SaaS 2 (la superficie pública del módulo se mantiene).
- **Sistema visual v2 (suave/amigable)**: tipografía Outfit (display) + Inter
  (cuerpo) + DM Mono (datos); paleta dark cálida (#121016, tinta marfil) con
  acento menta #5eead4 y lavanda #a78bfa de apoyo (tema nativo en
  `.streamlit/config.toml`). Navbar de la landing como píldora flotante con
  blur; sidebar del analyzer agrupado por intención (Start/Build/Review/Ship)
  con ítem activo relleno + barra menta. Rampa del heatmap actualizada y paleta
  de series re-validada sobre el fondo nuevo.
- **Analyzer reestructurado como dashboard**: módulo **Overview** por defecto
  (bienvenida guiada + cards bloqueadas sin análisis; métricas + "What next?"
  con análisis), **Analyze** como módulo propio, y los demás módulos con gating
  y CTA. Navegación por `state.goto_module` (callback).
- **Pulido de diseño**: emojis eliminados de toda la UI (iconos SVG hairline en
  las feature cards), CTAs de pricing alineados a una línea base, botones ▲▼
  compactos, vocabulario unificado ("Open Keyflow →").
- **Rebranding a Keyflow** (dominio elegido: `keyflow.dj`, sin registrar aún;
  tagline "Sets that flow in key."). Marca aplicada en landing, analyzer,
  exports (rekordbox/Traktor/M3U), user-agent de Discover y README. La ruta de
  licencias `~/.track_analyzer/` se conserva por compatibilidad.
- **Paleta de charts validada** (dataviz: banda de luminosidad, CVD ΔE≥41,
  contraste ≥3:1 sobre `#08080b`) para los 5 componentes de transición; el teal
  de marca queda solo para acentos de UI y marcas de una sola serie.
- Rediseño **premium/minimalista**: `ui/styles.py` reescrito (tokens CSS, menos
  neón, botones "quiet luxury"); se conservaron todos los nombres de clase.
- `ui/pages/home.py` reconstruida con secciones SaaS: hero, banda de stats,
  **preview de producto**, posicionamiento vs key detectors, **pricing**.
- `ui/components.py`: onboarding con feedback de estado + copy de privacidad.
- Tras editar `ui/`, **reiniciar Streamlit por completo** (cachea submódulos).

## Próximos pasos (orden sugerido)
1. ~~Conectar CTAs de pricing a checkout real~~ **HECHO en código**: Pro y
   Lifetime usan `st.link_button` hacia `gumroad_product_url` /
   `gumroad_lifetime_url` (secrets o env `TA_GUMROAD_*_URL`) con fallback al
   analyzer si no están configuradas. **Falta (lado usuario):** crear el
   producto *membership* (Pro) y el producto Lifetime en Gumroad y poner las
   dos URLs en `.streamlit/secrets.toml`.
2. Estados de carga/vacío del analyzer + QA responsive móvil + accesibilidad AA.
3. ~~Fase SaaS 1 — Backend FastAPI~~ **HECHO (MVP)**: `api/main.py` con
   `POST /v1/auth/register|login`, `/v1/me`, `POST /v1/analyze` (multipart →
   job en background), `GET /v1/jobs/{id}[/result]`, `POST /v1/playlist`,
   `POST /v1/export/{fmt}`. Auth compartida con la UI vía `authcore.py`
   (mismos tokens revocables → un login sirve en ambas superficies), límites
   de plan aplicados server-side (free: 50 tracks, sin plateau, sin exports
   DJ), **caché por hash de contenido** y **borrado del audio post-análisis**.
   Worker in-process (ThreadPool) con tabla `jobs` — contrato listo para
   migrar a RQ/Redis. Suite e2e en `tests/test_api.py`. Correr:
   `uvicorn api.main:app --port 8000`. Pendiente de la fase: Postgres/Supabase
   y storage de objetos cuando se despliegue.
4. Fase SaaS 2 — Frontend Next.js + auth (Supabase) + persistencia + gating
   Free/Pro. Portar los design tokens y componentes de la landing actual.
5. Fase SaaS 3 — Billing (LemonSqueezy/Paddle como Merchant of Record) con
   suscripción + créditos.

## Notas
- Cobro recurrente ya es posible casi sin código: `ui/premium.py` ya maneja los
  campos de suscripción de Gumroad; basta convertir el producto en *membership*.
- No romper la separación motor/UI: el motor se importa, no se reimplementa.

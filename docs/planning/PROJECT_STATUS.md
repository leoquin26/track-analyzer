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

## Hecho recientemente (UI)
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
3. **Fase SaaS 1 — Backend FastAPI** que envuelve `run_analysis()` con cola de
   jobs, storage temporal de audio con borrado, y caché por hash.
4. Fase SaaS 2 — Frontend Next.js + auth (Supabase) + persistencia + gating
   Free/Pro. Portar los design tokens y componentes de la landing actual.
5. Fase SaaS 3 — Billing (LemonSqueezy/Paddle como Merchant of Record) con
   suscripción + créditos.

## Notas
- Cobro recurrente ya es posible casi sin código: `ui/premium.py` ya maneja los
  campos de suscripción de Gumroad; basta convertir el producto en *membership*.
- No romper la separación motor/UI: el motor se importa, no se reimplementa.

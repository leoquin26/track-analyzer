# Track Analyzer — Rediseño UI (premium/minimal) + plan de desarrollo

Dirección aplicada: **premium / minimalista**. Se conserva el ADN (teal como
único acento, rueda Camelot como firma, fuentes Syne/Space Grotesk/JetBrains
Mono) pero se baja el neón, se mete aire y la tipografía lleva la jerarquía.

---

## 1. Qué se implementó en esta ronda

**Sistema de estilos — `ui/styles.py` (reescrito)**
- Nueva paleta con tokens CSS (`--bg`, `--ink`, `--muted`, `--faint`, `--line`,
  `--surface`): near-black plano, bordes hairline, superficies casi planas.
- Fondo calmado: un solo radial teal muy tenue en vez de los dos washes intensos.
- Botones premium *kind-aware*: primario = relleno claro con tinta oscura
  (look "producto caro"); secundarios/descarga/link = hairline discreto.
- Menos glow y menos texto en degradado; el énfasis del hero es teal sólido.
- Se conservan **todos** los nombres de clase que usan `home.py`, `analyzer.py`
  y `components.py`, así que nada se rompe.
- Clases nuevas para la landing: `lp-stats`, `preview-frame`/`pv-*`,
  `price-*`, `compare`, `lp-lead`, `lp-center`.

**Landing — `ui/pages/home.py` (reconstruida)**
- Navbar con enlace a **Pricing**.
- Hero refinado (eyebrow con acento, subtítulo más aireado, nota de privacidad).
- **Banda de stats** (24 keys · 5 señales · 0 uploads · ∞ librería).
- **Preview del producto**: mock de ventana con playlist + sparkline de energía
  + keys en el set (prueba visual sin necesitar screenshot todavía).
- Capabilities (4 señales) y How-it-works (3 pasos) pulidos.
- **Posicionamiento** "más que un key detector": columna *ellos* vs *nosotros*.
- **Pricing**: Free / Pro (destacado) / Lifetime, con CTAs.
- Footer CTA.

**Analyzer — `ui/components.py`**
- Copy de setup más claro sobre privacidad/local.
- **Feedback de onboarding**: mensajes distintos según haya carpeta válida,
  carpeta sin audios (sugiere subcarpetas), o nada seleccionado.
- Todo el resto del analyzer (chips, playlist cards, inspector, wheel, badges)
  hereda el nuevo look premium vía CSS, sin cambios estructurales de riesgo.

**Verificación**
- Compilación de sintaxis confirmada (Python 3.10) para los patrones f-string de
  CSS y los builders de la preview. Los archivos sin tocar siguen compilando.
- Nota: reinicia Streamlit por completo para ver los cambios (Streamlit cachea
  submódulos en proceso; tu `CLAUDE.md` ya lo advierte).

Cómo verlo:
```bash
python -m streamlit run dashboard.py   # o run_dashboard.bat en Windows
```

---

## 2. Pendientes inmediatos (cerrar esta capa de UI)

1. **Conectar los CTAs de Pricing a checkout real.** Hoy todos abren el analyzer.
   El card Pro debería ir al checkout (Gumroad membership) y Lifetime a su
   producto. Reusar `ui/premium.product_url()` o pasar links por `st.secrets`.
2. **Reemplazar el mock de preview por un screenshot real** del analyzer cuando
   tengas uno limpio (el mock es buen placeholder, pero una captura real convierte
   mejor). Mantener el mock como fallback.
3. **Estados de carga y vacío del analyzer.** Añadir un skeleton/placeholder
   mientras analiza y un empty-state más rico cuando una carpeta no tiene audio.
4. **QA responsive real** en móvil (≤640px): navbar, hero, pricing en 1 columna,
   preview apilado. Ya hay media queries; falta probar en dispositivo.
5. **Accesibilidad:** contraste de `--muted`/`--faint` sobre el fondo (apuntar a
   WCAG AA), foco visible en botones/inputs, `aria-label` en la rueda (ya existe)
   y en el mock de preview.

## 3. Roadmap UI/UX (siguiente fase)

1. **Design tokens como fuente única.** Extraer la paleta/tipografía a un archivo
   de tokens (`tokens.json` o variables CSS) para que la futura app web (Next.js)
   y la de escritorio (Tauri) reusen exactamente el mismo lenguaje visual.
2. **Onboarding guiado de primer uso**: tour de 3 pasos la primera vez, carpeta
   de demo incluida ("prueba con estos tracks") para el momento *aha* sin fricción.
3. **Componentización con miras a la web.** Al portar a Next.js (ver roadmap SaaS),
   convertir estas secciones en componentes React reutilizables: `<PriceCard>`,
   `<FeatureCard>`, `<SetPreview>`, `<CamelotWheel>`. El CSS actual ya está
   ordenado por bloques, lo que facilita el port.
4. **Modo claro opcional** (premium suele ofrecer ambos) usando los mismos tokens.
5. **Microinteracciones con criterio**: hover/transiciones ya suaves; añadir
   estados de éxito (set generado), toasts consistentes y foco de teclado.
6. **Landing → conversión**: sección de testimonios/social proof cuando tengas
   primeros usuarios, FAQ de pricing, y comparativa explícita vs Mixed In Key.

## 4. Cómo encaja con el plan SaaS (web-first)

- Esta capa visual es la **base de diseño** que se porta tal cual a Next.js en la
  Fase 2 del roadmap SaaS (`track-analyzer-roadmap-saas.md`). No es trabajo
  desechable: los tokens, la landing y los componentes se reusan.
- El **pricing** que se agregó a la landing es el que alimenta la Fase 3 (billing
  con créditos/suscripción). Deja los planes y copy ya validados aquí.
- El **mock de preview** se sustituye por el producto real embebido cuando exista
  el frontend web.

---

### Archivos tocados
- `ui/styles.py` — reescrito (premium/minimal + clases nuevas)
- `ui/pages/home.py` — reconstruido (secciones SaaS)
- `ui/components.py` — copy + feedback de onboarding

### Siguiente paso sugerido
Cerrar el punto 2.1 (CTAs de pricing → checkout real) para que la landing sea
funcional de punta a punta, y luego decidir si seguimos puliendo Streamlit o
arrancamos el port a Next.js de la Fase 2 del roadmap SaaS.

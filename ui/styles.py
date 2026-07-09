"""Theme constants and the injected CSS for the dashboard.

Design language: premium / minimal. Teal is used sparingly as a single accent;
surfaces are near-flat with hairline borders; typography (Syne display, Space
Grotesk UI, JetBrains Mono meta) carries the hierarchy instead of neon glow.
All class names referenced by the pages/components are preserved.
"""

from __future__ import annotations

APP_TITLE = "Keyflow"
TAGLINE = "Sets that flow in key."
DOMAIN = "keyflow.dj"
ACCENT = "#00f5d4"
ACCENT_2 = "#9b5de5"
SURFACE = "#12121a"
SURFACE_2 = "#1a1a27"

# Categorical series colors for the transition-component charts.
# Validated (dataviz six checks, dark surface #08080b): lightness band,
# chroma floor, adjacent-pair CVD ΔE ≥ 41, contrast ≥ 3:1. Brand teal stays
# reserved for UI accents and single-series marks (energy curve, wheel).
COMPONENT_COLORS = {
    "harmonic": "#9085e9",
    "bpm": "#199e70",
    "rhythm": "#c98500",
    "onset": "#d55181",
    "energy": "#3987e5",
}


# --------------------------------------------------------------------------- #
# Global app CSS (injected on every page by dashboard.py)
# --------------------------------------------------------------------------- #
CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        --accent: {ACCENT};
        --accent-2: {ACCENT_2};
        --bg: #08080b;
        --ink: #f5f5f7;
        --muted: rgba(245,245,247,0.58);
        --faint: rgba(245,245,247,0.40);
        --line: rgba(255,255,255,0.08);
        --line-soft: rgba(255,255,255,0.05);
        --surface: rgba(255,255,255,0.025);
        --surface-2: rgba(255,255,255,0.04);
    }}

    .stApp {{
        background:
            radial-gradient(1100px 520px at 50% -280px, rgba(0,245,212,0.06), transparent 70%),
            var(--bg);
        font-family: 'Space Grotesk', sans-serif;
        color: var(--ink);
    }}

    [data-testid="stMainBlockContainer"], .block-container {{
        max-width: 1200px !important;
    }}

    /* App rail — Linear-style cool dark grey, never pure black */
    [data-testid="stSidebar"] {{
        background: #0d0d12;
        border-right: 1px solid var(--line);
        min-width: 252px !important; max-width: 252px !important;
    }}
    [data-testid="stSidebar"] .block-container {{ padding: 1.2rem 0.8rem; }}
    [data-testid="stSidebar"] div[data-testid="stButton"] > button,
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="secondary"] {{
        justify-content: flex-start;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: var(--muted);
        font-weight: 500;
        padding: 0.42rem 0.85rem;
        min-height: 2.2rem;
        transition: color .18s ease, background .18s ease, padding-left .18s ease;
    }}
    [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
        color: var(--ink);
        background: var(--surface-2) !important;
        padding-left: 1.05rem;
    }}
    .sb-brand {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.12rem;
        color: var(--ink); letter-spacing: -0.02em;
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.2rem 0.85rem 0.9rem;
    }}
    .sb-brand .disc {{
        width: 0.95rem; height: 0.95rem; border-radius: 50%;
        background: conic-gradient(from 0deg, var(--accent), var(--accent-2), #f15bb5, #fee440, var(--accent));
    }}
    .sb-section {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
        letter-spacing: 0.22em; text-transform: uppercase; color: var(--faint);
        padding: 0.9rem 0.85rem 0.35rem;
    }}
    .sb-status {{
        margin: 0.9rem 0.4rem 0.4rem; padding: 0.7rem 0.8rem;
        border: 1px solid var(--line); border-radius: 12px; background: var(--surface);
        font-size: 0.78rem; color: var(--muted); line-height: 1.5;
    }}
    .sb-status b {{ color: var(--accent); font-family: 'JetBrains Mono', monospace; }}

    /* Page header inside the app shell */
    .pg-title {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.7rem;
        color: var(--ink); letter-spacing: -0.025em; margin: 0 0 0.15rem;
        animation: rise .35s ease both;
    }}
    .pg-desc {{ color: var(--muted); margin: 0 0 1.2rem; animation: rise .4s ease both; }}

    /* ------- Motion layer: purposeful, 200–450ms, reduced-motion aware ------- */
    @keyframes rise {{
        from {{ opacity: 0; transform: translateY(9px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .metric-card, .feature-card, .price-card, .lp-step, .lp-stat,
    [data-testid="stVerticalBlockBorderWrapper"] {{
        animation: rise .42s cubic-bezier(.22,.9,.35,1) both;
    }}
    div[data-testid="column"]:nth-of-type(2) .metric-card,
    div[data-testid="column"]:nth-of-type(2) .feature-card,
    div[data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"] {{ animation-delay: .06s; }}
    div[data-testid="column"]:nth-of-type(3) .metric-card,
    div[data-testid="column"]:nth-of-type(3) .feature-card,
    div[data-testid="column"]:nth-of-type(3) [data-testid="stVerticalBlockBorderWrapper"] {{ animation-delay: .12s; }}
    div[data-testid="column"]:nth-of-type(4) .metric-card,
    div[data-testid="column"]:nth-of-type(4) .feature-card,
    div[data-testid="column"]:nth-of-type(4) [data-testid="stVerticalBlockBorderWrapper"] {{ animation-delay: .18s; }}

    .metric-card {{ transition: transform .2s ease, border-color .2s ease; }}
    .metric-card:hover {{ transform: translateY(-2px); border-color: rgba(0,245,212,0.3); }}

    /* Sparkline draw-in */
    .spark-line {{
        stroke-dasharray: 520; stroke-dashoffset: 520;
        animation: spark-draw 1s cubic-bezier(.3,.8,.3,1) .15s forwards;
    }}
    @keyframes spark-draw {{ to {{ stroke-dashoffset: 0; }} }}

    @media (prefers-reduced-motion: reduce) {{
        .metric-card, .feature-card, .price-card, .lp-step, .lp-stat, .pg-title, .pg-desc,
        [data-testid="stVerticalBlockBorderWrapper"] {{ animation: none; }}
        .spark-line {{ animation: none; stroke-dashoffset: 0; }}
    }}

    /* Buttons: premium, kind-aware */
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stLinkButton"] > a {{
        border-radius: 11px;
        font-weight: 600;
        letter-spacing: -0.01em;
        transition: background .16s ease, border-color .16s ease, color .16s ease, transform .16s ease;
    }}
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: var(--ink);
        color: #0a0a0e;
        border: 1px solid var(--ink);
    }}
    div[data-testid="stButton"] > button[kind="primary"]:hover {{
        background: #ffffff;
        border-color: #ffffff;
        color: #08080b;
        transform: translateY(-1px);
    }}
    div[data-testid="stButton"] > button[kind="secondary"],
    div[data-testid="stDownloadButton"] > button,
    div[data-testid="stLinkButton"] > a {{
        background: var(--surface-2);
        border: 1px solid var(--line);
        color: var(--ink);
    }}
    div[data-testid="stButton"] > button[kind="secondary"]:hover,
    div[data-testid="stDownloadButton"] > button:hover,
    div[data-testid="stLinkButton"] > a:hover {{
        border-color: rgba(0,245,212,0.45);
        color: #fff;
    }}

    .stTextInput input, .stNumberInput input {{
        border-radius: 11px;
        background: var(--surface);
        border: 1px solid var(--line);
        color: var(--ink);
        font-family: 'JetBrains Mono', monospace;
    }}
    .stTextInput input:focus, .stNumberInput input:focus {{
        border-color: rgba(0,245,212,0.45);
        box-shadow: none;
    }}

    .hero {{ padding: 0.25rem 0 1.5rem 0; }}
    .hero h1 {{
        font-family: 'Syne', sans-serif;
        font-size: 2.6rem; font-weight: 800; margin: 0;
        color: var(--ink); letter-spacing: -0.03em;
    }}
    .hero p {{ color: var(--muted); font-size: 1.05rem; margin: 0.5rem 0 0 0; max-width: 52rem; }}

    .metric-card {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        min-height: 108px;
    }}
    .metric-label {{
        color: var(--faint); font-size: 0.74rem;
        text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 0.4rem;
    }}
    .metric-value {{ color: var(--ink); font-size: 1.85rem; font-weight: 700; line-height: 1.1; }}
    .metric-sub {{ color: var(--accent); font-size: 0.85rem; margin-top: 0.35rem; font-family: 'JetBrains Mono', monospace; }}

    .playlist-card {{
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.35rem;
        transition: border-color 0.16s ease, background 0.16s ease;
    }}
    .playlist-card:hover {{ border-color: rgba(0,245,212,0.3); background: var(--surface-2); }}
    .playlist-order {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 2.1rem; height: 2.1rem; border-radius: 999px;
        background: var(--surface-2); border: 1px solid var(--line);
        color: var(--accent); font-weight: 700; font-size: 0.9rem;
        margin-right: 0.85rem; flex-shrink: 0;
        font-family: 'JetBrains Mono', monospace;
    }}
    .playlist-title {{ color: var(--ink); font-size: 1.02rem; font-weight: 600; margin: 0; }}
    .playlist-meta {{ color: var(--muted); font-size: 0.84rem; margin-top: 0.28rem; font-family: 'JetBrains Mono', monospace; }}

    .camelot-pill {{
        display: inline-block; padding: 0.14rem 0.55rem; border-radius: 999px;
        font-size: 0.76rem; font-weight: 600; margin-right: 0.45rem;
        font-family: 'JetBrains Mono', monospace;
    }}
    .camelot-a {{ background: rgba(155,93,229,0.16); color: #d8b4fe; border: 1px solid rgba(155,93,229,0.3); }}
    .camelot-b {{ background: rgba(0,245,212,0.14); color: #7fffe8; border: 1px solid rgba(0,245,212,0.3); }}

    .score-pill {{
        display: inline-block; margin-top: 0.45rem; padding: 0.2rem 0.55rem;
        border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--muted);
        font-size: 0.76rem; font-family: 'JetBrains Mono', monospace;
    }}
    .score-pill.warn {{ color: #ffb4a2; background: rgba(241,91,91,0.1); }}
    .score-pill.good {{ color: #7fffe8; background: rgba(0,245,212,0.1); }}

    .score-pill[title], .chip[title], .ic[title], .mix-card[title], .camelot-pill[title] {{ cursor: help; }}

    .st-key-an_module {{ margin: 0.7rem 0 0.4rem; border-bottom: 1px solid var(--line); }}
    .st-key-an_module button {{
        background: transparent !important; border: none !important; border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        font-size: 0.96rem !important; padding: 0.6rem 1.1rem !important; font-weight: 600;
        color: var(--faint) !important; box-shadow: none !important;
    }}
    .st-key-an_module button:hover {{ color: #fff !important; }}
    .st-key-an_module button[kind="segmented_controlActive"],
    .st-key-an_module button[aria-checked="true"] {{
        color: var(--ink) !important; border-bottom: 2px solid var(--accent) !important;
    }}

    .setup-steps {{
        display: flex; flex-wrap: wrap; gap: 2rem; margin: 0.3rem 0 1.2rem;
        font-size: 0.86rem; color: var(--muted);
    }}
    .setup-steps b {{
        font-family: 'Syne', sans-serif; font-size: 1.02rem; color: var(--accent);
        margin-right: 0.4rem;
    }}

    .bar-label {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.66rem;
        letter-spacing: 0.26em; text-transform: uppercase; color: var(--faint); margin-bottom: 0.15rem;
    }}
    .module-desc {{ color: var(--muted); font-size: 0.88rem; margin: 0.2rem 0 1rem; }}

    .disc-card {{
        display: flex; align-items: center; gap: 0.8rem; padding: 0.85rem 1rem;
        margin-bottom: 0.6rem; border-radius: 14px;
        background: var(--surface); border: 1px solid var(--line);
        transition: border-color .16s ease;
    }}
    .disc-card:hover {{ border-color: rgba(0,245,212,0.28); }}
    .disc-card .t {{ color: var(--ink); font-size: 0.95rem; font-weight: 600; }}
    .disc-card .a {{ color: var(--muted); font-size: 0.85rem; }}
    .disc-card .grow {{ flex: 1; min-width: 0; }}
    .disc-card .src {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
        padding: 0.15rem 0.5rem; border-radius: 999px;
        border: 1px solid var(--line); color: var(--muted);
    }}
    .disc-card a {{ color: var(--accent); text-decoration: none; font-size: 0.85rem; }}
    .disc-chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
        padding: 0.2rem 0.55rem; border-radius: 8px;
        background: rgba(255,255,255,0.04); border: 1px solid var(--line); color: var(--muted);
        white-space: nowrap;
    }}
    .disc-chip.good {{ color: #7fffe8; background: rgba(0,245,212,0.1); }}
    .disc-chip.warn {{ color: #ffb4a2; background: rgba(241,91,91,0.1); }}

    .empty-state {{
        text-align: center; padding: 3.5rem 1.5rem;
        border: 1px dashed var(--line); border-radius: 20px; background: var(--surface);
    }}
    .empty-state h3 {{ color: var(--ink); margin-bottom: 0.5rem; }}
    .empty-state p {{ color: var(--muted); margin: 0; }}

    .section-title {{
        color: var(--ink); font-size: 1.15rem; font-weight: 600;
        margin: 1.5rem 0 0.75rem 0; letter-spacing: -0.02em;
    }}
    .section-hint {{ color: var(--muted); font-size: 0.85rem; margin: -0.4rem 0 0.75rem 0; }}

    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stHeaderActionElements"] {{ display: none; }}

    .app-brand {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.12rem;
        letter-spacing: -0.02em; color: var(--ink);
        display: flex; align-items: center; gap: 0.55rem;
    }}
    .app-brand .disc {{
        width: 1.0rem; height: 1.0rem; border-radius: 50%;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
    }}
    .app-brand .crumb {{
        color: var(--faint); font-weight: 400; font-size: 0.9rem;
        font-family: 'JetBrains Mono', monospace; margin-left: 0.35rem;
    }}
    .app-header-rule {{
        height: 1px; border: 0; margin: 0.5rem 0 1.3rem; background: var(--line);
    }}
    .st-key-nav_home button {{
        background: transparent !important; border: none !important;
        color: var(--muted) !important; font-weight: 500;
    }}
    .st-key-nav_home button:hover {{ color: var(--accent) !important; box-shadow: none !important; }}

    .stTabs [data-baseweb="tab-highlight"] {{ background-color: var(--accent); }}
    .stTabs button[aria-selected="true"] {{ color: var(--ink) !important; }}
</style>
"""


# --------------------------------------------------------------------------- #
# Landing-page CSS (injected only by home.py)
# --------------------------------------------------------------------------- #
HOME_CSS = f"""
<style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"] {{ display: none !important; }}
    [data-testid="stMainBlockContainer"], .block-container {{
        max-width: 1120px !important; padding-top: 1.4rem !important;
    }}

    .lp-brand {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.18rem;
        letter-spacing: -0.02em; color: var(--ink);
        display: flex; align-items: center; gap: 0.55rem; padding-top: 0.55rem;
    }}
    .lp-brand .disc {{
        width: 1.1rem; height: 1.1rem; border-radius: 50%;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
    }}
    .lp-links {{
        display: flex; justify-content: flex-end; align-items: center; gap: 1.9rem;
        height: 100%; padding-top: 0.7rem;
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; letter-spacing: 0.04em;
    }}
    .lp-links a {{ color: var(--muted); text-decoration: none; transition: color 0.15s ease; }}
    .lp-links a:hover {{ color: var(--accent); }}

    .lp-eyebrow {{
        display: inline-block; font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem; letter-spacing: 0.28em; text-transform: uppercase; color: var(--muted);
        padding: 0.35rem 0.85rem; border-radius: 999px;
        border: 1px solid var(--line); background: var(--surface);
    }}
    .lp-eyebrow b {{ color: var(--accent); font-weight: 500; }}
    .lp-title {{
        font-family: 'Syne', sans-serif; font-weight: 800;
        font-size: clamp(3rem, 6vw, 5rem); line-height: 0.98;
        letter-spacing: -0.035em; margin: 1.3rem 0 0; color: var(--ink);
    }}
    .lp-title em {{ font-style: normal; color: var(--accent); }}
    .lp-sub {{
        color: var(--muted); font-size: 1.14rem; line-height: 1.6;
        max-width: 31rem; margin: 1.4rem 0 0; font-weight: 400;
    }}
    .lp-hero-note {{
        margin-top: 1.6rem; color: var(--faint);
        font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; letter-spacing: 0.03em;
    }}

    .wheel-wrap {{ position: relative; width: min(100%, 430px); aspect-ratio: 1; margin: 0 auto; }}
    .wheel-halo {{
        position: absolute; inset: 2%; border-radius: 50%; z-index: 0;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
        filter: blur(46px); opacity: 0.16; animation: spin 40s linear infinite;
    }}
    .wheel-svg {{ position: relative; z-index: 1; width: 100%; height: auto; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    .lp-stats {{
        display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
        border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
        padding: 1.6rem 0; margin: 0.5rem 0;
    }}
    .lp-stat {{ text-align: center; }}
    .lp-stat .n {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.9rem;
        color: var(--ink); letter-spacing: -0.02em;
    }}
    .lp-stat .l {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
        letter-spacing: 0.14em; text-transform: uppercase; color: var(--faint); margin-top: 0.25rem;
    }}

    .lp-specs {{ display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center; margin: 0.5rem 0; }}
    .lp-chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--muted);
        padding: 0.4rem 0.8rem; border-radius: 999px; border: 1px solid var(--line); background: var(--surface);
    }}
    .lp-chip b {{ color: var(--accent); font-weight: 500; }}

    .lp-kicker {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
        letter-spacing: 0.28em; text-transform: uppercase; color: var(--accent);
    }}
    .lp-h2 {{
        font-family: 'Syne', sans-serif; font-weight: 700;
        font-size: clamp(1.8rem, 3.2vw, 2.6rem); letter-spacing: -0.025em;
        color: var(--ink); margin: 0.45rem 0 0.2rem;
    }}
    .lp-lead {{ color: var(--muted); font-size: 1.02rem; max-width: 38rem; margin: 0.4rem 0 0; line-height: 1.6; }}

    .feature-card {{
        height: 100%; min-height: 252px;
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 18px; padding: 1.5rem 1.35rem;
        transition: transform 0.16s ease, border-color 0.16s ease;
    }}
    .feature-card:hover {{ transform: translateY(-3px); border-color: rgba(0,245,212,0.3); }}
    .feature-icon {{ color: var(--accent); }}
    .feature-icon svg {{ width: 26px; height: 26px; display: block; }}
    .feature-card h4 {{ color: var(--ink); margin: 0.7rem 0 0.4rem; font-size: 1.04rem; font-weight: 600; }}
    .feature-card p {{ color: var(--muted); font-size: 0.9rem; margin: 0; line-height: 1.55; }}

    .preview-frame {{
        border: 1px solid var(--line); border-radius: 18px; overflow: hidden;
        background: linear-gradient(180deg, #0c0c12, #0a0a10);
        box-shadow: 0 30px 80px -40px rgba(0,0,0,0.8);
    }}
    .preview-bar {{
        display: flex; align-items: center; gap: 0.4rem;
        padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--line); background: rgba(255,255,255,0.02);
    }}
    .preview-bar i {{ width: 0.6rem; height: 0.6rem; border-radius: 50%; display: inline-block; background: rgba(255,255,255,0.16); }}
    .preview-bar .u {{
        margin-left: 0.6rem; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--faint);
    }}
    .preview-body {{ display: grid; grid-template-columns: 1.3fr 1fr; gap: 1.1rem; padding: 1.2rem; }}
    .pv-rows {{ display: flex; flex-direction: column; gap: 0.5rem; }}
    .pv-row {{
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.55rem 0.7rem; border-radius: 11px;
        background: var(--surface); border: 1px solid var(--line-soft);
    }}
    .pv-row .o {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--accent);
        width: 1.1rem; text-align: center;
    }}
    .pv-row .nm {{ flex: 1; color: var(--ink); font-size: 0.82rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .pv-row .bp {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--faint); }}
    .pv-pill {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.66rem; font-weight: 600;
        padding: 0.1rem 0.4rem; border-radius: 999px;
    }}
    .pv-side {{ display: flex; flex-direction: column; gap: 0.7rem; }}
    .pv-panel {{
        border: 1px solid var(--line-soft); border-radius: 12px; padding: 0.85rem; background: var(--surface);
    }}
    .pv-panel .cap {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.64rem; letter-spacing: 0.14em;
        text-transform: uppercase; color: var(--faint); margin-bottom: 0.55rem;
    }}

    .price-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.4rem; }}
    .price-card {{
        display: flex; flex-direction: column; height: 100%;
        min-height: 474px;  /* taller than the featured card -> the three CTAs share a baseline */
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 18px; padding: 1.6rem 1.4rem;
    }}
    .price-card.featured {{
        border-color: rgba(0,245,212,0.45);
        background: linear-gradient(180deg, rgba(0,245,212,0.05), var(--surface));
    }}
    .price-tag {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; letter-spacing: 0.16em;
        text-transform: uppercase; color: var(--accent);
        border: 1px solid rgba(0,245,212,0.3); border-radius: 999px;
        padding: 0.12rem 0.5rem; align-self: flex-start; margin-bottom: 0.7rem;
    }}
    .price-name {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.2rem; color: var(--ink); }}
    .price-amount {{ margin: 0.6rem 0 0.1rem; }}
    .price-amount .a {{ font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.4rem; color: var(--ink); letter-spacing: -0.02em; }}
    .price-amount .p {{ color: var(--faint); font-size: 0.9rem; font-family: 'JetBrains Mono', monospace; }}
    .price-desc {{ color: var(--muted); font-size: 0.88rem; margin: 0.4rem 0 1rem; min-height: 2.4rem; }}
    .price-feats {{ list-style: none; padding: 0; margin: 0 0 1.2rem; }}
    .price-feats li {{ color: var(--muted); font-size: 0.88rem; padding: 0.32rem 0 0.32rem 1.4rem; position: relative; }}
    .price-feats li::before {{ content: "+"; position: absolute; left: 0; color: var(--accent); font-weight: 700; }}
    .price-foot {{ margin-top: auto; }}

    .compare {{
        border: 1px solid var(--line); border-radius: 20px; padding: 2rem 1.8rem;
        background: var(--surface); display: grid; grid-template-columns: 1fr 1fr; gap: 1.4rem;
    }}
    .compare .col h5 {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.16em;
        text-transform: uppercase; margin: 0 0 0.8rem;
    }}
    .compare .them h5 {{ color: var(--faint); }}
    .compare .us h5 {{ color: var(--accent); }}
    .compare ul {{ list-style: none; padding: 0; margin: 0; }}
    .compare li {{ color: var(--muted); font-size: 0.92rem; padding: 0.34rem 0 0.34rem 1.5rem; position: relative; line-height: 1.4; }}
    .compare .them li::before {{ content: "—"; position: absolute; left: 0; color: var(--faint); }}
    .compare .us li::before {{ content: "+"; position: absolute; left: 0; color: var(--accent); font-weight: 700; }}

    .lp-center {{ text-align: center; }}
    .lp-center .lp-lead {{ margin-left: auto; margin-right: auto; }}

    .lp-footer {{
        text-align: center; padding: 3rem 1.5rem 6rem; margin-bottom: 0;
        border: 1px solid var(--line); border-radius: 24px;
        background:
            radial-gradient(ellipse 60% 130% at 50% 0%, rgba(0,245,212,0.08), transparent 60%),
            linear-gradient(180deg, #0b0b12, #0a0a10);
    }}
    .st-key-footer_cta {{ margin-top: -4.6rem; }}
    .lp-footer h3 {{
        font-family: 'Syne', sans-serif; font-weight: 700;
        font-size: clamp(1.7rem, 3vw, 2.4rem); color: var(--ink); margin: 0 0 0.4rem; letter-spacing: -0.02em;
    }}
    .lp-footer p {{ color: var(--muted); margin: 0 0 1.3rem; }}
    .lp-foot-mark {{
        margin-top: 2rem; color: var(--faint);
        font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;
    }}

    div[data-testid="stButton"] {{ margin: 0.35rem 0; }}

    @media (max-width: 900px) {{
        .wheel-wrap {{ width: min(80%, 360px); margin-top: 1.5rem; }}
        .preview-body {{ grid-template-columns: 1fr; }}
        .lp-stats {{ grid-template-columns: repeat(2, 1fr); row-gap: 1.3rem; }}
        .price-grid {{ grid-template-columns: 1fr; }}
        .compare {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 640px) {{
        [data-testid="stMainBlockContainer"], .block-container {{
            padding-left: 1.1rem !important; padding-right: 1.1rem !important;
        }}
        .lp-links {{ display: none; }}
        .lp-brand {{ font-size: 1.05rem; }}
        .lp-title {{ font-size: clamp(2.4rem, 10vw, 3.2rem); }}
        .lp-sub {{ font-size: 1rem; }}
        .lp-footer {{ padding: 2.2rem 1.1rem 4rem; }}
        .lp-h2 {{ font-size: 1.7rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .wheel-halo {{ animation: none; }} }}
</style>
"""


# --------------------------------------------------------------------------- #
# Analyzer-page CSS
# --------------------------------------------------------------------------- #
ANALYZER_CSS = f"""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
    }}

    .setup-kicker {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
        letter-spacing: 0.26em; text-transform: uppercase; color: var(--accent);
    }}
    .setup-title {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.9rem; color: var(--ink);
        margin: 0.3rem 0 0.2rem; letter-spacing: -0.025em;
    }}
    .setup-sub {{ color: var(--muted); margin: 0 0 1rem; max-width: 34rem; line-height: 1.55; }}

    .an-divider {{ height: 1px; border: 0; margin: 1.6rem 0 0.4rem; background: var(--line); }}

    .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.2rem 0 0.4rem; }}
    .chip-row .chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; color: var(--muted);
        padding: 0.32rem 0.7rem; border-radius: 999px; border: 1px solid var(--line); background: var(--surface);
    }}
    .chip-row .chip b {{ color: var(--ink); font-weight: 600; }}

    .inspect-chips {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin-bottom: 0.7rem; }}
    .inspect-chips .ic {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted);
        padding: 0.25rem 0.6rem; border-radius: 8px; background: var(--surface); border: 1px solid var(--line);
    }}
    .inspect-h {{
        color: var(--faint); font-size: 0.72rem; text-transform: uppercase;
        letter-spacing: 0.14em; margin-bottom: 0.6rem;
    }}
    .mix-card {{
        display: flex; align-items: center; gap: 0.7rem; padding: 0.7rem 0.85rem;
        margin-bottom: 0.55rem; border-radius: 12px; background: var(--surface); border: 1px solid var(--line);
        transition: border-color .16s ease;
    }}
    .mix-card:hover {{ border-color: rgba(0,245,212,0.28); }}
    .mix-name {{ color: var(--ink); font-size: 0.92rem; flex: 1; }}
    .mix-score {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--accent); }}

    .an-wheel {{ display: flex; justify-content: center; }}
    .an-wheel svg {{ width: min(100%, 420px); height: auto; }}

    .prem-badge {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; font-weight: 600;
        letter-spacing: 0.12em; vertical-align: middle; margin-left: 0.5rem;
        padding: 0.15rem 0.5rem; border-radius: 999px; color: #08080b;
        background: var(--accent);
    }}

    /* Compact ▲▼ reorder buttons so they don't compete with the track cards. */
    div[class*="st-key-up_"] button, div[class*="st-key-down_"] button {{
        padding: 0.12rem 0.4rem !important;
        min-height: 1.7rem !important;
        font-size: 0.72rem !important;
        border-radius: 8px !important;
    }}

    /* Overview action cards */
    .ov-card-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 600;
        font-size: 1.02rem; color: var(--ink); margin: 0 0 0.25rem;
    }}
    .ov-card-desc {{
        color: var(--muted); font-size: 0.86rem; line-height: 1.5;
        margin: 0 0 0.8rem; min-height: 2.6rem;
    }}
    .ov-locked {{ opacity: 0.55; }}
</style>
"""

"""Theme constants and the injected CSS for the dashboard."""

from __future__ import annotations

APP_TITLE = "Track Analyzer"
ACCENT = "#00f5d4"
ACCENT_2 = "#9b5de5"
SURFACE = "#12121a"
SURFACE_2 = "#1a1a27"

# Colors used by the per-component transition charts (keep in sync with charts.py).
COMPONENT_COLORS = {
    "harmonic": ACCENT_2,
    "bpm": ACCENT,
    "rhythm": "#f15bb5",
    "onset": "#fee440",
    "energy": "#00bbf9",
}


CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {{
        --accent: {ACCENT};
        --accent-2: {ACCENT_2};
        --surface: {SURFACE};
        --surface-2: {SURFACE_2};
    }}

    .stApp {{
        background:
            radial-gradient(ellipse 80% 50% at 20% -10%, rgba(155, 93, 229, 0.18), transparent 55%),
            radial-gradient(ellipse 60% 40% at 90% 10%, rgba(0, 245, 212, 0.12), transparent 50%),
            linear-gradient(180deg, #0a0a0f 0%, #0f0f18 100%);
        font-family: 'Space Grotesk', sans-serif;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #101018 0%, #141422 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 1.5rem;
    }}

    .hero {{
        padding: 0.25rem 0 1.5rem 0;
    }}

    .hero h1 {{
        font-size: 2.6rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, {ACCENT} 55%, {ACCENT_2} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }}

    .hero p {{
        color: rgba(255, 255, 255, 0.62);
        font-size: 1.05rem;
        margin: 0.5rem 0 0 0;
        max-width: 52rem;
    }}

    .metric-card {{
        background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.1rem 1.25rem;
        backdrop-filter: blur(8px);
        min-height: 108px;
    }}

    .metric-label {{
        color: rgba(255, 255, 255, 0.55);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
    }}

    .metric-value {{
        color: #ffffff;
        font-size: 1.85rem;
        font-weight: 700;
        line-height: 1.1;
    }}

    .metric-sub {{
        color: {ACCENT};
        font-size: 0.85rem;
        margin-top: 0.35rem;
        font-family: 'JetBrains Mono', monospace;
    }}

    .playlist-card {{
        background: linear-gradient(135deg, rgba(0, 245, 212, 0.06), rgba(155, 93, 229, 0.06));
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.35rem;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }}

    .playlist-card:hover {{
        border-color: rgba(0, 245, 212, 0.35);
        transform: translateY(-1px);
    }}

    .playlist-order {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 999px;
        background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
        color: #0a0a0f;
        font-weight: 700;
        font-size: 0.95rem;
        margin-right: 0.85rem;
        flex-shrink: 0;
    }}

    .playlist-title {{
        color: #fff;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 0;
    }}

    .playlist-meta {{
        color: rgba(255, 255, 255, 0.58);
        font-size: 0.86rem;
        margin-top: 0.25rem;
        font-family: 'JetBrains Mono', monospace;
    }}

    .camelot-pill {{
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.45rem;
        font-family: 'JetBrains Mono', monospace;
    }}

    .camelot-a {{
        background: rgba(155, 93, 229, 0.22);
        color: #d8b4fe;
        border: 1px solid rgba(155, 93, 229, 0.35);
    }}

    .camelot-b {{
        background: rgba(0, 245, 212, 0.18);
        color: #7fffe8;
        border: 1px solid rgba(0, 245, 212, 0.35);
    }}

    .score-pill {{
        display: inline-block;
        margin-top: 0.45rem;
        padding: 0.2rem 0.55rem;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.06);
        color: {ACCENT};
        font-size: 0.78rem;
        font-family: 'JetBrains Mono', monospace;
    }}

    .score-pill.warn {{
        color: #ffb4a2;
        background: rgba(241, 91, 91, 0.12);
    }}

    .score-pill.good {{
        color: #7fffe8;
        background: rgba(0, 245, 212, 0.12);
    }}

    /* Anything with a tooltip invites a hover. */
    .score-pill[title], .chip[title], .ic[title], .mix-card[title], .camelot-pill[title] {{
        cursor: help;
    }}

    /* Module switcher: styled as underline navigation tabs so it reads as
       "where am I", clearly distinct from the pill-shaped setting controls. */
    .st-key-an_module {{
        margin: 0.7rem 0 0.4rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }}
    .st-key-an_module button {{
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        border-bottom: 2px solid transparent !important;
        font-size: 0.98rem !important;
        padding: 0.6rem 1.15rem !important;
        font-weight: 600;
        color: rgba(255,255,255,0.55) !important;
        box-shadow: none !important;
    }}
    .st-key-an_module button:hover {{
        color: #fff !important;
    }}
    /* Selected tab: theme primaryColor drives the text; we add the underline. */
    .st-key-an_module button[kind="segmented_controlActive"],
    .st-key-an_module button[aria-checked="true"] {{
        color: {ACCENT} !important;
        border-bottom: 2px solid {ACCENT} !important;
    }}

    /* Setup journey strip */
    .setup-steps {{
        display: flex; flex-wrap: wrap; gap: 2rem;
        margin: 0.3rem 0 1.2rem;
        font-size: 0.86rem; color: rgba(255,255,255,0.55);
    }}
    .setup-steps b {{
        font-family: 'Syne', sans-serif; font-size: 1.05rem;
        background: linear-gradient(120deg, {ACCENT}, {ACCENT_2});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-right: 0.4rem;
    }}

    /* Labeled control bar */
    .bar-label {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
        letter-spacing: 0.25em; text-transform: uppercase;
        color: rgba(255,255,255,0.45); margin-bottom: 0.15rem;
    }}

    /* Module description line under the nav */
    .module-desc {{
        color: rgba(255,255,255,0.5); font-size: 0.88rem; margin: 0.2rem 0 1rem;
    }}

    /* Discover cards */
    .disc-card {{
        display: flex; align-items: center; gap: 0.8rem;
        padding: 0.85rem 1rem; margin-bottom: 0.6rem; border-radius: 14px;
        background: linear-gradient(135deg, rgba(0,245,212,0.04), rgba(155,93,229,0.04));
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .disc-card .t {{ color: #fff; font-size: 0.95rem; font-weight: 600; }}
    .disc-card .a {{ color: rgba(255,255,255,0.55); font-size: 0.85rem; }}
    .disc-card .grow {{ flex: 1; min-width: 0; }}
    .disc-card .src {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
        padding: 0.15rem 0.5rem; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.14); color: rgba(255,255,255,0.55);
    }}
    .disc-card a {{ color: {ACCENT}; text-decoration: none; font-size: 0.85rem; }}
    .disc-chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
        padding: 0.2rem 0.55rem; border-radius: 8px;
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.72); white-space: nowrap;
    }}
    .disc-chip.good {{ color: #7fffe8; background: rgba(0,245,212,0.1); }}
    .disc-chip.warn {{ color: #ffb4a2; background: rgba(241,91,91,0.1); }}

    .empty-state {{
        text-align: center;
        padding: 3.5rem 1.5rem;
        border: 1px dashed rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.02);
    }}

    .empty-state h3 {{
        color: #fff;
        margin-bottom: 0.5rem;
    }}

    .empty-state p {{
        color: rgba(255, 255, 255, 0.55);
        margin: 0;
    }}

    div[data-testid="stButton"] > button {{
        border-radius: 12px;
        border: 1px solid rgba(0, 245, 212, 0.35);
        background: linear-gradient(135deg, rgba(0, 245, 212, 0.18), rgba(155, 93, 229, 0.18));
        color: white;
        font-weight: 600;
        transition: all 0.15s ease;
    }}

    div[data-testid="stButton"] > button:hover {{
        border-color: {ACCENT};
        box-shadow: 0 0 24px rgba(0, 245, 212, 0.18);
        color: white;
    }}

    .stTextInput input {{
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        font-family: 'JetBrains Mono', monospace;
    }}

    .section-title {{
        color: #fff;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 1.5rem 0 0.75rem 0;
        letter-spacing: -0.02em;
    }}

    .section-hint {{
        color: rgba(255,255,255,0.5);
        font-size: 0.85rem;
        margin: -0.4rem 0 0.75rem 0;
    }}

    #MainMenu, footer, header {{
        visibility: hidden;
    }}

    /* Hide Streamlit's hover anchor icons on headings. */
    [data-testid="stHeaderActionElements"] {{
        display: none;
    }}

    /* Shared app brand (header on every page) */
    .app-brand {{
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: -0.02em;
        color: #fff;
        display: flex; align-items: center; gap: 0.55rem;
    }}
    .app-brand .disc {{
        width: 1.05rem; height: 1.05rem; border-radius: 50%;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
        box-shadow: 0 0 12px rgba(0,245,212,0.35);
    }}
    .app-brand .crumb {{
        color: rgba(255,255,255,0.45); font-weight: 400; font-size: 0.95rem;
        font-family: 'JetBrains Mono', monospace; margin-left: 0.35rem;
    }}
    .app-header-rule {{
        height: 1px; border: 0; margin: 0.4rem 0 1.1rem;
        background: linear-gradient(90deg, rgba(0,245,212,0.25), rgba(255,255,255,0.06) 40%, rgba(255,255,255,0));
    }}
    /* Quiet, link-like header nav button */
    .st-key-nav_home button {{
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.6) !important;
        font-weight: 500;
    }}
    .st-key-nav_home button:hover {{
        color: {ACCENT} !important;
        box-shadow: none !important;
    }}

    /* Tabs: use the theme accent instead of Streamlit's default red. */
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: {ACCENT};
    }}
    .stTabs button[aria-selected="true"] {{
        color: {ACCENT} !important;
    }}
</style>
"""


# Landing-page styles. Injected only by the Home page so the analyzer keeps its
# sidebar; the landing hides the sidebar/header and renders a full navbar layout.
HOME_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&display=swap');

    /* Landing chrome: no sidebar, no toolbar — a real landing page. */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    [data-testid="stMainBlockContainer"], .block-container {{
        max-width: 1180px !important;
        padding-top: 1.4rem !important;
    }}

    /* Navbar */
    .lp-brand {{
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 1.2rem;
        letter-spacing: -0.02em;
        color: #fff;
        display: flex; align-items: center; gap: 0.55rem;
        padding-top: 0.55rem;
    }}
    .lp-brand .disc {{
        width: 1.15rem; height: 1.15rem; border-radius: 50%;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
        box-shadow: 0 0 14px rgba(0,245,212,0.4);
    }}
    .lp-links {{
        display: flex; justify-content: flex-end; align-items: center; gap: 1.8rem;
        height: 100%; padding-top: 0.7rem;
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; letter-spacing: 0.06em;
    }}
    .lp-links a {{ color: rgba(255,255,255,0.6); text-decoration: none; transition: color 0.15s ease; }}
    .lp-links a:hover {{ color: {ACCENT}; }}

    /* Hero */
    .lp-eyebrow {{
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem; letter-spacing: 0.34em; text-transform: uppercase;
        color: {ACCENT};
        padding: 0.35rem 0.85rem; border-radius: 999px;
        border: 1px solid rgba(0,245,212,0.3); background: rgba(0,245,212,0.06);
    }}
    .lp-title {{
        font-family: 'Syne', sans-serif; font-weight: 800;
        font-size: clamp(2.9rem, 5.6vw, 4.6rem); line-height: 0.98;
        letter-spacing: -0.03em; margin: 1.3rem 0 0; color: #fff;
    }}
    .lp-title em {{
        font-style: normal;
        background: linear-gradient(115deg, {ACCENT} 0%, {ACCENT_2} 55%, #f15bb5 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .lp-sub {{
        color: rgba(255,255,255,0.66); font-size: 1.12rem; line-height: 1.55;
        max-width: 30rem; margin: 1.3rem 0 0;
    }}
    .lp-hero-note {{
        margin-top: 1.6rem; color: rgba(255,255,255,0.4);
        font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; letter-spacing: 0.04em;
    }}

    /* Signature: the Camelot wheel */
    .wheel-wrap {{
        position: relative; width: min(100%, 440px); aspect-ratio: 1; margin: 0 auto;
    }}
    .wheel-halo {{
        position: absolute; inset: -6%; border-radius: 50%; z-index: 0;
        background: conic-gradient(from 0deg, {ACCENT}, {ACCENT_2}, #f15bb5, #fee440, {ACCENT});
        filter: blur(40px); opacity: 0.32;
        animation: spin 26s linear infinite;
    }}
    .wheel-svg {{
        position: relative; z-index: 1; width: 100%; height: auto;
        filter: drop-shadow(0 0 26px rgba(0,245,212,0.14));
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    /* Spec chips */
    .lp-specs {{
        display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center;
        margin: 0.5rem 0 0.5rem;
    }}
    .lp-chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
        color: rgba(255,255,255,0.72);
        padding: 0.4rem 0.8rem; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03);
    }}
    .lp-chip b {{ color: {ACCENT}; font-weight: 500; }}

    /* Section headings */
    .lp-kicker {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.74rem;
        letter-spacing: 0.3em; text-transform: uppercase; color: {ACCENT_2};
    }}
    .lp-h2 {{
        font-family: 'Syne', sans-serif; font-weight: 700;
        font-size: clamp(1.7rem, 3vw, 2.4rem); letter-spacing: -0.02em;
        color: #fff; margin: 0.3rem 0 0.2rem;
    }}

    /* Feature cards */
    .feature-card {{
        height: 100%;
        background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.08); border-radius: 18px;
        padding: 1.4rem 1.3rem; transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .feature-card:hover {{ transform: translateY(-3px); border-color: rgba(0,245,212,0.35); }}
    .feature-icon {{ font-size: 1.6rem; }}
    .feature-card h4 {{ color: #fff; margin: 0.6rem 0 0.35rem; font-size: 1.05rem; font-weight: 600; }}
    .feature-card p {{ color: rgba(255,255,255,0.58); font-size: 0.88rem; margin: 0; line-height: 1.5; }}

    /* How-it-works steps (a real sequence, so numbered) */
    .lp-step {{
        border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1rem; height: 100%;
    }}
    .lp-step .num {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.1rem;
        background: linear-gradient(120deg, {ACCENT}, {ACCENT_2});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .lp-step h4 {{ color: #fff; margin: 0.3rem 0 0.35rem; font-size: 1.05rem; }}
    .lp-step p {{ color: rgba(255,255,255,0.55); font-size: 0.88rem; margin: 0; line-height: 1.5; }}

    /* Footer CTA band */
    .lp-footer {{
        text-align: center; padding: 2.8rem 1.5rem 6rem; margin-bottom: 0;
        border: 1px solid rgba(255,255,255,0.08); border-radius: 24px;
        background:
            radial-gradient(ellipse 60% 120% at 50% 0%, rgba(155,93,229,0.15), transparent 60%),
            linear-gradient(180deg, #0c0c14, #0a0a10);
    }}
    /* Pull the footer CTA up into the band so it reads as part of it. */
    .st-key-footer_cta {{ margin-top: -4.6rem; }}
    .lp-footer h3 {{
        font-family: 'Syne', sans-serif; font-weight: 700;
        font-size: clamp(1.6rem, 3vw, 2.3rem); color: #fff; margin: 0 0 0.4rem;
    }}
    .lp-footer p {{ color: rgba(255,255,255,0.55); margin: 0 0 1.3rem; }}
    .lp-foot-mark {{
        margin-top: 2rem; color: rgba(255,255,255,0.35);
        font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;
    }}

    /* Give every Launch button breathing room so it never glues to a block. */
    div[data-testid="stButton"] {{ margin: 0.35rem 0; }}

    /* Responsive: adapt navbar, type, and paddings down to mobile. */
    @media (max-width: 900px) {{
        .wheel-wrap {{ width: min(80%, 360px); margin-top: 1.5rem; }}
    }}
    @media (max-width: 640px) {{
        [data-testid="stMainBlockContainer"], .block-container {{
            padding-left: 1.1rem !important; padding-right: 1.1rem !important;
        }}
        .lp-links {{ display: none; }}
        .lp-brand {{ font-size: 1.05rem; }}
        .lp-title {{ font-size: clamp(2.2rem, 9vw, 3rem); }}
        .lp-sub {{ font-size: 1rem; }}
        .lp-footer {{ padding: 2rem 1.1rem; }}
        .lp-h2 {{ font-size: 1.6rem; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        .wheel-halo {{ animation: none; }}
    }}
</style>
"""


# Analyzer-page polish: setup panel, control bar, status chips, inspector.
ANALYZER_CSS = f"""
<style>
    /* Bordered containers (setup panel + control bar) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255,255,255,0.02);
        border-radius: 16px;
    }}

    .setup-kicker {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
        letter-spacing: 0.3em; text-transform: uppercase; color: {ACCENT};
    }}
    .setup-title {{
        font-family: 'Space Grotesk', sans-serif; font-weight: 700;
        font-size: 1.7rem; color: #fff; margin: 0.2rem 0 0.2rem; letter-spacing: -0.02em;
    }}
    .setup-sub {{ color: rgba(255,255,255,0.55); margin: 0 0 1rem; max-width: 34rem; }}

    /* A quiet section divider */
    .an-divider {{
        height: 1px; border: 0; margin: 1.6rem 0 0.4rem;
        background: linear-gradient(90deg, rgba(255,255,255,0.12), rgba(255,255,255,0));
    }}

    /* Status chips under the header */
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.2rem 0 0.4rem; }}
    .chip-row .chip {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;
        color: rgba(255,255,255,0.72); padding: 0.32rem 0.7rem; border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.03);
    }}
    .chip-row .chip b {{ color: {ACCENT}; font-weight: 500; }}

    /* Track inspector */
    .inspect-chips {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin-bottom: 0.7rem; }}
    .inspect-chips .ic {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
        color: rgba(255,255,255,0.7); padding: 0.25rem 0.6rem; border-radius: 8px;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    }}
    .inspect-h {{
        color: rgba(255,255,255,0.55); font-size: 0.8rem; text-transform: uppercase;
        letter-spacing: 0.12em; margin-bottom: 0.6rem;
    }}
    .mix-card {{
        display: flex; align-items: center; gap: 0.7rem;
        padding: 0.7rem 0.85rem; margin-bottom: 0.55rem; border-radius: 12px;
        background: linear-gradient(135deg, rgba(0,245,212,0.05), rgba(155,93,229,0.05));
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .mix-name {{ color: #fff; font-size: 0.92rem; flex: 1; }}
    .mix-score {{
        font-family: 'JetBrains Mono', monospace; font-weight: 600; color: {ACCENT};
    }}

    /* Analyzer's Camelot wheel: centered, capped width. */
    .an-wheel {{
        display: flex; justify-content: center;
    }}
    .an-wheel svg {{
        width: min(100%, 420px); height: auto;
        filter: drop-shadow(0 0 22px rgba(0,245,212,0.1));
    }}

    .prem-badge {{
        font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; font-weight: 600;
        letter-spacing: 0.12em; vertical-align: middle; margin-left: 0.5rem;
        padding: 0.15rem 0.5rem; border-radius: 999px; color: #0a0a0f;
        background: linear-gradient(120deg, {ACCENT}, {ACCENT_2});
    }}
</style>
"""

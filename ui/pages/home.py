"""Home / landing page — navbar, Camelot-wheel hero, and full-page sections.

No sidebar: the landing hides Streamlit's sidebar/header via ``HOME_CSS`` and
navigates into the tool through in-page buttons (navbar, hero, footer).
"""

from __future__ import annotations

import streamlit as st

from ui.charts import camelot_wheel_svg
from ui.styles import HOME_CSS

_FEATURES = [
    ("🎹", "Harmonic keys", "Every track gets a musical key and Camelot code, so blends stay in tune instead of clashing."),
    ("🥁", "Groove match", "A rhythm fingerprint and onset density line up tracks that actually feel alike, not just share a key."),
    ("⚡", "Energy flow", "Order the set as a build-up or a plateau, and reshape it live — no re-analysis."),
    ("🎛️", "Live control", "Weight what matters for your mix and reorder by hand; the set updates the moment you change it."),
]

_STEPS = [
    ("01", "Point at a folder", "Choose any folder of songs — mp3, wav, flac, m4a, aac, ogg. Subfolders optional."),
    ("02", "Analyze", "Each track is read for BPM, key, groove, and energy. Results are cached, so it only runs once."),
    ("03", "Shape & export", "Reorder live, then export CSV or an M3U your DJ software can open."),
]


def _launch(key: str, label: str = "Launch Analyzer  →") -> None:
    if st.button(label, type="primary", key=key, width="stretch"):
        st.switch_page(st.session_state["_analyzer_page"])


def _navbar() -> None:
    brand, links, cta = st.columns([1.4, 2, 1], vertical_alignment="center")
    with brand:
        st.markdown(
            '<div class="lp-brand"><span class="disc"></span>Track Analyzer</div>',
            unsafe_allow_html=True,
        )
    with links:
        st.markdown(
            '<div class="lp-links">'
            '<a href="#capabilities">Capabilities</a>'
            '<a href="#how-it-works">How it works</a>'
            '</div>',
            unsafe_allow_html=True,
        )
    with cta:
        _launch("nav_launch", "Launch  →")


def _hero() -> None:
    text, art = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")
    with text:
        st.markdown('<span class="lp-eyebrow">Harmonic mixing engine</span>', unsafe_allow_html=True)
        st.markdown(
            '<h1 class="lp-title">Mix in<br><em>perfect key.</em></h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="lp-sub">Turn any folder of songs into a DJ set that flows — '
            'ordered by key, tempo, groove, and energy for transitions that just land.</p>',
            unsafe_allow_html=True,
        )
        cta, _ = st.columns([1.4, 2])  # constrain CTA width under the copy
        with cta:
            _launch("hero_launch")
        st.markdown(
            '<p class="lp-hero-note">Local · private · no upload — your tracks never leave your machine.</p>',
            unsafe_allow_html=True,
        )
    with art:
        st.markdown(
            f'<div class="wheel-wrap"><div class="wheel-halo"></div>{camelot_wheel_svg()}</div>',
            unsafe_allow_html=True,
        )


def _specs() -> None:
    st.markdown(
        '<div class="lp-specs">'
        '<span class="lp-chip"><b>24</b> Camelot keys</span>'
        '<span class="lp-chip"><b>BPM</b> detection</span>'
        '<span class="lp-chip"><b>Rhythm</b> fingerprint</span>'
        '<span class="lp-chip"><b>Energy</b> flow</span>'
        '<span class="lp-chip"><b>CSV</b> · <b>M3U</b> export</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _capabilities() -> None:
    st.markdown('<span id="capabilities"></span>', unsafe_allow_html=True)
    st.markdown('<div class="lp-kicker">What it does</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="lp-h2">Four signals, one seamless set</h2>', unsafe_allow_html=True)
    st.write("")
    for col, (icon, title, body) in zip(st.columns(4, gap="medium"), _FEATURES):
        with col:
            st.markdown(
                f'<div class="feature-card"><div class="feature-icon">{icon}</div>'
                f'<h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )


def _how() -> None:
    st.markdown('<span id="how-it-works"></span>', unsafe_allow_html=True)
    st.markdown('<div class="lp-kicker">How it works</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="lp-h2">From folder to flawless set</h2>', unsafe_allow_html=True)
    st.write("")
    for col, (num, title, body) in zip(st.columns(3, gap="large"), _STEPS):
        with col:
            st.markdown(
                f'<div class="lp-step"><div class="num">{num}</div>'
                f'<h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )


def _footer() -> None:
    st.markdown(
        '<div class="lp-footer"><h3>Ready to build your set?</h3>'
        '<p>Point it at your library and let the wheel do the sequencing.</p></div>',
        unsafe_allow_html=True,
    )
    # Keyed container -> .st-key-footer_cta, pulled up into the band via CSS.
    with st.container(key="footer_cta"):
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            _launch("footer_launch")
    st.markdown(
        '<p class="lp-foot-mark">Track Analyzer · harmonic playlist builder</p>',
        unsafe_allow_html=True,
    )


def _divider(space: str = "3.5rem") -> None:
    st.markdown(f"<div style='height:{space}'></div>", unsafe_allow_html=True)


def home_page() -> None:
    st.markdown(HOME_CSS, unsafe_allow_html=True)
    _navbar()
    _divider("2rem")
    _hero()
    _divider("2.5rem")
    _specs()
    _divider()
    _capabilities()
    _divider()
    _how()
    _divider()
    _footer()

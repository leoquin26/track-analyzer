"""Home / landing page — premium, minimal, SaaS-shaped.

No sidebar: the landing hides Streamlit's sidebar/header via ``HOME_CSS`` and
navigates into the tool through in-page buttons (navbar, hero, pricing, footer).
Sections: navbar · hero · stat band · product preview · capabilities ·
how-it-works · positioning · pricing · footer.
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
    ("03", "Shape & export", "Reorder live, then export CSV, M3U, or your DJ software's own format."),
]

_STATS = [
    ("24", "Camelot keys"),
    ("5", "Mix signals"),
    ("0", "Uploads needed"),
    ("∞", "Library size"),
]

# (name, price, per, description, [features], featured?, cta_label, cta_key)
_PLANS = [
    ("Free", "$0", "forever", "Try the full engine on a small crate.",
     ["Up to 50 tracks", "Harmonic ordering", "CSV + M3U export", "Live reordering"],
     False, "Start free  →", "price_free"),
    ("Pro", "$12", "/ month", "For working DJs with a real library.",
     ["Unlimited tracks", "rekordbox · Serato · Traktor export",
      "Key + BPM written to tags", "Energy-curve set builder", "Similar-track discovery"],
     True, "Go Pro  →", "price_pro"),
    ("Lifetime", "$149", "once", "Pay once, own it. Limited early-bird.",
     ["Everything in Pro", "All future updates", "Founder's badge", "Priority feature requests"],
     False, "Get lifetime  →", "price_life"),
]


def _launch(key: str, label: str = "Launch Analyzer  →", kind: str = "primary") -> None:
    if st.button(label, type=kind, key=key, width="stretch"):
        st.switch_page(st.session_state["_analyzer_page"])


def _navbar() -> None:
    brand, links, cta = st.columns([1.4, 2, 1], vertical_alignment="center")
    with brand:
        st.markdown(
            '<div class="lp-brand"><span class="disc"></span>Keyflow</div>',
            unsafe_allow_html=True,
        )
    with links:
        st.markdown(
            '<div class="lp-links">'
            '<a href="#capabilities">Capabilities</a>'
            '<a href="#how-it-works">How it works</a>'
            '<a href="#pricing">Pricing</a>'
            '</div>',
            unsafe_allow_html=True,
        )
    with cta:
        _launch("nav_launch", "Open app  →")


def _hero() -> None:
    text, art = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")
    with text:
        st.markdown(
            '<span class="lp-eyebrow">Keyflow · harmonic mixing engine · <b>local & private</b></span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h1 class="lp-title">Sets that flow<br><em>in key.</em></h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="lp-sub">Keyflow turns any folder of songs into a DJ set that flows — '
            'ordered by key, tempo, groove, and energy for transitions that just land.</p>',
            unsafe_allow_html=True,
        )
        cta, _ = st.columns([1.4, 2])
        with cta:
            _launch("hero_launch")
        st.markdown(
            '<p class="lp-hero-note">No upload · your tracks never leave your machine.</p>',
            unsafe_allow_html=True,
        )
    with art:
        st.markdown(
            f'<div class="wheel-wrap"><div class="wheel-halo"></div>{camelot_wheel_svg()}</div>',
            unsafe_allow_html=True,
        )


def _stats() -> None:
    cells = "".join(
        f'<div class="lp-stat"><div class="n">{n}</div><div class="l">{l}</div></div>'
        for n, l in _STATS
    )
    st.markdown(f'<div class="lp-stats">{cells}</div>', unsafe_allow_html=True)


_PV_ROWS = [
    ("1", "Midnight Drive", "8A", "camelot-a", "124"),
    ("2", "Neon Tide", "9A", "camelot-a", "125"),
    ("3", "Afterglow", "9B", "camelot-b", "126"),
    ("4", "Parallel", "10B", "camelot-b", "128"),
    ("5", "Skyline", "11B", "camelot-b", "128"),
]


def _preview() -> None:
    st.markdown('<div class="lp-kicker">The tool</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="lp-h2">See the set take shape</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="lp-lead">Your library, ordered for smooth transitions — with the energy '
        'curve and Camelot coverage right beside it.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    rows = "".join(
        f'<div class="pv-row"><span class="o">{o}</span>'
        f'<span class="pv-pill {cls}">{cam}</span>'
        f'<span class="nm">{name}</span><span class="bp">{bpm} BPM</span></div>'
        for o, name, cam, cls, bpm in _PV_ROWS
    )
    # A small energy sparkline for the side panel.
    spark = (
        '<svg viewBox="0 0 200 60" preserveAspectRatio="none" style="width:100%;height:56px">'
        '<polyline points="0,46 40,40 80,30 120,20 160,14 200,10" fill="none" '
        'stroke="#00f5d4" stroke-width="2.5"/>'
        '<polyline points="0,46 40,40 80,30 120,20 160,14 200,10 200,60 0,60" '
        'fill="rgba(0,245,212,0.10)" stroke="none"/></svg>'
    )
    keys = "".join(
        f'<span class="pv-pill {cls}" style="margin:2px">{c}</span>'
        for c, cls in [("8A", "camelot-a"), ("9A", "camelot-a"), ("9B", "camelot-b"),
                       ("10B", "camelot-b"), ("11B", "camelot-b")]
    )
    st.markdown(
        '<div class="preview-frame">'
        '<div class="preview-bar"><i></i><i></i><i></i>'
        '<span class="u">keyflow.dj · set builder</span></div>'
        '<div class="preview-body">'
        f'<div class="pv-rows">{rows}</div>'
        '<div class="pv-side">'
        f'<div class="pv-panel"><div class="cap">Energy curve</div>{spark}</div>'
        f'<div class="pv-panel"><div class="cap">Keys in set</div><div>{keys}</div></div>'
        '</div></div></div>',
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


def _positioning() -> None:
    st.markdown('<div class="lp-kicker">Why it\'s different</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="lp-h2">More than a key detector</h2>', unsafe_allow_html=True)
    st.write("")
    st.markdown(
        '<div class="compare">'
        '<div class="col them"><h5>Traditional key tools</h5><ul>'
        '<li>Detect key &amp; BPM, then stop</li>'
        '<li>You sequence the set by hand</li>'
        '<li>No sense of groove or energy</li>'
        '<li>One-time desktop license</li>'
        '</ul></div>'
        '<div class="col us"><h5>Keyflow</h5><ul>'
        '<li>Key, BPM, groove &amp; energy in one pass</li>'
        '<li>Orders the whole set for smooth transitions</li>'
        '<li>Reshape the energy curve live</li>'
        '<li>Exports to rekordbox, Serato &amp; Traktor</li>'
        '</ul></div></div>',
        unsafe_allow_html=True,
    )


def _pricing() -> None:
    st.markdown('<span id="pricing"></span>', unsafe_allow_html=True)
    st.markdown('<div class="lp-center">'
                '<div class="lp-kicker">Pricing</div>'
                '<h2 class="lp-h2">Start free. Upgrade when it earns you gigs.</h2>'
                '<p class="lp-lead">Analysis runs locally, so your library stays private on every plan.</p>'
                '</div>', unsafe_allow_html=True)
    st.write("")
    cols = st.columns(3, gap="medium")
    for col, (name, price, per, desc, feats, featured, cta_label, cta_key) in zip(cols, _PLANS):
        with col:
            tag = '<span class="price-tag">Most popular</span>' if featured else ''
            feat_items = "".join(f"<li>{f}</li>" for f in feats)
            st.markdown(
                f'<div class="price-card{" featured" if featured else ""}">'
                f'{tag}'
                f'<div class="price-name">{name}</div>'
                f'<div class="price-amount"><span class="a">{price}</span> '
                f'<span class="p">{per}</span></div>'
                f'<div class="price-desc">{desc}</div>'
                f'<ul class="price-feats">{feat_items}</ul>'
                f'<div class="price-foot"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _launch(cta_key, cta_label, kind="primary" if featured else "secondary")
    st.markdown(
        '<p class="lp-hero-note" style="text-align:center">Lifetime early-bird is capped — '
        'price rises as slots fill.</p>',
        unsafe_allow_html=True,
    )


def _footer() -> None:
    st.markdown(
        '<div class="lp-footer"><h3>Ready to build your set?</h3>'
        '<p>Point it at your library and let the wheel do the sequencing.</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="footer_cta"):
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            _launch("footer_launch")
    st.markdown(
        '<p class="lp-foot-mark">Keyflow · sets that flow in key · keyflow.dj</p>',
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
    _stats()
    _divider()
    _preview()
    _divider()
    _capabilities()
    _divider()
    _how()
    _divider()
    _positioning()
    _divider()
    _pricing()
    _divider()
    _footer()

"""Keyflow — multipage entry point / router.

Defines page config, session state, and CSS once, then hands off to the Home
(landing) and Analyzer pages via ``st.navigation``. Page bodies live in
``ui/pages/``; analysis/charts/components/styles live in ``ui/``.
"""

from __future__ import annotations

import streamlit as st

from ui import state
from ui.styles import APP_TITLE, CUSTOM_CSS

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.pages.analyzer import analyzer_page  # noqa: E402 - after set_page_config
from ui.pages.home import home_page  # noqa: E402


def main() -> None:
    state.init_session_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    home = st.Page(home_page, title="Home", icon="🏠", default=True)
    analyzer = st.Page(analyzer_page, title="Analyzer", icon="🎛️")

    # Stashed so in-page buttons can move between the landing and the tool;
    # the default sidebar nav is hidden so the landing reads as a real page.
    st.session_state["_home_page"] = home
    st.session_state["_analyzer_page"] = analyzer

    st.navigation([home, analyzer], position="hidden").run()


if __name__ == "__main__":
    main()

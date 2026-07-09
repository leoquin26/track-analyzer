"""Analyzer page — guided setup → analyzing → results, no sidebar.

Controls live in a top control bar (state 3) instead of the sidebar; the page
walks through three states so it never looks blank or stuck.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ui import auth, charts, components, premium, state
from ui.styles import ANALYZER_CSS


def _stash_uploads(uploads: list) -> Path:
    """Persist uploaded files into a per-session temp dir so the normal
    folder-based analysis (and audio preview) can work on them."""
    import tempfile

    if "upload_dir" not in st.session_state:
        st.session_state["upload_dir"] = tempfile.mkdtemp(prefix="ta_uploads_")
    upload_dir = Path(st.session_state["upload_dir"])
    for uploaded in uploads:
        (upload_dir / Path(uploaded.name).name).write_bytes(uploaded.getbuffer())
    return upload_dir


def run_analysis_flow(config: dict) -> None:
    if config.get("uploads"):
        folder = _stash_uploads(config["uploads"])
        config = {**config, "recursive": False}
    else:
        folder = config["folder"]
    if not folder or not folder.is_dir():
        st.session_state.last_error = "Choose a music folder or upload some tracks first."
        st.session_state.tracks = None
        return

    # Plan limit: Free analyzes the first N tracks of a crate.
    max_tracks = auth.entitled("max_tracks")
    if max_tracks is not None:
        from harmonic_playlist import find_audio_files

        found = len(find_audio_files(folder, config["recursive"]))
        if found > max_tracks:
            st.warning(
                f"Your **Free** plan analyzes up to **{max_tracks} tracks** per crate — "
                f"this folder has {found}, so only the first {max_tracks} will be read. "
                f"Upgrade to Pro for unlimited tracks."
            )
            st.session_state["_track_cap"] = max_tracks
        else:
            st.session_state["_track_cap"] = None
    else:
        st.session_state["_track_cap"] = None

    st.session_state.last_error = ""
    progress = st.progress(0.0, text="Starting analysis…")
    status = st.empty()

    def on_progress(name: str, index: int, total: int) -> None:
        progress.progress(index / total, text=f"Analyzing {index}/{total}: {name}")
        status.caption(f"Current track: **{name}**")

    with st.spinner("Analyzing tracks…"):
        tracks, failed, total = state.analyze_folder(
            folder, config["duration"], config["recursive"], on_progress,
            limit=st.session_state.get("_track_cap"),
        )

    progress.empty()
    status.empty()

    if total == 0:
        st.session_state.last_error = "No audio files found in that folder."
        st.session_state.tracks = None
    elif not tracks:
        st.session_state.last_error = "Tracks were found, but none could be analyzed."
        st.session_state.tracks = None
    else:
        state.store_analysis(tracks, failed, total)


def _divider() -> None:
    st.markdown('<hr class="an-divider">', unsafe_allow_html=True)


def render_page_header(module: str) -> None:
    st.markdown(f'<h1 class="pg-title">{module}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="pg-desc">{MODULE_DESCRIPTIONS[module]}</p>', unsafe_allow_html=True)


def _energy_sparkline(ordered: list[dict]) -> str:
    """Inline SVG sparkline of the set's energy curve, with a draw-in animation."""
    energies = [float(t["energy"]) for t in ordered]
    if len(energies) < 2:
        energies = energies * 2 or [0.0, 0.0]
    lo, hi = min(energies), max(energies)
    span = (hi - lo) or 1.0
    n = len(energies)
    pts = [(i * (220 / (n - 1)), 52 - ((e - lo) / span) * 40) for i, e in enumerate(energies)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"0,60 {line} 220,60"
    return (
        '<svg viewBox="0 0 220 60" preserveAspectRatio="none" style="width:100%;height:56px">'
        f'<polyline points="{area}" fill="rgba(94,234,212,0.08)" stroke="none"/>'
        f'<polyline class="spark-line" points="{line}" fill="none" stroke="#5eead4" '
        'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def render_status_chips(frames: dict, ordered: list[dict]) -> None:
    analysis_df = frames["analysis_df"]
    playlist_df = frames["playlist_df"]
    avg_bpm = analysis_df["bpm"].mean() if not analysis_df.empty else float("nan")
    avg_score = pd.to_numeric(
        playlist_df["transition_score_from_previous"], errors="coerce"
    ).mean()
    keys = analysis_df["camelot"].nunique() if not analysis_df.empty else 0

    chips = [
        f"<span class='chip' title='Tracks successfully analyzed from your folder.'>"
        f"<b>{len(st.session_state.tracks or [])}</b> tracks</span>"
    ]
    if pd.notna(avg_bpm):
        chips.append(
            f"<span class='chip' title='Average tempo across the library, in beats per minute.'>"
            f"avg <b>{avg_bpm:.0f}</b> BPM</span>"
        )
    if pd.notna(avg_score):
        chips.append(
            f"<span class='chip' title='Average transition smoothness across the set, out of ~115. "
            f"75+ seamless · 40–75 workable · below 40 tricky.'>avg transition <b>{avg_score:.0f}</b></span>"
        )
    chips.append(
        f"<span class='chip' title='Tracks currently in the set (excluded tracks don’t count).'>"
        f"<b>{len(ordered)}</b> in set</span>"
    )
    chips.append(
        f"<span class='chip' title='Distinct Camelot keys in the set — fewer keys usually means easier mixing.'>"
        f"<b>{keys}</b> keys</span>"
    )
    chips_col, guide_col = st.columns([5.2, 0.9], vertical_alignment="center")
    with chips_col:
        st.markdown(f"<div class='chip-row'>{''.join(chips)}</div>", unsafe_allow_html=True)
    with guide_col:
        components.render_metrics_guide()


def render_downloads(frames: dict) -> None:
    st.markdown('<div class="section-title">Exports</div>', unsafe_allow_html=True)
    output_dir = Path(st.session_state.output_folder or "output")
    files = {
        "track_analysis.csv": frames["analysis_df"].to_csv(index=False),
        "playlist_order.csv": frames["playlist_df"].to_csv(index=False),
        "transition_matrix.csv": frames["matrix_df"].to_csv(),
        "playlist.m3u": frames["m3u_content"],
    }
    cols = st.columns(5)
    for col, (filename, content) in zip(cols, files.items()):
        with col:
            st.download_button(
                label=f"Download {filename}",
                data=content,
                file_name=filename,
                mime="text/csv" if filename.endswith(".csv") else "audio/x-mpegurl",
                width="stretch",
            )
    with cols[4]:
        if st.button("Save all to output folder", width="stretch"):
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                for filename, content in files.items():
                    (output_dir / filename).write_text(content, encoding="utf-8")
                st.success(f"Saved to {output_dir}")
            except Exception as error:  # noqa: BLE001
                st.error(f"Could not save: {error}")


MODULES = ["Overview", "Analyze", "Set builder", "Inspector", "Discover", "Insights", "Data", "Export", "Account"]

# Modules that need an analysis before they have anything to show.
DATA_MODULES = MODULES[2:8]

MODULE_DESCRIPTIONS = {
    "Overview": "Your workspace at a glance — library metrics and where to go next.",
    "Analyze": "Point Keyflow at a folder (or upload tracks) and read every song's key, BPM, groove and energy.",
    "Set builder": "Your set in playing order — listen, reorder, and watch the energy flow.",
    "Inspector": "One track under the microscope: preview it, see what it mixes into, fix its key or BPM.",
    "Discover": "Find new tracks similar to the ones in your set, ranked by how well they'd mix in.",
    "Insights": "The big picture: which keys you're playing in and how everything pairs up.",
    "Data": "Every number behind the set, filterable and sortable.",
    "Export": "Take the set with you — files for any player, DJ software formats with Pro.",
    "Account": "Your profile and plan — link a license, upgrade, or sign out.",
}


def _start_session(user: dict) -> None:
    """Session-state login + persistent cookie so a refresh keeps you in.

    The cookie itself is written on the NEXT run (via ``_cookie_set``): writing
    it here and immediately calling ``st.rerun()`` tears the component iframe
    down before its script executes, so the cookie never lands.
    """
    auth.sign_in_session(user)
    token = auth.issue_session(user["id"])
    st.session_state["_session_token"] = token
    st.session_state["_cookie_set"] = token


def _render_auth_gate() -> None:
    """Sign-in / create-account / reset panel shown instead of the workspace."""
    from ui import mailer

    st.markdown(
        '<div class="setup-kicker">Welcome</div>'
        '<h2 class="setup-title">Sign in to your workspace</h2>'
        '<p class="setup-sub">Your plan, sets and preferences live with your account. '
        'Creating one is free.</p>',
        unsafe_allow_html=True,
    )
    tab_in, tab_up, tab_reset = st.tabs(["Sign in", "Create account", "Forgot password"])

    with tab_in:
        with st.form("login_form"):
            email = st.text_input("Email", key="li_email")
            password = st.text_input("Password", type="password", key="li_pw")
            if st.form_submit_button("Sign in", type="primary", width="stretch"):
                user, error = auth.login(email, password)
                if user:
                    _start_session(user)
                    st.rerun()
                else:
                    st.error(error)

    with tab_up:
        with st.form("register_form"):
            name = st.text_input("Name / DJ name", key="rg_name")
            email = st.text_input("Email", key="rg_email")
            password = st.text_input("Password (8+ characters)", type="password", key="rg_pw")
            if st.form_submit_button("Create free account", type="primary", width="stretch"):
                user, error = auth.register(email, name, password)
                if user:
                    if mailer.configured():
                        code, _uid = auth.create_code(user["email"], "verify")
                        if code:
                            mailer.send_code(user["email"], code, "verify")
                    _start_session(user)
                    st.rerun()
                else:
                    st.error(error)

    with tab_reset:
        if not mailer.configured():
            st.info("Password reset sends a code by email, which isn't configured yet. "
                    "Set `smtp_host`, `smtp_user` and `smtp_password` in secrets to enable it.")
        email = st.text_input("Account email", key="fp_email")
        if st.button("Send reset code", width="stretch", key="fp_send",
                     disabled=not mailer.configured()):
            code, _uid = auth.create_code(email, "reset")
            if code:
                error = mailer.send_code(email.strip().lower(), code, "reset")
                st.error(error) if error else st.success("Code sent — check your inbox.")
            else:
                # Same message either way: don't leak which emails exist.
                st.success("Code sent — check your inbox.")
        with st.form("reset_form"):
            code = st.text_input("6-digit code", key="fp_code")
            new_pw = st.text_input("New password (8+ characters)", type="password", key="fp_new")
            if st.form_submit_button("Reset password", width="stretch"):
                user_id = auth.consume_code(email, "reset", code)
                if user_id is None:
                    st.error("That code isn't valid (or it expired — they last 15 minutes).")
                else:
                    error = auth.set_password(user_id, new_pw)
                    st.error(error) if error else st.success(
                        "Password updated — sign in with it now.")

    st.caption("Free plan: up to 50 tracks per analysis, harmonic ordering, CSV + M3U export. "
               "Pro unlocks unlimited tracks, Discover, energy curves and DJ-software exports.")


def _module_account() -> None:
    user = auth.current_user()
    plan = auth.ROLE_LABELS[user["role"]]

    m1, m2 = st.columns(2)
    with m1:
        components.render_metric("Signed in as", user["name"], user["email"])
    with m2:
        components.render_metric("Current plan", plan,
                                 "everything unlocked" if user["role"] != "free"
                                 else "50 tracks · no DJ exports")

    _divider()
    if user["role"] == "free":
        st.markdown('<div class="section-title">Upgrade</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Buy on Gumroad, then paste the license key '
                    'from your receipt — your account upgrades instantly.</p>',
                    unsafe_allow_html=True)
        pro_url = state.get_secret("gumroad_product_url", "TA_GUMROAD_PRODUCT_URL")
        life_url = state.get_secret("gumroad_lifetime_url", "TA_GUMROAD_LIFETIME_URL")
        c1, c2 = st.columns(2)
        with c1:
            if pro_url:
                st.link_button("Go Pro — $12/month", pro_url, type="primary", width="stretch")
            else:
                st.caption("Set `gumroad_product_url` in secrets to enable Pro checkout.")
        with c2:
            if life_url:
                st.link_button("Lifetime — $149 once", life_url, width="stretch")
            else:
                st.caption("Set `gumroad_lifetime_url` in secrets to enable Lifetime checkout.")

    st.markdown('<div class="section-title">License</div>', unsafe_allow_html=True)
    key = st.text_input("License key", key="acct_license",
                        placeholder="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX")
    if st.button("Link license to this account", width="stretch", key="acct_link"):
        status, message = auth.link_license(user, key)
        if status == "ok":
            st.success(message)
            st.rerun()
        elif status == "unreachable":
            st.warning(message)
        else:
            st.error(message)

    if not user.get("verified"):
        from ui import mailer

        _divider()
        st.markdown('<div class="section-title">Verify your email</div>', unsafe_allow_html=True)
        if mailer.configured():
            v1, v2 = st.columns([2, 1], vertical_alignment="bottom")
            with v1:
                vcode = st.text_input("6-digit code from your inbox", key="acct_vcode")
            with v2:
                if st.button("Resend code", width="stretch", key="acct_vresend"):
                    code, _uid = auth.create_code(user["email"], "verify")
                    error = mailer.send_code(user["email"], code, "verify") if code else "No account."
                    st.error(error) if error else st.toast("Code sent", icon="✉️")
            if st.button("Verify email", width="stretch", key="acct_verify"):
                if auth.consume_code(user["email"], "verify", vcode) is not None:
                    auth.mark_verified(user["id"])
                    st.success("Email verified — thanks!")
                    st.rerun()
                else:
                    st.error("That code isn't valid (or it expired).")
        else:
            st.caption("Email verification needs SMTP configured "
                       "(`smtp_host`/`smtp_user`/`smtp_password` in secrets).")

    _divider()
    if st.button("Sign out", key="acct_signout"):
        auth.revoke_session(st.session_state.get("_session_token"))
        st.session_state["_session_token"] = None
        st.session_state["_cookie_clear"] = True
        auth.sign_out()
        st.rerun()


def _module_card(title: str, desc: str, key: str, locked: bool = False) -> None:
    with st.container(border=True):
        cls = " ov-locked" if locked else ""
        st.markdown(
            f'<div class="{cls.strip()}"><p class="ov-card-title">{title}</p>'
            f'<p class="ov-card-desc">{desc}</p></div>',
            unsafe_allow_html=True,
        )
        if locked:
            st.caption("Unlocks after your first analysis.")
        else:
            st.button("Open  →", key=key, width="stretch",
                      on_click=state.goto_module, args=(title,))


def _module_overview() -> None:
    tracks = st.session_state.tracks

    if not tracks:
        st.markdown(
            '<div class="setup-kicker">Welcome</div>'
            '<h2 class="setup-title">Your harmonic mixing workspace</h2>'
            '<p class="setup-sub">Keyflow reads your music, then helps you build a set that '
            'flows. Everything starts with one analysis — here\'s the path:</p>'
            '<div class="setup-steps">'
            '<span><b>1</b> Analyze a folder or upload tracks</span>'
            '<span><b>2</b> Shape the set — order, energy, keys</span>'
            '<span><b>3</b> Export to your DJ software</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        cta, _ = st.columns([1.2, 2])
        with cta:
            st.button("Analyze your library  →", type="primary", width="stretch",
                      key="ov_start", on_click=state.goto_module, args=("Analyze",))
        _divider()
        st.markdown('<p class="section-hint">What unlocks after that first analysis:</p>',
                    unsafe_allow_html=True)
        for row_modules in (DATA_MODULES[:3], DATA_MODULES[3:]):
            for col, module in zip(st.columns(3, gap="medium"), row_modules):
                with col:
                    _module_card(module, MODULE_DESCRIPTIONS[module], f"ovlk_{module}", locked=True)
        return

    ordered = state.ensure_order()
    frames = state.build_result_frames(ordered)
    analysis_df = frames["analysis_df"]
    playlist_df = frames["playlist_df"]
    avg_bpm = analysis_df["bpm"].mean() if not analysis_df.empty else float("nan")
    avg_score = pd.to_numeric(
        playlist_df["transition_score_from_previous"], errors="coerce").mean()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        components.render_metric("Tracks analyzed", str(len(tracks)),
                                 f"{st.session_state.audio_file_count} files scanned")
    with m2:
        components.render_metric("Average tempo",
                                 f"{avg_bpm:.0f} BPM" if pd.notna(avg_bpm) else "—",
                                 "the set's centre of gravity")
    with m3:
        components.render_metric("Keys in play",
                                 str(analysis_df["camelot"].nunique() if not analysis_df.empty else 0),
                                 "fewer keys = easier mixing")
    with m4:
        components.render_metric("Set smoothness",
                                 f"{avg_score:.0f} / 115" if pd.notna(avg_score) else "—",
                                 "75+ seamless · <40 tricky")

    failed = st.session_state.failed_files
    if failed:
        with st.expander(f"{len(failed)} files could not be analyzed", expanded=False):
            for failure in failed:
                st.write(failure)

    # A glance at the set itself: energy arc, key coverage, transition callouts.
    spark_col, wheel_col, call_col = st.columns([1.2, 0.9, 1.1], gap="medium")
    with spark_col:
        with st.container(border=True):
            st.markdown('<div class="metric-label">Energy arc of the set</div>',
                        unsafe_allow_html=True)
            st.markdown(_energy_sparkline(ordered), unsafe_allow_html=True)
            st.caption("Opens mellow, lands loud — the build-up curve.")
    with wheel_col:
        with st.container(border=True):
            st.markdown('<div class="metric-label">Key coverage</div>', unsafe_allow_html=True)
            present = {t["camelot"] for t in ordered if t["camelot"]}
            st.markdown(
                f'<div class="an-wheel" style="max-width:180px;margin:0 auto">'
                f'{charts.camelot_wheel_svg(present)}</div>',
                unsafe_allow_html=True,
            )
    with call_col:
        with st.container(border=True):
            st.markdown('<div class="metric-label">Transition callouts</div>',
                        unsafe_allow_html=True)
            scores = pd.to_numeric(
                playlist_df["transition_score_from_previous"], errors="coerce")
            if scores.notna().any():
                best, worst = scores.idxmax(), scores.idxmin()
                st.markdown(
                    f"Smoothest: **{playlist_df.loc[best - 1, 'title'] if best > 0 else '—'} → "
                    f"{playlist_df.loc[best, 'title']}** ({scores[best]:.0f})")
                st.markdown(
                    f"Trickiest: **{playlist_df.loc[worst - 1, 'title'] if worst > 0 else '—'} → "
                    f"{playlist_df.loc[worst, 'title']}** ({scores[worst]:.0f})")
                st.caption("Rework the tricky one in Set builder or Inspector.")
            else:
                st.caption("Add more tracks to see transition highlights.")

    _divider()
    st.markdown('<div class="section-title">What next?</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Each module does one job — open the one that matches '
                'what you\'re trying to do.</p>', unsafe_allow_html=True)
    for row_modules in (DATA_MODULES[:3], DATA_MODULES[3:]):
        for col, module in zip(st.columns(3, gap="medium"), row_modules):
            with col:
                _module_card(module, MODULE_DESCRIPTIONS[module], f"ov_{module}")

    st.caption("Working on a different crate? Run a new analysis from the **Analyze** module — "
               "it replaces the current one.")


def _module_analyze() -> None:
    tracks = st.session_state.tracks
    if tracks:
        st.caption(f"Current analysis: **{len(tracks)} tracks**. Running a new one replaces it.")

    config = components.render_setup_panel()
    if config["run"]:
        run_analysis_flow(config)
    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    if config["run"] and st.session_state.tracks:
        st.success(f"Analyzed {len(st.session_state.tracks)} tracks — your set is ready.")
        c1, c2, _ = st.columns([1.2, 1, 1.8])
        with c1:
            st.button("Open Set builder  →", type="primary", width="stretch",
                      key="an_done_sb", on_click=state.goto_module, args=("Set builder",))
        with c2:
            st.button("See overview", width="stretch",
                      key="an_done_ov", on_click=state.goto_module, args=("Overview",))


def _render_locked(module: str) -> None:
    st.info(f"**{module}** needs an analysis first — {MODULE_DESCRIPTIONS[module].lower()}")
    cta, _ = st.columns([1.2, 2.8])
    with cta:
        st.button("Analyze your library  →", type="primary", width="stretch",
                  key=f"lk_{module}", on_click=state.goto_module, args=("Analyze",))


def _module_set_builder(frames: dict) -> None:
    playlist_df = frames["playlist_df"]
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown('<div class="section-title">Playlist order</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Use ▲ ▼ to reorder by hand.</p>', unsafe_allow_html=True)
        components.render_playlist_editor(playlist_df, show_audio=True)
    with right:
        st.markdown('<div class="section-title">Energy curve</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_energy_curve(playlist_df), width="stretch")
        st.markdown('<div class="section-title">Transition breakdown</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_transition_scores(playlist_df), width="stretch")


def _module_inspector(frames: dict) -> None:
    st.markdown('<div class="section-title">Track inspector</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Preview a track, see what it mixes into, or fix its key/BPM.</p>',
                unsafe_allow_html=True)
    components.render_track_inspector(frames["matrix_df"])


def _render_pro_gate(feature: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{feature}** is a **Pro** feature. Upgrade to unlock it — "
                    "or link an existing license in Account.")
        c1, c2, _ = st.columns([1, 1.4, 1.6])
        with c1:
            url = state.get_secret("gumroad_product_url", "TA_GUMROAD_PRODUCT_URL")
            if url:
                st.link_button("Go Pro", url, type="primary", width="stretch")
        with c2:
            st.button("Open Account →", key=f"gate_{feature}", width="stretch",
                      on_click=state.goto_module, args=("Account",))


def _module_discover(frames: dict) -> None:
    if not auth.entitled("discover"):
        _render_pro_gate("Discover")
        return

    tracks = st.session_state.tracks or []
    titles = [track["title"] for track in tracks]

    seed_col, btn_col = st.columns([3, 1], vertical_alignment="bottom")
    with seed_col:
        seed = st.selectbox("Find tracks similar to", titles, key="discover_seed")
    with btn_col:
        search = st.button("Find similar tracks", type="primary", width="stretch")

    reference = next((t for t in tracks if t["title"] == seed), None)

    if search and reference:
        with st.spinner("Asking the music graph…"):
            suggestions, note = state.fetch_suggestions(reference)
        st.session_state["discover_results"] = {"seed": seed, "suggestions": suggestions, "note": note}

    results = st.session_state.get("discover_results")
    if results and results["seed"] == seed:
        components.render_suggestion_cards(results["suggestions"], results["note"])
    elif not search:
        st.markdown(
            '<p class="section-hint">Suggestions come from what real listeners play together '
            '(Last.fm / ListenBrainz), then get scored for key &amp; BPM fit against your seed track.</p>',
            unsafe_allow_html=True,
        )

    if not state.get_secret("lastfm_api_key", "TA_LASTFM_API_KEY"):
        st.caption("Tip: add a free `lastfm_api_key` in secrets for richer matches — "
                   "currently using open ListenBrainz data.")
    if not state.get_secret("getsongbpm_api_key", "TA_GETSONGBPM_KEY"):
        st.caption("Tip: add a `getsongbpm_api_key` to see key + BPM compatibility for suggestions.")


def _module_insights(frames: dict) -> None:
    playlist_df = frames["playlist_df"]
    wheel_col, scatter_col = st.columns(2, gap="large")
    with wheel_col:
        st.markdown('<div class="section-title">Camelot wheel</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-hint">Lit keys are in your set.</p>', unsafe_allow_html=True)
        present = {c for c in playlist_df["camelot"] if c}
        st.markdown(
            f'<div class="an-wheel">{charts.camelot_wheel_svg(present)}</div>',
            unsafe_allow_html=True,
        )
    with scatter_col:
        st.markdown('<div class="section-title">BPM vs energy map</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.plot_bpm_energy_scatter(frames["analysis_df"]), width="stretch")

    st.markdown('<div class="section-title">Transition compatibility heatmap</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-hint">Every pairing at a glance — brighter cells mix more smoothly.</p>',
                unsafe_allow_html=True)
    st.plotly_chart(charts.plot_transition_heatmap(frames["matrix_df"]), width="stretch")


def _module_data(frames: dict) -> None:
    tab_analysis, tab_playlist, tab_matrix = st.tabs(
        ["Track analysis", "Playlist table", "Transition matrix"]
    )
    with tab_analysis:
        query = st.text_input("Filter tracks", key="analysis_filter", placeholder="search title / key…")
        table = frames["analysis_df"]
        if query:
            mask = table.apply(
                lambda r: query.lower() in " ".join(map(str, r.values)).lower(), axis=1
            )
            table = table[mask]
        st.dataframe(table, width="stretch", hide_index=True,
                     column_config=components.analysis_column_config())
    with tab_playlist:
        st.dataframe(frames["playlist_df"], width="stretch", hide_index=True,
                     column_config=components.playlist_column_config())
    with tab_matrix:
        st.caption(
            "Each cell scores mixing **from** the row track **into** the column track "
            "(out of ~115 — higher is smoother). Hover any column header in the other tabs "
            "for what each metric means."
        )
        st.dataframe(frames["matrix_df"], width="stretch")


def _module_export(frames: dict, ordered: list[dict]) -> None:
    render_downloads(frames)
    _divider()
    premium.render_premium_export_section(frames, ordered)


def analyzer_page() -> None:
    st.markdown(ANALYZER_CSS, unsafe_allow_html=True)

    # Deferred cookie writes (see _start_session for why they can't happen
    # in the same run as a st.rerun()).
    pending_token = st.session_state.pop("_cookie_set", None)
    if pending_token:
        components.set_session_cookie(pending_token, auth.SESSION_TTL)
    if st.session_state.pop("_cookie_clear", False):
        components.clear_session_cookie()

    # Survive hard refreshes: restore the session from the browser cookie.
    if auth.current_user() is None:
        token = components.read_session_cookie()
        user = auth.restore_session(token)
        if user:
            auth.sign_in_session(user)
            st.session_state["_session_token"] = token

    if auth.current_user() is None:
        _render_auth_gate()
        return

    module = st.session_state.get("an_module") or "Overview"
    if module not in MODULES:
        module = "Overview"
    components.render_sidebar_nav(MODULES, module)
    render_page_header(module)

    if module == "Overview":
        _module_overview()
        return
    if module == "Analyze":
        _module_analyze()
        return
    if module == "Account":
        _module_account()
        return

    # Data modules need an analysis to exist.
    if st.session_state.tracks is None:
        _render_locked(module)
        return

    ordered = state.ensure_order()
    if not ordered:
        st.warning("Every track is excluded — clear some exclusions in the control bar.")
        return
    frames = state.build_result_frames(ordered)

    components.render_control_bar()
    render_status_chips(frames, ordered)

    if module == "Set builder":
        _module_set_builder(frames)
    elif module == "Inspector":
        _module_inspector(frames)
    elif module == "Discover":
        _module_discover(frames)
    elif module == "Insights":
        _module_insights(frames)
    elif module == "Data":
        _module_data(frames)
    else:
        _module_export(frames, ordered)

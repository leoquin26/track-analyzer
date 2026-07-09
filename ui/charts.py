"""Chart builders for the dashboard: Plotly figures + the SVG Camelot wheel."""

from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from harmonic_playlist import CAMELOT_MAJOR, CAMELOT_MINOR

from .styles import ACCENT, ACCENT_2, COMPONENT_COLORS

# Camelot wheel geometry (shared by the landing hero and the analyzer).
_CX = _CY = 200
_RINGS = [(132, 190, "B"), (74, 128, "A")]  # (inner r, outer r, Camelot letter)
_GAP_DEG = 1.4


def _annular(r_in: float, r_out: float, a0: float, a1: float) -> str:
    a0r, a1r = math.radians(a0), math.radians(a1)
    x0o, y0o = _CX + r_out * math.cos(a0r), _CY + r_out * math.sin(a0r)
    x1o, y1o = _CX + r_out * math.cos(a1r), _CY + r_out * math.sin(a1r)
    x1i, y1i = _CX + r_in * math.cos(a1r), _CY + r_in * math.sin(a1r)
    x0i, y0i = _CX + r_in * math.cos(a0r), _CY + r_in * math.sin(a0r)
    return (
        f"M {x0o:.2f} {y0o:.2f} A {r_out} {r_out} 0 0 1 {x1o:.2f} {y1o:.2f} "
        f"L {x1i:.2f} {y1i:.2f} A {r_in} {r_in} 0 0 0 {x0i:.2f} {y0i:.2f} Z"
    )


def camelot_wheel_svg(present: set[str] | None = None) -> str:
    """Spectrum Camelot wheel. ``present=None`` lights every key (landing hero);
    a set of Camelot codes lights only those keys and dims the rest (analyzer)."""
    segments: list[str] = []
    labels: list[str] = []
    for r_in, r_out, letter in _RINGS:
        for i in range(12):
            code = f"{i + 1}{letter}"
            lit = present is None or code in present
            a0 = -90 + i * 30 + _GAP_DEG / 2
            a1 = -90 + (i + 1) * 30 - _GAP_DEG / 2
            hue = (i / 12) * 360
            fill = (
                f"hsl({hue:.0f} 68% {'56%' if letter == 'B' else '46%'})"
                if lit else "rgba(255,255,255,0.05)"
            )
            text_fill = "#14121a" if lit else "rgba(255,255,255,0.3)"
            segments.append(
                f'<path d="{_annular(r_in, r_out, a0, a1)}" fill="{fill}" '
                f'stroke="#14121a" stroke-width="1.5"/>'
            )
            amid = math.radians((a0 + a1) / 2)
            rmid = (r_in + r_out) / 2
            lx, ly = _CX + rmid * math.cos(amid), _CY + rmid * math.sin(amid)
            labels.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{text_fill}" font-size="12" '
                f'font-weight="700" font-family="DM Mono, monospace" '
                f'text-anchor="middle" dominant-baseline="central">{code}</text>'
            )
    hub = (
        f'<circle cx="{_CX}" cy="{_CY}" r="70" fill="#171420" '
        f'stroke="rgba(255,255,255,0.12)" stroke-width="1"/>'
        f'<text x="{_CX}" y="{_CY - 5}" fill="#fff" font-size="15" font-weight="700" '
        f'font-family="Outfit, sans-serif" text-anchor="middle">CAMELOT</text>'
        f'<text x="{_CX}" y="{_CY + 15}" fill="{ACCENT}" font-size="10" letter-spacing="3" '
        f'font-family="DM Mono, monospace" text-anchor="middle">WHEEL</text>'
    )
    return (
        '<svg viewBox="0 0 400 400" class="wheel-svg" role="img" '
        'aria-label="Camelot wheel of musical keys" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(segments)}{hub}{"".join(labels)}</svg>'
    )

_DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=30, b=20),
)


def plot_transition_scores(playlist_df: pd.DataFrame) -> go.Figure:
    transitions = playlist_df[playlist_df["order"] > 1].copy()
    if transitions.empty:
        return go.Figure().update_layout(**_DARK_LAYOUT, height=360)

    labels = [
        f'{int(row["order"] - 1)} → {int(row["order"])}'
        for _, row in transitions.iterrows()
    ]

    fig = go.Figure()
    for component, color in COMPONENT_COLORS.items():
        fig.add_trace(
            go.Bar(
                name=component.capitalize(),
                x=labels,
                y=transitions[f"{component}_score"].astype(float),
                marker_color=color,
            )
        )

    fig.update_layout(
        **_DARK_LAYOUT,
        barmode="stack",
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_title="Transition",
        yaxis_title="Score contribution",
    )
    return fig


def plot_energy_curve(playlist_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=playlist_df["order"],
            y=playlist_df["energy"].astype(float),
            mode="lines+markers",
            line=dict(color=ACCENT, width=3, shape="spline"),
            marker=dict(size=9, color=ACCENT_2, line=dict(color="#14121a", width=1)),
            fill="tozeroy",
            fillcolor="rgba(94, 234, 212, 0.08)",
            hovertext=playlist_df["title"],
            hovertemplate="%{hovertext}<br>energy %{y:.1f} dB<extra></extra>",
        )
    )
    fig.update_layout(
        **_DARK_LAYOUT,
        height=280,
        xaxis_title="Set position",
        yaxis_title="Energy (dB)",
    )
    fig.update_xaxes(dtick=1)
    return fig


def plot_transition_heatmap(matrix_df: pd.DataFrame) -> go.Figure:
    numeric = matrix_df.apply(pd.to_numeric, errors="coerce")
    fig = px.imshow(
        numeric,
        text_auto=".0f",
        color_continuous_scale=[
            [0.0, "#181523"],
            [0.35, "#5b4b9e"],
            [0.65, "#2f8f7d"],
            [1.0, "#5eead4"],
        ],
        aspect="auto",
    )
    fig.update_layout(**_DARK_LAYOUT, height=520)
    fig.update_xaxes(tickangle=45)
    return fig


def plot_bpm_energy_scatter(analysis_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        analysis_df,
        x="bpm",
        y="energy",
        color="camelot",
        hover_data=["title", "key", "onset_rate"],
        size="key_strength",
        size_max=24,
    )
    fig.update_layout(
        **_DARK_LAYOUT,
        height=360,
        xaxis_title="BPM",
        yaxis_title="Energy (dB)",
        legend_title_text="Camelot",
    )
    return fig



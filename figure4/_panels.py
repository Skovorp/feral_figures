"""Standalone-panel renderers for figure 4.

Each panel function builds its own matplotlib Figure sized in CSS px @
96 DPI, saves it as an SVG. figure4.html + build.py compose them via
absolute CSS positioning and rasterize through headless Chrome.

Panel letters are drawn by the HTML overlay (`<div class="letter">`),
not by matplotlib. We monkey-patch `_style.panel_label` to no-op below.
"""
from __future__ import annotations

import os
import sys
import matplotlib.pyplot as plt

HERE_ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE_))
sys.path.insert(0, HERE_)

# Silence in-panel letters (drawn by HTML overlays instead).
import _style  # noqa: E402
_style.panel_label = lambda *a, **kw: None

from figure4 import (                                               # noqa: E402
    HERE, load_json, panel_a, panel_b, panel_c, panel_d,
    panel_e, panel_f, panel_g, panel_h,
)
from _style import apply_rcparams                                   # noqa: E402

PANELS_DIR = os.path.join(HERE, "panels")
os.makedirs(PANELS_DIR, exist_ok=True)


# Panel sizes (CSS pixels at 96 DPI). Tweak here, not in HTML.
SIZES = {
    "a": (340, 200),    # 3 thumbnail tiles + legend dots above
    "b": (490, 220),    # 2 example videos (ethograms)
    "c": (340, 200),    # stacked bars per video
    "d": (340, 220),    # paired boxplot
    "e": (490, 380),    # 3x3 monkey grid (image asset, lots of internal padding)
    "f": (820, 200),    # multi-row ethogram across many videos
    "g": (490, 220),    # stacked bars per monkey video
    "h": (310, 220),    # mAP bars + data proportion line (dual axis)
}


def _new_fig(name: str) -> plt.Figure:
    apply_rcparams()
    w, h = SIZES[name]
    return plt.figure(figsize=(w / 96, h / 96), dpi=96)


def _save_svg(fig: plt.Figure, name: str) -> str:
    """bbox_inches='tight' so labels/titles outside axes bounds aren't
    clipped by the SVG canvas. CSS uses object-fit:contain to scale."""
    out = os.path.join(PANELS_DIR, f"{name}.svg")
    fig.savefig(out, format="svg", bbox_inches="tight", pad_inches=0.02,
                facecolor="white")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
def render_a():
    fig = _new_fig("a")
    zebra = load_json("zebra.json")
    gs = fig.add_gridspec(2, 1, height_ratios=[0.22, 1.0], hspace=0.10,
                          left=0.04, right=0.98, top=0.95, bottom=0.04)
    ax_dots = fig.add_subplot(gs[0])
    thumbs_gs = gs[1].subgridspec(1, 3, wspace=0.06)
    ax_thumbs = [fig.add_subplot(thumbs_gs[0, i]) for i in range(3)]
    panel_a(ax_dots, ax_thumbs, zebra)
    return _save_svg(fig, "a")


def render_b():
    fig = _new_fig("b")
    zebra = load_json("zebra.json")
    gs = fig.add_gridspec(
        8, 1,
        height_ratios=[0.28, 0.40, 0.40, 0.20, 0.30, 0.40, 0.40, 0.30],
        hspace=0.25,
        left=0.10, right=0.99, top=0.95, bottom=0.08,
    )
    axes_b = {
        "t1": fig.add_subplot(gs[0]),
        "l1": fig.add_subplot(gs[1]),
        "p1": fig.add_subplot(gs[2]),
        "f1": fig.add_subplot(gs[3]),
        "t2": fig.add_subplot(gs[4]),
        "l2": fig.add_subplot(gs[5]),
        "p2": fig.add_subplot(gs[6]),
        "f2": fig.add_subplot(gs[7]),
    }
    panel_b(axes_b, zebra)
    return _save_svg(fig, "b")


def render_c():
    fig = _new_fig("c")
    zebra = load_json("zebra.json")
    # Generous bottom margin to fit the "correctly labelled / error" legend
    # below the bars (panel_c places it at bbox_to_anchor=(0.5, -0.32)).
    ax = fig.add_axes([0.13, 0.32, 0.85, 0.58])
    panel_c(ax, zebra)
    return _save_svg(fig, "c")


def render_d():
    fig = _new_fig("d")
    zebra = load_json("zebra.json")
    ax = fig.add_axes([0.18, 0.20, 0.78, 0.68])
    panel_d(ax, zebra)
    return _save_svg(fig, "d")


def render_e():
    fig = _new_fig("e")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.94])
    panel_e(ax)
    return _save_svg(fig, "e")


def render_f():
    fig = _new_fig("f")
    monkeys = load_json("monkeys.json")
    ax = fig.add_axes([0.05, 0.10, 0.93, 0.78])
    panel_f(ax, monkeys)
    return _save_svg(fig, "f")


def render_g():
    fig = _new_fig("g")
    monkeys = load_json("monkeys.json")
    # Bottom margin for the legend below the bars.
    ax = fig.add_axes([0.08, 0.30, 0.90, 0.60])
    panel_g(ax, monkeys)
    return _save_svg(fig, "g")


def render_h():
    fig = _new_fig("h")
    monkeys = load_json("monkeys.json")
    # Wide left/right margins for the dual-y-axis labels.
    ax = fig.add_axes([0.18, 0.40, 0.65, 0.50])
    panel_h(ax, monkeys)
    return _save_svg(fig, "h")


# ---------------------------------------------------------------------------
RENDERERS = {
    "a": render_a, "b": render_b, "c": render_c, "d": render_d,
    "e": render_e, "f": render_f, "g": render_g, "h": render_h,
}


def render_all(only: list[str] | None = None) -> list[str]:
    out = []
    for name, fn in RENDERERS.items():
        if only is not None and name not in only:
            continue
        path = fn()
        print(f"  panel {name}: {path}")
        out.append(path)
    return out


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    render_all(only)

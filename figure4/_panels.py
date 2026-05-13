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
from _render import save_svg                                        # noqa: E402

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
    """Figure with constrained_layout AND explicit padding so the top-most
    tick label (e.g. panel d's "17500") gets clear breathing room from
    the figure edge — without padding, matplotlib places the tick right
    at the top of the SVG.

    `h_pad=0.05` ≈ 7 pt of vertical padding inside the figure.
    `w_pad=0.05` ≈ 7 pt of horizontal padding.
    """
    apply_rcparams()
    w, h = SIZES[name]
    fig = plt.figure(figsize=(w / 96, h / 96), dpi=96, layout="constrained")
    fig.get_layout_engine().set(h_pad=0.15, w_pad=0.08)
    return fig


def _save_svg(fig: plt.Figure, name: str) -> str:
    """Save SVG without `bbox_inches='tight'` — constrained_layout already
    sized the figure with proper padding; `tight` would crop that padding
    back away (the cause of panel d's earlier "17500"-clipping problem)."""
    return save_svg(fig, os.path.join(PANELS_DIR, f"{name}.svg"),
                    tight=False)


# ---------------------------------------------------------------------------
def render_a():
    fig = _new_fig("a")
    zebra = load_json("zebra.json")
    gs = fig.add_gridspec(2, 1, height_ratios=[0.22, 1.0], hspace=0.10)
    ax_dots = fig.add_subplot(gs[0])
    thumbs_gs = gs[1].subgridspec(1, 3, wspace=0.06)
    ax_thumbs = [fig.add_subplot(thumbs_gs[0, i]) for i in range(3)]
    panel_a(ax_dots, ax_thumbs, zebra, show_legend=False)
    return _save_svg(fig, "a")


def render_b():
    fig = _new_fig("b")
    zebra = load_json("zebra.json")
    gs = fig.add_gridspec(
        8, 1,
        height_ratios=[0.28, 0.40, 0.40, 0.20, 0.30, 0.40, 0.40, 0.30],
        hspace=0.25,
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
    ax = fig.subplots()
    panel_c(ax, zebra)
    return _save_svg(fig, "c")


def render_d():
    fig = _new_fig("d")
    zebra = load_json("zebra.json")
    ax = fig.subplots()
    panel_d(ax, zebra)
    return _save_svg(fig, "d")


def render_e():
    fig = _new_fig("e")
    ax = fig.subplots()
    panel_e(ax)
    return _save_svg(fig, "e")


def render_f():
    fig = _new_fig("f")
    monkeys = load_json("monkeys.json")
    ax = fig.subplots()
    panel_f(ax, monkeys)
    return _save_svg(fig, "f")


def render_g():
    fig = _new_fig("g")
    monkeys = load_json("monkeys.json")
    ax = fig.subplots()
    panel_g(ax, monkeys)
    return _save_svg(fig, "g")


def render_h():
    fig = _new_fig("h")
    monkeys = load_json("monkeys.json")
    ax = fig.subplots()
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

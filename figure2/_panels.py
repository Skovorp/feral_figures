"""Standalone-panel renderers for figure 2.

Each function builds ONE panel as its own matplotlib Figure (sized in
CSS pixels at 96 DPI) and saves it as SVG. The SVGs are composed into
the final figure via figure2.html + Chrome headless.

Why CSS pixels at 96 DPI?
  Browsers treat 1 CSS px = 1/96 in. By matching matplotlib's figsize
  (inches) to the SVG's CSS-pixel size, the rendered panels land at
  exactly the dimensions the HTML expects — no scaling artefacts.

To tweak a panel size, change W/H constants here. To move a panel,
edit figure2.html (CSS — absolute positioning).
"""
from __future__ import annotations

import os
import matplotlib.pyplot as plt

import sys
HERE_ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE_))
sys.path.insert(0, HERE_)

# IMPORTANT: silence the in-panel letter (a/b/c/...) before importing the
# panel functions. Letters are drawn by the HTML composition layer
# (figure2.html) so they can't be clipped at SVG edges.
import _style  # noqa: E402
_style.panel_label = lambda *a, **kw: None

from figure2 import (                                               # noqa: E402
    HERE, load_data,
    panel_a, panel_b, panel_c, panel_d,
    panel_e, panel_f, panel_g, panel_h,
)
from _style import apply_rcparams                                   # noqa: E402
from _render import save_svg                                        # noqa: E402

PANELS_DIR = os.path.join(HERE, "panels")
os.makedirs(PANELS_DIR, exist_ok=True)


# Panel sizes (CSS pixels at 96 DPI). Tweak here, not in HTML.
SIZES = {
    "a": (225, 175),     # just the cage photo (legend is HTML)
    "b": (555, 260),
    "c": (200, 260),
    "d": (290, 260),
    "e": (290, 280),
    "f": (255, 235),
    "g": (300, 235),
    "h": (200, 235),
}


def _new_fig(name: str) -> plt.Figure:
    """Figure with constrained_layout — matplotlib auto-pads margins so
    NOTHING gets clipped (top tick labels, rotated x-tick labels, legend
    below, twin-axis labels, etc.)."""
    apply_rcparams()
    w, h = SIZES[name]
    return plt.figure(figsize=(w / 96, h / 96), dpi=96,
                      layout="constrained")


def _save_svg(fig: plt.Figure, name: str) -> str:
    """Save SVG with NO cropping — see `figures/_render.save_svg`."""
    return save_svg(fig, os.path.join(PANELS_DIR, f"{name}.svg"))


# ---------------------------------------------------------------------------
def render_a():
    """Just the cage photo — the legend box is composed in HTML."""
    fig = _new_fig("a")
    ax = fig.subplots()
    panel_a(ax, ax_legend=None)
    return _save_svg(fig, "a")


def render_b():
    fig = _new_fig("b")
    data = load_data()
    gs = fig.add_gridspec(
        7, 2,
        height_ratios=[0.30, 0.55, 0.55, 0.28, 0.30, 0.55, 0.55],
        width_ratios=[0.10, 1.00],
        hspace=0.12, wspace=0.0,
    )
    axes_b = [
        {"title":      fig.add_subplot(gs[0, :]),
         "lbl_label":  fig.add_subplot(gs[1, 0]),
         "lbl":        fig.add_subplot(gs[1, 1]),
         "pred_label": fig.add_subplot(gs[2, 0]),
         "pred":       fig.add_subplot(gs[2, 1])},
        {"title":      fig.add_subplot(gs[4, :]),
         "lbl_label":  fig.add_subplot(gs[5, 0]),
         "lbl":        fig.add_subplot(gs[5, 1]),
         "pred_label": fig.add_subplot(gs[6, 0]),
         "pred":       fig.add_subplot(gs[6, 1])},
    ]
    panel_b(axes_b, data)
    return _save_svg(fig, "b")


def render_c():
    fig = _new_fig("c")
    data = load_data()
    ax = fig.subplots()
    panel_c(ax, data)
    return _save_svg(fig, "c")


def render_d():
    fig = _new_fig("d")
    data = load_data()
    ax = fig.subplots()
    panel_d(ax, data)
    return _save_svg(fig, "d")


def render_e():
    fig = _new_fig("e")
    data = load_data()
    gs = fig.add_gridspec(2, 1, height_ratios=[0.06, 1.0], hspace=0.30)
    cax = fig.add_subplot(gs[0])
    ax = fig.add_subplot(gs[1])
    panel_e(ax, data, cax)
    return _save_svg(fig, "e")


def render_f():
    fig = _new_fig("f")
    data = load_data()
    ax = fig.subplots()
    panel_f(ax, data)
    return _save_svg(fig, "f")


def render_g():
    fig = _new_fig("g")
    ax = fig.subplots()
    panel_g(ax)
    return _save_svg(fig, "g")


def render_h():
    fig = _new_fig("h")
    data = load_data()
    ax = fig.subplots()
    panel_h(ax, data)
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
    import sys as _sys
    only = _sys.argv[1:] if len(_sys.argv) > 1 else None
    render_all(only)

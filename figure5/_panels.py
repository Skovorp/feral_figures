"""Standalone-panel renderers for figure 5.

Each function builds ONE panel (or a sub-piece) as its own matplotlib
Figure sized in CSS pixels at 96 DPI, then saves it as SVG. The SVGs are
composed into the final figure by figure5.html (CSS positioning) and
build.py (Chrome headless rasterization).

Panel c is split into:
  - c_matrix.svg  — the 2×2 confusion matrix + colorbar (matplotlib)
  - left + right thumbnails are loaded directly as <img> in HTML
    (the assets are already circular-masked PNGs)
  - the two curved arrows are inline SVG paths in figure5.html
"""
from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
import numpy as np

HERE_ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE_))
sys.path.insert(0, HERE_)

# Silence in-panel letters (drawn by HTML overlays instead).
import _style  # noqa: E402
_style.panel_label = lambda *a, **kw: None

from figure5 import (                                               # noqa: E402
    HERE, load_collective_ants, load_all_maps,
    panel_a, panel_b, panel_d, panel_e,
    COLORS, _hide_spines,
)
from _style import apply_rcparams                                   # noqa: E402
from _render import save_svg                                        # noqa: E402

# We import the confusion-matrix drawing pieces from figure5 but invoke
# them in a stripped-down "matrix-only" axes set. Easier to inline the
# matrix drawing rather than refactor panel_c — see render_c_matrix below.
from matplotlib.colors import LinearSegmentedColormap

PANELS_DIR = os.path.join(HERE, "panels")
os.makedirs(PANELS_DIR, exist_ok=True)


# Panel sizes (CSS pixels at 96 DPI).
SIZES = {
    "a":         (170, 360),   # narrow, tall — two stacked petri boxes
    "b":         (560, 270),
    "c_matrix":  (240, 240),   # square: matrix + colorbar
    "d":         (490, 230),
    "e":         (260, 220),
}


def _new_fig(name: str) -> plt.Figure:
    apply_rcparams()
    w, h = SIZES[name]
    return plt.figure(figsize=(w / 96, h / 96), dpi=96)


def _save_svg(fig: plt.Figure, name: str) -> str:
    """Save SVG with NO cropping — see `figures/_render.save_svg`."""
    return save_svg(fig, os.path.join(PANELS_DIR, f"{name}.svg"))


# ---------------------------------------------------------------------------
def render_a():
    fig = _new_fig("a")
    # HTML draws the dot+text headers; matplotlib draws only the photos.
    # Tight hspace=0.04 makes the two petri boxes nearly touch (matches
    # the source figure where they sit close together).
    gs = fig.add_gridspec(
        2, 1, height_ratios=[1.0, 1.0], hspace=0.04,
        left=0.05, right=0.95, top=0.97, bottom=0.03,
    )
    ax_top_img = fig.add_subplot(gs[0])
    ax_bot_img = fig.add_subplot(gs[1])
    # Dummy axes for panel_a's signature (won't be drawn because
    # show_headers=False just hides them and never registers any artist).
    # We DON'T add them as subplots — they have no figure presence, so
    # they can't overlap with the image axes.
    import matplotlib.pyplot as _plt
    ax_top_dot = _plt.Axes(fig, [0, 0, 0.001, 0.001])
    ax_bot_dot = _plt.Axes(fig, [0, 0, 0.001, 0.001])
    panel_a(ax_top_dot, ax_top_img, ax_bot_dot, ax_bot_img, fig,
            show_headers=False)
    fig.canvas.draw()
    fig.canvas.draw()  # 2nd pass so draw-event hooks settle
    return _save_svg(fig, "a")


def render_b():
    fig = _new_fig("b")
    data = load_collective_ants()
    gs = fig.add_gridspec(
        4, 1,
        height_ratios=[0.32, 0.55, 0.55, 0.20],
        hspace=0.15,
        left=0.08, right=0.97, top=0.93, bottom=0.10,
    )
    ax_title  = fig.add_subplot(gs[0])
    ax_lbl    = fig.add_subplot(gs[1])
    ax_pred   = fig.add_subplot(gs[2])
    ax_frames = fig.add_subplot(gs[3])
    panel_b(ax_title, ax_lbl, ax_pred, data, ax_frames, fig=fig)
    fig.canvas.draw()
    return _save_svg(fig, "b")


def render_c_matrix():
    """Just the 2x2 confusion matrix + colorbar; thumbnails + arrows in HTML."""
    fig = _new_fig("c_matrix")
    data = load_collective_ants()

    gs = fig.add_gridspec(
        1, 2, width_ratios=[1.0, 0.10], wspace=0.10,
        left=0.30, right=0.84, top=0.85, bottom=0.20,
    )
    ax_cm   = fig.add_subplot(gs[0])
    ax_cbar = fig.add_subplot(gs[1])

    # Compute combined confusion matrix
    all_g = np.concatenate([np.array(data["gt"][k]) for k in data["gt"]])
    all_p = np.concatenate([np.array(data["pred"][k]) for k in data["pred"]])
    cm_raw = np.zeros((2, 2), dtype=int)
    for gv in (0, 1):
        for pv in (0, 1):
            cm_raw[gv, pv] = int(((all_g == gv) & (all_p == pv)).sum())
    cm = np.array([
        [cm_raw[1, 1], cm_raw[1, 0]],
        [cm_raw[0, 1], cm_raw[0, 0]],
    ])
    mask_diag = np.eye(2, dtype=bool)
    off = np.where(mask_diag, np.nan, cm).astype(float)

    cmap = LinearSegmentedColormap.from_list(
        "blues", [COLORS["heatmap_lo"], COLORS["heatmap_hi"]]
    )
    cmap.set_bad(COLORS["diag_gray"])
    vmax = float(cm[~mask_diag].max())
    im = ax_cm.imshow(off, cmap=cmap, vmin=0, vmax=vmax, aspect="equal")

    for i in range(2):
        ax_cm.add_patch(patches.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                          facecolor=COLORS["diag_gray"],
                                          edgecolor="white", linewidth=0.5))
    for r in range(2):
        for c in range(2):
            v = cm[r, c]
            color = "white" if (not mask_diag[r, c] and v > vmax * 0.5) else "black"
            ax_cm.text(c, r, f"{v}", ha="center", va="center",
                       fontsize=9, color=color)

    ax_cm.set_xticks([0, 1]); ax_cm.set_yticks([0, 1])
    ax_cm.set_xticklabels(["raiding", "no raiding"], fontsize=8.5)
    ax_cm.set_yticklabels(["raiding", "no raiding"], fontsize=8.5,
                          rotation=0, ha="right", va="center")
    for tl, c in zip(ax_cm.get_xticklabels(),
                     [COLORS["raiding"], COLORS["no_raiding"]]):
        tl.set_color(c)
    for tl, c in zip(ax_cm.get_yticklabels(),
                     [COLORS["raiding"], COLORS["no_raiding"]]):
        tl.set_color(c)
    ax_cm.set_xlabel("predicted", labelpad=4, fontsize=9)
    ax_cm.set_ylabel("groundtruth", labelpad=4, fontsize=9)
    ax_cm.tick_params(length=0)
    for s in ax_cm.spines.values():
        s.set_visible(False)
    ax_cm.set_xlim(-0.5, 1.5); ax_cm.set_ylim(1.5, -0.5)

    cb = plt.colorbar(im, cax=ax_cbar, orientation="vertical")
    cb.set_ticks([0, 100, 200, 300])
    ax_cbar.tick_params(labelsize=8, length=2)
    ax_cbar.set_ylabel("misclassified frames", fontsize=8.5, labelpad=4)
    cb.outline.set_linewidth(0.5)

    return _save_svg(fig, "c_matrix")


def render_d():
    fig = _new_fig("d")
    maps = load_all_maps()
    # Generous bottom margin so rotated italic species names don't clip.
    ax = fig.add_axes([0.10, 0.45, 0.87, 0.42])
    panel_d(ax, maps)
    return _save_svg(fig, "d")


def render_e():
    fig = _new_fig("e")
    # Box-frame with arrow axes — needs internal padding for the
    # "harder/segmentation/easier" right-side stack.
    ax = fig.add_axes([0.13, 0.13, 0.80, 0.75])
    panel_e(ax)
    return _save_svg(fig, "e")


# ---------------------------------------------------------------------------
RENDERERS = {
    "a": render_a,
    "b": render_b,
    "c_matrix": render_c_matrix,
    "d": render_d,
    "e": render_e,
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

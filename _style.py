"""Shared style: colors, fonts, rcParams.

Matches the look of the original Illustrator-composed figures.
Tweaking values here propagates to every panel.
"""
from __future__ import annotations

import os
import matplotlib as mpl
from matplotlib import font_manager


COLORS = {
    "attack":      "#E66B3D",
    "investigate": "#3E9863",
    "mount":       "#83C2DD",
    "no_label":    "#5A5A5A",
    "feral":       "#83C2DD",
    "baseline":    "#B5B5B5",
    "correct":     "#C8B6D9",
    "error":       "#A8302C",
    "vigilant":    "#E66B3D",
    "out_of_sight":"#83D8C7",
    "raiding":     "#F0996E",
    "no_raiding":  "#5A5A5A",
    "predicted":   "#83C2DD",
    "groundtruth": "#3A3A3A",
    "heatmap_lo":  "#FFFFFF",
    "heatmap_hi":  "#1F3A8A",
    "diag_gray":   "#D6D6D6",
    "axis":        "#1A1A1A",
    "grid":        "#D6D6D6",
}


def _pick_font():
    """Arial only; warn loudly if it's not installed."""
    available = {f.name for f in font_manager.fontManager.ttflist}
    if "Arial" not in available:
        # Fall back to a metric-equivalent (Arimo) or sans-serif if Arial isn't on this box.
        for cand in ("Arimo", "Liberation Sans", "Helvetica", "DejaVu Sans"):
            if cand in available:
                return cand
        return "sans-serif"
    return "Arial"


FONT = _pick_font()


def apply_rcparams():
    # All text is Arial *regular* — no bold, no italic, anywhere.
    mpl.rcParams.update({
        "font.family": FONT,
        "font.weight": "normal",
        "font.style": "normal",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "normal",
        "axes.labelsize": 9,
        "axes.labelweight": "normal",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.titleweight": "normal",
        "axes.edgecolor": COLORS["axis"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": COLORS["axis"],
        "ytick.color": COLORS["axis"],
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "mathtext.default": "regular",
        "mathtext.fontset": "custom",
        "mathtext.rm": FONT,
        "mathtext.it": FONT,
        "mathtext.bf": FONT,
    })


def panel_label(ax, letter, *, x=-0.18, y=1.08, fontsize=15):
    """Lowercase panel letter (a, b, c, ...) in the top-left corner.

    Source figure uses bold panel letters — minor exception to the Arial
    regular rule for emphasis (matches the published figure).
    """
    ax.text(x, y, letter, transform=ax.transAxes,
            fontsize=fontsize, fontweight="bold",
            ha="left", va="bottom")


def style_value_label(ax, x, y, text, *, color="black", fontsize=8, dy=0.5):
    """Number above a bar."""
    ax.text(x, y + dy, text, ha="center", va="bottom",
            color=color, fontsize=fontsize)


HERE = os.path.dirname(os.path.abspath(__file__))


def asset(path: str) -> str:
    """Resolve an asset path relative to the figures/ root."""
    return os.path.join(HERE, path)

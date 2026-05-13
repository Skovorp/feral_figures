"""Figure 2 — CalMS21 mice.

Panels:
    a) cage photo + behavior-labels legend
    b) two example videos (labels vs prediction ethograms)
    c) mAP bar comparison: FERAL vs literature baselines
    d) per-video stacked bars (correct vs error)
    e) confusion matrix
    f) frames-per-class box plot (groundtruth vs predicted, paired)
    g) training-data scaling curve
    h) f1 comparison: FERAL vs reference baseline

All data-driven panels read figures/data/calms.json.
Numbers external to the data file (literature baselines, training-curve
points, reference-baseline f1) are hardcoded near where they're used.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _style import COLORS, apply_rcparams, panel_label  # noqa: E402


# ---------------------------------------------------------------------------
# Class color map for CalMS21 (keys are class indices in calms.json)
CLASS_COLORS = {
    0: COLORS["attack"],
    1: COLORS["investigate"],
    2: COLORS["mount"],
    3: COLORS["no_label"],
}
CLASS_DISPLAY = {0: "attack", 1: "investigate", 2: "mount", 3: "no label"}


# ---------------------------------------------------------------------------
def load_data():
    with open(os.path.join(HERE, "..", "data", "calms.json")) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
def panel_a(ax_photo, ax_legend=None):
    """Mouse cage photo + (optionally) behavior-labels legend box.

    The cage asset is 720x400 (aspect 1.8). We use aspect="equal" so the
    image is rendered at its native aspect ratio (no squish) — any extra
    space inside the gridspec slot becomes whitespace around the photo.

    When ax_legend is None, only the photo is drawn — the legend is
    composed in HTML (see figure2.html).
    """
    img = mpimg.imread(os.path.join(HERE, "assets", "mouse_cage.png"))
    ax_photo.imshow(img, aspect="equal")
    ax_photo.set_xticks([]); ax_photo.set_yticks([])
    for s in ax_photo.spines.values():
        s.set_visible(False)
    panel_label(ax_photo, "a", x=-0.08, y=1.02, fontsize=15)

    if ax_legend is None:
        return

    # Legend box
    ax_legend.set_xlim(0, 1); ax_legend.set_ylim(0, 1)
    ax_legend.set_xticks([]); ax_legend.set_yticks([])
    for s in ax_legend.spines.values():
        s.set_visible(False)

    box = patches.FancyBboxPatch(
        (0.02, 0.05), 0.96, 0.9,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=0.8, edgecolor=COLORS["axis"], facecolor="white",
        transform=ax_legend.transAxes,
    )
    ax_legend.add_patch(box)
    ax_legend.text(0.08, 0.85, "behavior labels", fontsize=9,
                   va="center", ha="left")

    # 2x2 layout: top row (no label / mount), bottom row (attack / investigate)
    # Dots use `scatter` (size in points²) so they render as true circles
    # regardless of the axes aspect — matplotlib's Circle patch with mixed
    # data ranges would squish.
    entries = [
        (0.08, 0.55, COLORS["no_label"],    "no label"),
        (0.48, 0.55, COLORS["mount"],       "mount"),
        (0.08, 0.27, COLORS["attack"],      "attack"),
        (0.48, 0.27, COLORS["investigate"], "investigate"),
    ]
    for x, y, c, lbl in entries:
        ax_legend.scatter([x], [y], s=120, c=c, edgecolors="none", zorder=3)
        ax_legend.text(x + 0.08, y, lbl, fontsize=9, va="center", ha="left")


# ---------------------------------------------------------------------------
def _ethogram_row(ax, arr):
    """Draw an ethogram strip as filled rectangles for run-length-encoded arr."""
    arr = np.asarray(arr)
    n = len(arr)
    if n == 0:
        return
    cuts = np.where(np.diff(arr) != 0)[0] + 1
    starts = np.concatenate(([0], cuts))
    ends = np.concatenate((cuts, [n]))
    for s, e in zip(starts, ends):
        ax.add_patch(patches.Rectangle(
            (s, 0), e - s, 1,
            facecolor=CLASS_COLORS[int(arr[s])], linewidth=0,
        ))


def _style_eth_ax(ax, n):
    ax.set_xlim(0, n); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def panel_b(axes_set, data):
    """Two ethogram pairs (labels vs prediction) with titles.

    axes_set is a list of dicts with keys: title, lbl, pred, lbl_label,
    pred_label. The *_label axes are dedicated narrow slots to the left of
    the strips that hold the row-label text — keeps the text from bleeding
    into the adjacent strip's axes region (which the layout check flags).
    """
    examples = [
        ("mouse073_task1_annotator1.mp4", "97.8"),
        ("mouse075_task1_annotator1.mp4", "93.5"),
    ]
    for i, ((vid, acc), axes) in enumerate(zip(examples, axes_set)):
        gt = data["gt"][vid]
        pred = data["pred"][vid]
        n = len(gt)

        ax_title = axes["title"]
        ax_l = axes["lbl"]
        ax_p = axes["pred"]
        ax_l_lbl = axes["lbl_label"]
        ax_p_lbl = axes["pred_label"]

        _ethogram_row(ax_l, gt)
        _ethogram_row(ax_p, pred)
        _style_eth_ax(ax_l, n)
        _style_eth_ax(ax_p, n)

        # Row labels — drawn inside their own dedicated narrow axes so the
        # text bbox cannot intrude into the strip-axes regions above/below.
        for ax_lbl, txt in [(ax_l_lbl, "labels"), (ax_p_lbl, "prediction")]:
            ax_lbl.set_xlim(0, 1); ax_lbl.set_ylim(0, 1)
            ax_lbl.set_xticks([]); ax_lbl.set_yticks([])
            for s in ax_lbl.spines.values():
                s.set_visible(False)
            ax_lbl.text(0.98, 0.5, txt, transform=ax_lbl.transAxes,
                        ha="right", va="center", fontsize=8.5)

        # Bottom frame range labels below prediction strip
        ax_p.text(0, -0.25, "0", transform=ax_p.transAxes,
                  ha="left", va="top", fontsize=7.5)
        ax_p.text(1, -0.25, str(n), transform=ax_p.transAxes,
                  ha="right", va="top", fontsize=7.5)

        # Bold italic title: "Example video N: accuracy XX.X%".
        # Source figure renders the entire title in bold italic; the
        # percentage is visually heavier but standard Arial bold-italic is
        # the closest we can get without a custom font.
        ax_title.set_xlim(0, 1); ax_title.set_ylim(0, 1)
        ax_title.text(0.0, 0.5,
                      f"Example video {i+1}: accuracy {acc}%",
                      transform=ax_title.transAxes,
                      ha="left", va="center", fontsize=11,
                      fontstyle="italic", fontweight="bold")
        ax_title.set_xticks([]); ax_title.set_yticks([])
        for s in ax_title.spines.values():
            s.set_visible(False)

        if i == 0:
            panel_label(ax_title, "b", x=-0.08, y=0.55, fontsize=15)

    # "frames" label under bottom strip
    last_pred = axes_set[-1]["pred"]
    last_pred.text(0.5, -0.85, "frames", transform=last_pred.transAxes,
                   ha="center", va="top", fontsize=9)


# ---------------------------------------------------------------------------
def panel_c(ax, data):
    """mAP comparison bars."""
    panel_label(ax, "c", x=-0.32, y=1.02, fontsize=15)
    feral_map = data["metrics"]["map"] * 100  # ~94.5
    vals = [feral_map, 88.9, 91.4, 91.5]
    labels = ["FERAL", "Baseline", "Top 1", "Google's Videoprism"]
    sublabels = ["", "(Sun et al. 2021)", "(Sun et al. 2021)", "(Zhao et al. 2025)"]
    colors_ = [COLORS["feral"], COLORS["baseline"], COLORS["baseline"], COLORS["baseline"]]

    x = np.arange(4)
    ax.bar(x, vals, color=colors_, width=0.7, linewidth=0)
    ax.set_ylim(86, 100)
    ax.set_yticks([86, 88, 90, 92, 94, 96, 98, 100])
    ax.set_ylabel("mAP (%)", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([""] * 4)

    # Value on top of each bar
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.25, f"{v:.1f}", ha="center", va="bottom",
                fontsize=9,
                color=COLORS["feral"] if xi == 0 else "black")

    # Rotated labels (30°), anchored at the right edge so they fan
    # diagonally below their bar. Italic citation is rendered as a
    # SECOND line of the same annotation (newline separated) so the
    # citation stays parallel to its label and can't overlap the next
    # bar's main label.
    label_colors = [COLORS["feral"], "black", "black", "black"]
    trans = ax.get_xaxis_transform()
    for xi, lbl, sub, col in zip(x, labels, sublabels, label_colors):
        ax.annotate(lbl, xy=(xi + 0.30, 0), xycoords=trans,
                    xytext=(0, -3), textcoords="offset points",
                    ha="right", va="top", rotation=30,
                    rotation_mode="anchor",
                    fontsize=8, color=col, annotation_clip=False)
        if sub:
            # Offset further along the rotated label's perpendicular so the
            # citation sits a clear line below the main label without
            # poking into the previous bar's text region.
            ax.annotate(sub, xy=(xi + 0.30, 0), xycoords=trans,
                        xytext=(-7, -16), textcoords="offset points",
                        ha="right", va="top", rotation=30,
                        rotation_mode="anchor",
                        fontsize=6, fontstyle="italic",
                        annotation_clip=False)

    ax.tick_params(axis="x", length=0, pad=2)
    ax.tick_params(axis="y", labelsize=9)


# ---------------------------------------------------------------------------
def panel_d(ax, data):
    """Stacked bars per video."""
    panel_label(ax, "d", x=-0.20, y=1.02, fontsize=15)
    pct_correct = []
    for v in data["gt"]:
        gt = np.array(data["gt"][v]); pr = np.array(data["pred"][v])
        pct_correct.append((gt == pr).mean() * 100)
    pct_correct = sorted(pct_correct, reverse=True)
    n = len(pct_correct)

    x = np.arange(n)
    # Slight gap between bars so individual videos read as separate units.
    ax.bar(x, pct_correct, color=COLORS["correct"], width=0.85, linewidth=0)
    errs = [100 - c for c in pct_correct]
    ax.bar(x, errs, bottom=pct_correct, color=COLORS["error"], width=0.85, linewidth=0)

    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("% of frames", fontsize=10)
    ax.set_xticks([])
    ax.set_xlabel("videos", fontsize=10)
    ax.set_xlim(-0.55, n - 0.45)
    ax.tick_params(axis="y", labelsize=9)

    h_correct = patches.Patch(facecolor=COLORS["correct"], label="correctly labelled")
    h_err = patches.Patch(facecolor=COLORS["error"], label="error")
    ax.legend(handles=[h_correct, h_err], loc="lower center",
              bbox_to_anchor=(0.5, -0.32), ncol=2, frameon=False,
              fontsize=9, handlelength=1.2, handleheight=1.2,
              columnspacing=1.5, handletextpad=0.6)


# ---------------------------------------------------------------------------
def panel_e(ax, data, cax):
    """4x4 confusion matrix."""
    # Panel letter placed up and to the left of the matrix (above colorbar
    # but not overlapping its title).
    panel_label(ax, "e", x=-0.30, y=1.50, fontsize=15)
    classes = [0, 1, 2, 3]
    cm = np.zeros((4, 4), dtype=int)
    for v in data["gt"]:
        gt = np.array(data["gt"][v]); pr = np.array(data["pred"][v])
        for g in classes:
            for p in classes:
                cm[g, p] += int(((gt == g) & (pr == p)).sum())

    mask_diag = np.eye(4, dtype=bool)
    off = np.where(mask_diag, np.nan, cm).astype(float)

    cmap = LinearSegmentedColormap.from_list(
        "blues", [COLORS["heatmap_lo"], COLORS["heatmap_hi"]]
    )
    cmap.set_bad(COLORS["diag_gray"])
    vmax = 5000
    # aspect="equal" makes cells square — matches source.
    im = ax.imshow(off, cmap=cmap, vmin=0, vmax=vmax, aspect="equal")

    # Diagonal cells: solid gray (overdraw) with subtle white borders
    for i in range(4):
        ax.add_patch(patches.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                       facecolor=COLORS["diag_gray"],
                                       edgecolor="white", linewidth=0.8))

    # Cell text. Diagonal numbers are still shown (matches source).
    for r in range(4):
        for c in range(4):
            v = cm[r, c]
            if mask_diag[r, c]:
                color = "black"
            else:
                color = "white" if v > vmax * 0.6 else "black"
            ax.text(c, r, f"{v}", ha="center", va="center",
                    fontsize=7.5, color=color)

    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels([CLASS_DISPLAY[c] for c in classes], rotation=45,
                       ha="right", rotation_mode="anchor", fontsize=9)
    ax.set_yticklabels([CLASS_DISPLAY[c] for c in classes], rotation=45,
                       ha="right", rotation_mode="anchor", fontsize=9)
    for tl, c in zip(ax.get_xticklabels(), classes):
        tl.set_color(CLASS_COLORS[c])
    for tl, c in zip(ax.get_yticklabels(), classes):
        tl.set_color(CLASS_COLORS[c])

    ax.set_xlabel("predicted", fontsize=10)
    ax.set_ylabel("groundtruth", fontsize=10)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlim(-0.5, 3.5); ax.set_ylim(3.5, -0.5)

    # Colorbar (horizontal, on top)
    cb = plt.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_ticks([0, 2000, 4000])
    cax.xaxis.set_ticks_position("top")
    cax.xaxis.set_label_position("top")
    cax.set_xlabel("misclassified frames", fontsize=10, labelpad=4)
    cax.tick_params(axis="x", labelsize=9, length=2, pad=2)
    cb.outline.set_linewidth(0.5)


# ---------------------------------------------------------------------------
def panel_f(ax, data):
    """Frames-per-class boxes with paired gt/predicted dots."""
    panel_label(ax, "f", x=-0.22, y=1.02, fontsize=15)
    behaviors = [0, 1, 2]

    gt_counts = {b: [] for b in behaviors}
    pr_counts = {b: [] for b in behaviors}
    for v in data["gt"]:
        gt = np.array(data["gt"][v]); pr = np.array(data["pred"][v])
        for b in behaviors:
            gt_counts[b].append(int((gt == b).sum()))
            pr_counts[b].append(int((pr == b).sum()))

    width = 0.34
    positions_gt = np.array([0, 1, 2]) - 0.22
    positions_pr = np.array([0, 1, 2]) + 0.22

    for i, b in enumerate(behaviors):
        gt_vals = np.array(gt_counts[b]) / 1000
        pr_vals = np.array(pr_counts[b]) / 1000

        # In the source, box outlines are BLACK (not colored by class).
        for vals, pos in [
            (gt_vals, positions_gt[i]),
            (pr_vals, positions_pr[i]),
        ]:
            ax.boxplot(
                [vals], positions=[pos], widths=width,
                patch_artist=True, showfliers=False,
                boxprops=dict(facecolor="white", edgecolor="black", linewidth=0.9),
                medianprops=dict(color="black", linewidth=0.9),
                whiskerprops=dict(color="black", linewidth=0.9),
                capprops=dict(color="black", linewidth=0.9),
            )

        rng = np.random.default_rng(i)
        jitter = rng.uniform(-0.05, 0.05, size=len(gt_vals))
        for g, p, j in zip(gt_vals, pr_vals, jitter):
            ax.plot([positions_gt[i] + j, positions_pr[i] + j], [g, p],
                    color="#9E9E9E", linewidth=0.5, zorder=1, alpha=0.7)
            ax.scatter([positions_gt[i] + j], [g], s=14,
                       color=COLORS["groundtruth"], zorder=3, linewidths=0)
            ax.scatter([positions_pr[i] + j], [p], s=14,
                       color=COLORS["predicted"], zorder=3, linewidths=0)

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["attack", "investigate", "mount"], fontsize=10,
                       rotation=30, ha="right", rotation_mode="anchor",
                       fontstyle="italic")
    for tl, b in zip(ax.get_xticklabels(), behaviors):
        tl.set_color(CLASS_COLORS[b])
    # Push the bottom slightly below 0 so the y=0 tick label sits above the
    # axis line (matches source typography).
    ax.set_ylim(-0.4, 10)
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.set_ylabel("frames (thousands)", fontsize=10)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5,
                  color=COLORS["grid"], alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlim(-0.6, 2.6)

    h_gt = patches.Patch(facecolor=COLORS["groundtruth"], label="groundtruth")
    h_pr = patches.Patch(facecolor=COLORS["predicted"], label="predicted")
    ax.legend(handles=[h_gt, h_pr], loc="lower center",
              bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False,
              fontsize=9, handlelength=1.2, handleheight=1.2,
              columnspacing=2.0, handletextpad=0.6)


# ---------------------------------------------------------------------------
def panel_g(ax):
    """Training-data scaling curve (hardcoded values)."""
    panel_label(ax, "g", x=-0.18, y=1.20, fontsize=15)

    pct = np.array([1, 5, 12, 25, 50])
    mins = np.array([5.5, 28, 67, 140, 280])
    maps = np.array([59.5, 83.0, 89.2, 92.8, 93.7])
    videoprism = 91.5

    # Horizontal dashed gridlines first so the curve sits on top.
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5,
                  color=COLORS["grid"], alpha=0.8)
    ax.set_axisbelow(True)

    # Linear x-axis: 25 sits halfway from 0 to 50, etc.
    ax.plot(pct, maps, "o-", color="black", linewidth=1.2, markersize=5,
            zorder=5)
    ax.axhline(videoprism, color=COLORS["feral"], linestyle="--",
               linewidth=1.0, zorder=4)

    ax.set_xlim(0, 52)
    ax.set_xticks(pct)
    ax.set_xticklabels([str(int(p)) for p in pct], fontsize=9)
    ax.minorticks_off()
    ax.set_xlabel("% training data used", fontsize=10)

    ax.set_ylim(55, 96)
    ax.set_yticks([55, 65, 75, 85, 95])
    ax.set_ylabel("mAP (%)", fontsize=10)
    ax.tick_params(axis="y", labelsize=9)

    # Top axis: labelled-data duration in minutes, aligned to the same
    # linear positions as the bottom axis (one duration per training-data %).
    secax = ax.twiny()
    secax.set_xlim(ax.get_xlim())
    secax.set_xticks(pct)
    def _fmt(m):
        return f"{m:g}"
    secax.set_xticklabels([_fmt(m) for m in mins], rotation=45, ha="left",
                          fontsize=9, rotation_mode="anchor")
    secax.minorticks_off()
    secax.set_xlabel("labelled data duration (mins)", fontsize=10, labelpad=14)
    secax.spines["top"].set_visible(True)
    secax.spines["right"].set_visible(False)
    secax.tick_params(axis="x", length=2, pad=2)

    # Legend below: short dashed swatch + label, anchored within the panel.
    ax.plot([0.18, 0.32], [-0.42, -0.42], transform=ax.transAxes,
            color=COLORS["feral"], linestyle="--", linewidth=1.2,
            clip_on=False)
    ax.text(0.34, -0.42, "Videoprism mAP (%)",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=9.5, color=COLORS["feral"], clip_on=False)


# ---------------------------------------------------------------------------
def panel_h(ax, data):
    """f1 comparison.

    NOTE: The source figure shows FERAL f1 = 92.0, but data["metrics"]["_f1"]
    in calms.json is ~0.893 (i.e. 89.3). The source value (92.0) is the
    macro-averaged per-class f1 reported in the paper. We use the source
    value here to match the published figure exactly. See the user's
    instructions: "prefer matching the source — so use 92.0 hardcoded".
    """
    panel_label(ax, "h", x=-0.40, y=1.02, fontsize=15)
    feral_f1 = 92.0  # from source figure (paper macro-f1); see docstring
    baseline_f1 = 75.8

    x = np.arange(2)
    ax.bar(x, [feral_f1, baseline_f1],
           color=[COLORS["feral"], COLORS["baseline"]], width=0.7, linewidth=0)
    ax.set_ylim(70, 100)
    ax.set_yticks([70, 80, 90, 100])
    ax.set_xticks(x)
    ax.set_xticklabels(["FERAL", "Reference\nBaseline"], fontsize=10)
    ax.get_xticklabels()[0].set_color(COLORS["feral"])
    ax.set_ylabel("f1 score", fontsize=10)
    ax.tick_params(axis="y", labelsize=9)

    # Dashed gridlines at 80, 90, 100
    ax.yaxis.grid(True, linestyle="--", linewidth=0.5,
                  color=COLORS["grid"], alpha=0.8)
    ax.set_axisbelow(True)

    for xi, v in zip(x, [feral_f1, baseline_f1]):
        ax.text(xi, v + 0.5, f"{v:.1f}", ha="center", va="bottom",
                fontsize=10,
                color=COLORS["feral"] if xi == 0 else "black")
    ax.tick_params(axis="x", length=0, pad=2)


# ---------------------------------------------------------------------------
def main(out=None):
    apply_rcparams()
    data = load_data()

    fig = plt.figure(figsize=(7.74, 8.33))

    # Master gridspec: 3 rows.
    # Inter-row spacing is intentionally tight — each panel handles its own
    # caption/legend padding within its slot.
    gs = fig.add_gridspec(
        3, 1, hspace=0.42,
        height_ratios=[1.00, 1.05, 1.05],
        left=0.07, right=0.975, top=0.975, bottom=0.085,
    )

    # ---- Row 1: panel a (left) | panel b (right) ----
    row1 = gs[0].subgridspec(1, 2, width_ratios=[1.0, 1.85], wspace=0.16)

    # Panel a: photo on top, legend below.
    a_sub = row1[0].subgridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.18)
    ax_photo = fig.add_subplot(a_sub[0])
    ax_legend = fig.add_subplot(a_sub[1])
    panel_a(ax_photo, ax_legend)

    # Panel b: two stacked groups of (title / labels / prediction).
    # 7 rows × 2 cols. The narrow spacer row (b_sub[3, :]) separates the two
    # videos. The narrow left column hosts row-label text (so it can't bleed
    # into the strip axes' region — `_layout_check.text_intrudes_into_axes`).
    b_sub = row1[1].subgridspec(
        7, 2,
        height_ratios=[0.30, 0.60, 0.60, 0.30, 0.30, 0.60, 0.60],
        width_ratios=[0.10, 1.00],
        hspace=0.12, wspace=0.0,
    )
    axes_b = [
        {"title":      fig.add_subplot(b_sub[0, :]),
         "lbl_label":  fig.add_subplot(b_sub[1, 0]),
         "lbl":        fig.add_subplot(b_sub[1, 1]),
         "pred_label": fig.add_subplot(b_sub[2, 0]),
         "pred":       fig.add_subplot(b_sub[2, 1])},
        {"title":      fig.add_subplot(b_sub[4, :]),
         "lbl_label":  fig.add_subplot(b_sub[5, 0]),
         "lbl":        fig.add_subplot(b_sub[5, 1]),
         "pred_label": fig.add_subplot(b_sub[6, 0]),
         "pred":       fig.add_subplot(b_sub[6, 1])},
    ]
    panel_b(axes_b, data)

    # ---- Row 2: c | d | e+colorbar ----
    row2 = gs[1].subgridspec(1, 3, width_ratios=[0.80, 1.05, 1.30],
                             wspace=0.55)
    ax_c = fig.add_subplot(row2[0])
    ax_d = fig.add_subplot(row2[1])
    # Panel e with a small colorbar slot on top.
    e_sub = row2[2].subgridspec(2, 1, height_ratios=[0.05, 1.0], hspace=0.30)
    cax_e = fig.add_subplot(e_sub[0])
    ax_e = fig.add_subplot(e_sub[1])
    panel_c(ax_c, data)
    panel_d(ax_d, data)
    panel_e(ax_e, data, cax_e)

    # ---- Row 3: f | g | h ----
    row3 = gs[2].subgridspec(1, 3, width_ratios=[1.10, 1.30, 1.00],
                             wspace=0.48)
    ax_f = fig.add_subplot(row3[0])
    ax_g = fig.add_subplot(row3[1])
    ax_h = fig.add_subplot(row3[2])
    panel_f(ax_f, data)
    panel_g(ax_g)
    panel_h(ax_h, data)

    # Resolve output path.
    if out is None:
        out_path = os.path.join(HERE, "figure2_remade.png")
    else:
        out_path = out if os.path.isabs(out) else os.path.join(HERE, out)

    fig.savefig(out_path, dpi=300)
    print(f"wrote {out_path}")
    return fig


if __name__ == "__main__":
    main()

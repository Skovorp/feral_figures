"""Figure 4 — zebras (top half) + monkeys (bottom half).

Top (panels a-d) reads figures/data/zebra.json (camera trap, 3 classes:
no_label / vigilant / out_of_sight).

Bottom (panels e-h) reads figures/data/monkeys.json (9 monkey behaviors,
short ~360-frame clips, 100 videos).

All plot styling routed through _style.apply_rcparams (Arial regular only).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
from sklearn.metrics import average_precision_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _style import COLORS, apply_rcparams, panel_label  # noqa: E402


# ---------------------------------------------------------------------------
# Source-figure-extracted palette (sampled from FIGURE4.png pixels).
# Locally overrides the shared style so this figure can be pixel-close
# without disturbing other figures in the project.
PAL = {
    "no_label":     "#59595C",  # dark gray
    "vigilant":     "#F49F7B",  # salmon orange
    "out_of_sight": "#91D1BC",  # mint teal
    "correct":      "#BFB3D8",  # lavender purple
    "error":        "#991B1E",  # deep red
    "feral":        "#7FB8E5",  # light blue (panel h bars, panel d pred)
    "predicted":    "#7FB8E5",
    "groundtruth":  "#1C1C1C",  # near-black dots
    "red_line":     "#ED2024",  # data-proportion line
    "grid":         "#D6D6D6",
    "light_gray":   "#EBECED",  # ethogram empty-row fill (panel f)
}

# Zebra class color map
ZEBRA_COLORS = {
    0: PAL["no_label"],
    1: PAL["out_of_sight"],
    2: PAL["vigilant"],
}
ZEBRA_DISPLAY = {0: "no label", 1: "out of sight", 2: "vigilant"}


# Monkey: 9 classes. Distinct colors matching the source figure palette.
# Class indices follow class_names in monkeys.json:
#   0=camera_interaction, 1=climbing_down, 2=climbing_up, 3=hanging,
#   4=running, 5=sitting, 6=sitting_on_back, 7=standing, 8=walking
MONKEY_COLORS = {
    0: "#1F5AA6",  # camera_interaction (dark blue)
    1: "#E97F2E",  # climbing_down (orange)
    2: "#7BC36A",  # climbing_up (green)
    3: "#F2856E",  # hanging (coral/peach)
    4: "#8C564B",  # running (brown)
    5: "#E36AAE",  # sitting (pink/magenta)
    6: "#A7A9AC",  # sitting_on_back (gray)
    7: "#DBDC8D",  # standing (yellow-olive)
    8: "#9EDAE6",  # walking (light cyan)
}
MONKEY_DISPLAY = {
    0: "camera interaction", 1: "climbing down", 2: "climbing up",
    3: "hanging", 4: "running", 5: "sitting", 6: "sitting on back",
    7: "standing", 8: "walking",
}
# Row order for panel f's per-class stripes — visually matches source:
# top to bottom = [camera_interaction, climbing_up, climbing_down, running,
# sitting, sitting_on_back, hanging, standing, walking].
MONKEY_F_ROW_ORDER = [0, 2, 1, 4, 5, 6, 3, 7, 8]


def load_json(name):
    with open(os.path.join(HERE, "..", "data", name)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
def _ethogram_strip(ax, arr, color_map, height=1.0, y=0.0):
    """Draw an ethogram strip from a 1-D int class array."""
    arr = np.asarray(arr)
    n = len(arr)
    if n == 0:
        return
    cuts = np.where(np.diff(arr) != 0)[0] + 1
    starts = np.concatenate(([0], cuts))
    ends = np.concatenate((cuts, [n]))
    for s, e in zip(starts, ends):
        ax.axvspan(s, e, ymin=y, ymax=y + height,
                   facecolor=color_map[int(arr[s])], linewidth=0)


# ---------------------------------------------------------------------------
def panel_a(ax_dots, ax_thumb_list, data, show_legend=True):
    """Legend row: 3 colored dots + labels above 3 thumbnails.

    `ax_thumb_list` is a list of 3 axes, one per thumbnail. Splitting into
    one axes per image lets each axes be (close to) square so the 250x250
    PNGs don't get stretched.

    When `show_legend=False`, the dot+label row is suppressed — the HTML
    layer (figure4.html) draws those overlays for crisp circle rendering.
    """
    panel_label(ax_dots, "a", x=-0.05, y=0.95, fontsize=12)

    # Hide the dots axes — we still pass it so the gridspec layout is
    # unchanged for the matplotlib-only render path.
    ax_dots.set_xlim(0, 3); ax_dots.set_ylim(0, 1)
    ax_dots.set_xticks([]); ax_dots.set_yticks([])
    for s in ax_dots.spines.values():
        s.set_visible(False)

    if show_legend:
        entries = [
            (0.25, PAL["no_label"], "no label"),
            (1.25, PAL["vigilant"], "vigilant"),
            (2.25, PAL["out_of_sight"], "out of sight"),
        ]
        for x, c, lbl in entries:
            ax_dots.add_patch(patches.Circle((x, 0.5), 0.16, facecolor=c,
                                             edgecolor="none",
                                             transform=ax_dots.transData))
            ax_dots.text(x + 0.22, 0.5, lbl, fontsize=9, va="center", ha="left")

    # Thumbnails — one axes per image so each cell is square.
    thumbs = [
        mpimg.imread(os.path.join(HERE, "assets", "thumb_no_label.png")),
        mpimg.imread(os.path.join(HERE, "assets", "thumb_vigilant.png")),
        mpimg.imread(os.path.join(HERE, "assets", "thumb_out_of_sight.png")),
    ]
    for ax_t, img in zip(ax_thumb_list, thumbs):
        ax_t.imshow(img, zorder=1)
        ax_t.set_xticks([]); ax_t.set_yticks([])
        for s in ax_t.spines.values():
            s.set_visible(False)
        ax_t.set_aspect("equal")


# ---------------------------------------------------------------------------
def panel_b(axes_b, data):
    """Two zebra example videos: labels vs prediction ethograms.

    axes_b is a dict with keys t1,l1,p1,t2,l2,p2.
    """
    panel_label(axes_b["t1"], "b", x=-0.04, y=1.0, fontsize=12)

    vid1 = "ob090-track-9.mp4"   # 57429 frames, 93.86% acc
    vid2 = "ob090-track-14.mp4"  # 56685 frames, 94.41% acc

    examples = [
        (vid1, axes_b["t1"], axes_b["l1"], axes_b["p1"], axes_b["f1"], 1),
        (vid2, axes_b["t2"], axes_b["l2"], axes_b["p2"], axes_b["f2"], 2),
    ]
    for vid, ax_t, ax_l, ax_p, ax_f, idx in examples:
        gt = np.array(data["gt"][vid])
        pr = np.array(data["pred"][vid])
        n = len(gt)
        acc = (gt == pr).mean() * 100

        for ax, arr in [(ax_l, gt), (ax_p, pr)]:
            _ethogram_strip(ax, arr, ZEBRA_COLORS, height=1.0, y=0.0)
            ax.set_xlim(0, n); ax.set_ylim(0, 1)
            ax.set_yticks([]); ax.set_xticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            # Transparent background so text drawn outside axes bbox via
            # neighbouring axes is not covered by a white patch.
            ax.patch.set_visible(False)

        # Dedicated frame-range axes (thin row below prediction strip).
        # Putting the text in its own axes prevents the labels from
        # bleeding into the next video block below.
        ax_f.set_xlim(0, 1); ax_f.set_ylim(0, 1)
        ax_f.set_xticks([]); ax_f.set_yticks([])
        for s in ax_f.spines.values():
            s.set_visible(False)
        ax_f.patch.set_visible(False)
        ax_f.text(0.0, 1.0, "0", transform=ax_f.transAxes,
                  ha="left", va="top", fontsize=9)
        ax_f.text(1.0, 1.0, str(n), transform=ax_f.transAxes,
                  ha="right", va="top", fontsize=9)

        # Row labels
        ax_l.text(-0.012, 0.5, "labels", transform=ax_l.transAxes,
                  ha="right", va="center", fontsize=9)
        ax_p.text(-0.012, 0.5, "prediction", transform=ax_p.transAxes,
                  ha="right", va="center", fontsize=9)

        # Title — italic per source. Percentage value rendered bold + italic.
        # Two text objects: prefix italic + suffix italic-bold, anchored
        # adjacently via the prefix's window extent.
        prefix = f"Example video {idx}: accuracy "
        t_prefix = ax_t.text(0.0, 0.5, prefix, transform=ax_t.transAxes,
                             ha="left", va="center", fontsize=10,
                             fontstyle="italic")
        # Draw figure once to populate renderer for measurement
        ax_t.figure.canvas.draw()
        bbox = t_prefix.get_window_extent()
        inv = ax_t.transAxes.inverted()
        x_after = inv.transform((bbox.x1, bbox.y0))[0]
        ax_t.text(x_after, 0.5, f"{acc:.1f}%",
                  transform=ax_t.transAxes,
                  ha="left", va="center", fontsize=10,
                  fontstyle="italic", fontweight="bold")

        ax_t.set_xticks([]); ax_t.set_yticks([])
        for s in ax_t.spines.values():
            s.set_visible(False)
        ax_t.patch.set_visible(False)

    # "frames" centered under the bottom strip, drawn inside the dedicated
    # frame-range axes of the second video.
    axes_b["f2"].text(0.5, -0.4, "frames", transform=axes_b["f2"].transAxes,
                      ha="center", va="top", fontsize=10, clip_on=False)


# ---------------------------------------------------------------------------
def panel_c(ax, data):
    """Stacked bars per zebra video: % correct vs error."""
    panel_label(ax, "c", x=-0.24, y=1.05, fontsize=12)

    pct_correct = []
    for v in data["gt"]:
        gt = np.array(data["gt"][v]); pr = np.array(data["pred"][v])
        pct_correct.append((gt == pr).mean() * 100)
    pct_correct = sorted(pct_correct, reverse=True)
    n = len(pct_correct)

    x = np.arange(n)
    ax.bar(x, pct_correct, color=PAL["correct"], width=0.85, linewidth=0)
    errs = [100 - c for c in pct_correct]
    ax.bar(x, errs, bottom=pct_correct, color=PAL["error"], width=0.85, linewidth=0)

    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("% of frames", fontsize=9)
    ax.set_xticks([])
    ax.set_xlabel("videos", fontsize=9)
    ax.set_xlim(-0.6, n - 0.4)

    h_correct = patches.Patch(facecolor=PAL["correct"], label="correctly labelled")
    h_err = patches.Patch(facecolor=PAL["error"], label="error")
    ax.legend(handles=[h_correct, h_err], loc="upper center",
              bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False,
              fontsize=8, handlelength=1.2, handleheight=1.2,
              columnspacing=1.4, handletextpad=0.5)


# ---------------------------------------------------------------------------
def panel_d(ax, data):
    """Paired boxplots vigilant / out_of_sight, gt vs predicted (frames)."""
    panel_label(ax, "d", x=-0.18, y=1.05, fontsize=12)

    behaviors = [2, 1]  # vigilant (label idx 2), out_of_sight (idx 1)
    display = {2: "vigilant", 1: "out of sight"}

    gt_counts = {b: [] for b in behaviors}
    pr_counts = {b: [] for b in behaviors}
    for v in data["gt"]:
        gt = np.array(data["gt"][v]); pr = np.array(data["pred"][v])
        for b in behaviors:
            gt_counts[b].append(int((gt == b).sum()))
            pr_counts[b].append(int((pr == b).sum()))

    width = 0.32
    positions_gt = np.array([0, 1]) - 0.21
    positions_pr = np.array([0, 1]) + 0.21

    for i, b in enumerate(behaviors):
        gt_vals = np.array(gt_counts[b])
        pr_vals = np.array(pr_counts[b])
        # Box outlines BLACK in source for both
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

        rng = np.random.default_rng(i + 7)
        jitter = rng.uniform(-0.03, 0.03, size=len(gt_vals))
        for g, p, j in zip(gt_vals, pr_vals, jitter):
            ax.plot([positions_gt[i] + j, positions_pr[i] + j], [g, p],
                    color="#9C9C9C", linewidth=0.5, zorder=1)
            ax.scatter([positions_gt[i] + j], [g], s=18,
                       color=PAL["groundtruth"], zorder=3, linewidths=0)
            ax.scatter([positions_pr[i] + j], [p], s=18,
                       color=PAL["predicted"], zorder=3, linewidths=0)

    ax.set_xticks([0, 1])
    ax.set_xticklabels([display[b] for b in behaviors], fontsize=8.5)
    for tl, b in zip(ax.get_xticklabels(), behaviors):
        tl.set_color(ZEBRA_COLORS[b])

    # Push the bottom further below 0 so the y=0 tick label has clear
    # separation from the axis line (matches the source typography and
    # ensures the label isn't clipped against the bottom x-axis text).
    ax.set_ylim(-1300, 17500)
    ax.set_yticks([0, 2500, 5000, 7500, 10000, 12500, 15000, 17500])
    ax.set_yticklabels(["0", "2500", "5000", "7500", "10000",
                        "12500", "15000", "17500"])
    ax.set_ylabel("frames", fontsize=9)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.4, color=PAL["grid"], alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.7, 1.7)

    h_gt = patches.Patch(facecolor=PAL["groundtruth"], label="groundtruth")
    h_pr = patches.Patch(facecolor=PAL["predicted"], label="predicted")
    ax.legend(handles=[h_gt, h_pr], loc="upper center",
              bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False,
              fontsize=8, handlelength=1.2, handleheight=1.2,
              columnspacing=1.4, handletextpad=0.5)


# ---------------------------------------------------------------------------
def panel_e(ax):
    """3x3 monkey behavior grid asset (single image)."""
    panel_label(ax, "e", x=-0.04, y=1.0, fontsize=12)
    img = mpimg.imread(os.path.join(HERE, "assets", "behavior_grid.png"))
    ax.imshow(img)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------------------
def _onehot_to_idx(arr2d):
    return np.argmax(np.array(arr2d), axis=1)


def panel_f(ax, data):
    """Multi-video ethogram: per-video small panels arranged side by side.

    Each video block: stacked 9 horizontal rows (one per class), filled
    where that class is active in labels / predictions respectively. Two
    blocks per video: top = labels, bottom = prediction. An "accuracy"
    row at the very top marks per-window-error class.
    """
    panel_label(ax, "f", x=-0.05, y=1.05, fontsize=12)

    videos = list(data["gt"].keys())
    # Sample ~12 videos spread across accuracy spectrum so the panel
    # shows variety without becoming a wall of stripes.
    n_show = 12
    accs = []
    for v in videos:
        g = _onehot_to_idx(data["gt"][v]); p = _onehot_to_idx(data["pred"][v])
        accs.append((v, (g == p).mean()))
    accs.sort(key=lambda kv: -kv[1])
    # Take every (len // n_show)-th to span the distribution
    step = max(1, len(accs) // n_show)
    selected = [accs[i] for i in range(0, len(accs), step)][:n_show]
    videos_show = [v for v, _ in selected]

    n_classes = len(MONKEY_F_ROW_ORDER)
    frames_per = 360
    gap = 32  # white gap between video blocks (frames-units)
    slot = frames_per + gap
    total_x = len(videos_show) * slot - gap

    # Layout (y is in arbitrary axes-data units; ascending = upward)
    # Top to bottom: accuracy row -> labels block (9 rows) -> prediction block (9 rows)
    row_h = 0.9             # height of one class row
    row_gap = 0.4           # vertical gap between rows
    block_gap = 1.2         # gap between accuracy/labels/prediction blocks
    acc_h = 0.9

    block_h = n_classes * row_h + (n_classes - 1) * row_gap

    # Anchor y=0 at bottom of prediction block; build upward.
    y_pred_bot = 0.0
    y_pred_top = y_pred_bot + block_h
    y_label_bot = y_pred_top + block_gap
    y_label_top = y_label_bot + block_h
    y_acc_bot = y_label_top + block_gap
    y_acc_top = y_acc_bot + acc_h

    def row_y(block_bot, row_idx_from_top):
        """Return (lo, hi) of a row, counted from top of block downward."""
        # rows stack from top -> bottom; row 0 is at the top
        y_top_of_row = block_bot + block_h - row_idx_from_top * (row_h + row_gap)
        y_bot_of_row = y_top_of_row - row_h
        return y_bot_of_row, y_top_of_row

    light_gray = "#EBECED"

    # Draw each video block
    for i, v in enumerate(videos_show):
        x0 = i * slot
        gt = _onehot_to_idx(data["gt"][v])
        pr = _onehot_to_idx(data["pred"][v])
        n = len(gt)

        # For each class row: first paint light gray background spanning
        # the whole block, then overlay colored segments where class active.
        for row_idx, cls in enumerate(MONKEY_F_ROW_ORDER):
            for block_bot, arr in [(y_label_bot, gt), (y_pred_bot, pr)]:
                lo, hi = row_y(block_bot, row_idx)
                # Light gray background
                ax.add_patch(patches.Rectangle(
                    (x0, lo), n, hi - lo,
                    facecolor=light_gray, linewidth=0, zorder=1,
                ))
                # Colored runs where this class is active
                mask = (arr == cls).astype(np.int8)
                if mask.any():
                    diffs = np.diff(np.concatenate(([0], mask, [0])))
                    starts = np.where(diffs == 1)[0]
                    ends = np.where(diffs == -1)[0]
                    for s, e in zip(starts, ends):
                        ax.add_patch(patches.Rectangle(
                            (x0 + s, lo), e - s, hi - lo,
                            facecolor=MONKEY_COLORS[cls], linewidth=0, zorder=2,
                        ))

        # Accuracy row: light gray background for the video span,
        # colored marks for error-frames keyed by the prediction class.
        ax.add_patch(patches.Rectangle(
            (x0, y_acc_bot), n, acc_h,
            facecolor=light_gray, linewidth=0, zorder=1,
        ))
        err_mask = (gt != pr).astype(np.int8)
        if err_mask.any():
            diffs = np.diff(np.concatenate(([0], err_mask, [0])))
            starts = np.where(diffs == 1)[0]
            ends = np.where(diffs == -1)[0]
            for s, e in zip(starts, ends):
                # Choose color = mode of the (wrong) prediction in this run
                run = pr[s:e]
                vals, counts = np.unique(run, return_counts=True)
                mode_cls = int(vals[np.argmax(counts)])
                ax.add_patch(patches.Rectangle(
                    (x0 + s, y_acc_bot), e - s, acc_h,
                    facecolor=MONKEY_COLORS[mode_cls], linewidth=0, zorder=2,
                ))

    # Row-section labels on the left
    y_acc_center = (y_acc_bot + y_acc_top) / 2
    y_label_center = (y_label_bot + y_label_top) / 2
    y_pred_center = (y_pred_bot + y_pred_top) / 2

    ax.text(-0.005, y_acc_center, "accuracy", transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=8.5)
    ax.text(-0.005, y_label_center, "labels", transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=8.5)
    ax.text(-0.005, y_pred_center, "prediction", transform=ax.get_yaxis_transform(),
            ha="right", va="center", fontsize=8.5)

    # 15-secs scale bar at lower-left, sized to ONE video block (360 frames).
    bar_y = -1.0
    bar_len = frames_per
    bar_x = 0
    ax.plot([bar_x, bar_x + bar_len], [bar_y, bar_y],
            color="#5A5A5A", linewidth=1.4, solid_capstyle="butt")
    ax.text(bar_x + bar_len / 2, bar_y - 0.6, "15 secs",
            ha="center", va="top", fontsize=8)

    # "videos" caption — centered under the lower half of f
    ax.text(total_x / 2, bar_y - 0.6, "videos",
            ha="center", va="top", fontsize=9)

    ax.set_xlim(-slot * 0.005, total_x + slot * 0.005)
    ax.set_ylim(bar_y - 2.0, y_acc_top + 0.4)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------------------
def panel_g(ax, data):
    """Stacked bars per monkey video: correct vs error."""
    panel_label(ax, "g", x=-0.10, y=1.05, fontsize=12)

    pct_correct = []
    for v in data["gt"]:
        g = _onehot_to_idx(data["gt"][v])
        p = _onehot_to_idx(data["pred"][v])
        pct_correct.append((g == p).mean() * 100)
    pct_correct = sorted(pct_correct, reverse=True)
    n = len(pct_correct)

    x = np.arange(n)
    ax.bar(x, pct_correct, color=PAL["correct"], width=0.78, linewidth=0)
    errs = [100 - c for c in pct_correct]
    ax.bar(x, errs, bottom=pct_correct, color=PAL["error"], width=0.78, linewidth=0)

    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("% of frames", fontsize=9)
    ax.set_xticks([])
    ax.set_xlabel("videos", fontsize=9)
    ax.set_xlim(-0.5, n - 0.5)

    h_correct = patches.Patch(facecolor=PAL["correct"], label="correctly labelled")
    h_err = patches.Patch(facecolor=PAL["error"], label="error")
    ax.legend(handles=[h_correct, h_err], loc="upper center",
              bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False,
              fontsize=8.5, handlelength=1.4, handleheight=1.4,
              columnspacing=1.6, handletextpad=0.5)


# ---------------------------------------------------------------------------
def panel_h(ax, data):
    """Per-class mAP bars + data proportion line (right y-axis).

    X-axis order: classes ordered by descending data proportion (matches the
    source figure: sitting, walking, standing, hanging, cam. interac.,
    climbing up, running, sit. on back, climbing down).
    """
    panel_label(ax, "h", x=-0.20, y=1.05, fontsize=12)

    gt_all = np.concatenate([np.array(data["gt"][v]) for v in data["gt"]], axis=0)
    pr_all = np.concatenate([np.array(data["pred"][v]) for v in data["gt"]], axis=0)
    n_classes = gt_all.shape[1]

    aps = {}
    props = {}
    for ki in range(n_classes):
        positives = gt_all[:, ki].sum()
        if positives == 0:
            aps[ki] = 0.0
            props[ki] = 0.0
            continue
        ap = average_precision_score(gt_all[:, ki], pr_all[:, ki])
        aps[ki] = ap * 100
        props[ki] = positives / gt_all.shape[0] * 100

    # Sort by descending data proportion (matches source x-axis order)
    sorted_idx = sorted(range(n_classes), key=lambda k: -props[k])
    names = [MONKEY_DISPLAY[k] for k in sorted_idx]
    ap_vals = [aps[k] for k in sorted_idx]
    prop_vals = [props[k] for k in sorted_idx]

    x = np.arange(len(sorted_idx))
    ax.bar(x, ap_vals, color=PAL["feral"], width=0.7, linewidth=0)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel("mAP (%)", fontsize=9)
    ax.set_xticks(x)
    short = {
        "camera interaction": "cam. interac.",
        "sitting on back": "sit on back",
    }
    display_names = [short.get(n, n) for n in names]
    ax.set_xticklabels(display_names, rotation=45, ha="right",
                       rotation_mode="anchor", fontsize=7.5)
    # Color each tick label by its class color
    for tl, k in zip(ax.get_xticklabels(), sorted_idx):
        # use the class color directly; for very light shades darken slightly
        c = MONKEY_COLORS[k]
        tl.set_color(c if c not in ("#DBDC8D", "#9EDAE6", "#A7A9AC") else "#444444")
    ax.tick_params(axis="x", length=0, pad=1)

    # Light horizontal grid for mAP axis
    ax.yaxis.grid(True, linestyle=":", linewidth=0.4, color=PAL["grid"], alpha=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.6, len(sorted_idx) - 0.4)

    # Right axis: data proportion line (dashed red)
    ax2 = ax.twinx()
    ax2.plot(x, prop_vals, color=PAL["red_line"], linestyle="--", linewidth=1.8,
             marker="", zorder=4, dash_capstyle="butt")
    ax2.set_ylim(0, 35)
    ax2.set_yticks([0, 5, 10, 15, 20, 25, 30, 35])
    ax2.set_ylabel("Data Proportion (%)", color=PAL["red_line"], fontsize=9)
    ax2.tick_params(axis="y", colors=PAL["red_line"])
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(PAL["red_line"])
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)


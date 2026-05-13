"""Figure 5 — Collective behavior (O. biroi raiding) + cross-dataset summary.

Panels:
    a) Two stacked rounded-box images (petri-dish photos) with dot+label headers
       for "no raiding" and "raiding".
    b) Example video 1 ethogram: labels strip + prediction strip (18000 frames,
       accuracy 96.3% — video 000004.mp4 from collective_ants.json).
    c) Confusion matrix (2x2) with circular-thumbnail examples on either side and
       curved arrows from off-diagonal cells to the thumbnails.
    d) mAP bar chart across 7 datasets (light blue).
    e) Hand-positioned 2x2 conceptual scatter — scene complexity (x) vs
       behavioral organization (y), with arrow-tipped axes.

Numeric values for panels a–d come from JSONs in figures/data/. Panel e is
schematic (no data file).
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
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _style import COLORS, apply_rcparams, panel_label  # noqa: E402


DATA_DIR = os.path.join(os.path.dirname(HERE), "data")


# ---------------------------------------------------------------------------
def load_collective_ants():
    with open(os.path.join(DATA_DIR, "collective_ants.json")) as f:
        return json.load(f)


def load_all_maps():
    files = {
        "mice (CalMS21)":        "calms.json",
        "C. elegans":            "worms.json",
        "O. biroi adult-larva":  "ants.json",
        "zebras":                "zebra.json",
        "primates (panAF500)":   "monkeys.json",
        "O. biroi colonies":     "collective_ants.json",
        "Beetles (MaBE)":        "mabe.json",
    }
    out = []
    for label, fn in files.items():
        with open(os.path.join(DATA_DIR, fn)) as f:
            d = json.load(f)
        out.append((label, d["metrics"]["map"] * 100))
    return out


# ---------------------------------------------------------------------------
def _hide_spines(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def panel_a(ax_top_dot, ax_top_img, ax_bot_dot, ax_bot_img, fig):
    """Two stacked petri-dish panels with dot+label header above each.

    Each image axis gets a rounded gray box outline drawn on the figure
    (so the box can extend slightly beyond the image edge for the source look).
    Dot+label header is centered horizontally above its box.
    """
    panel_label(ax_top_dot, "a", x=-0.30, y=1.50)

    # The dots are drawn as figure-coord circles after layout so they're
    # circular (not stretched by the axis aspect ratio).
    def _dot_header(ax, color, text):
        _hide_spines(ax)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        # Just place the text centered; the colored dot is drawn after layout
        # in figure coords (so it stays circular).
        ax.text(0.5, 0.5, text, ha="left", va="center", fontsize=10)
        ax._dot_color = color
        ax._dot_text = text

    _dot_header(ax_top_dot, COLORS["no_raiding"], "no raiding")
    _dot_header(ax_bot_dot, COLORS["raiding"],    "raiding")

    # Re-center the dot+text unit horizontally above the matching box.
    # Done at draw time so axes positions are settled. The dot+text is placed
    # at the dot AXIS vertical center (which already sits between rows of the
    # subgridspec).
    def _place_dots(event):
        fig.patches[:] = [
            p for p in fig.patches
            if getattr(p, "_fig5_panel_a_dot", False) is False
        ]
        for dot_ax, img_ax in [(ax_top_dot, ax_top_img),
                               (ax_bot_dot, ax_bot_img)]:
            color = getattr(dot_ax, "_dot_color")
            text  = getattr(dot_ax, "_dot_text")
            img_bb = img_ax.get_position()
            dot_bb = dot_ax.get_position()
            renderer = fig.canvas.get_renderer()
            txt_objs = [t for t in dot_ax.texts]
            if not txt_objs:
                continue
            t = txt_objs[0]
            bb_disp = t.get_window_extent(renderer=renderer)
            bb_fig = bb_disp.transformed(fig.transFigure.inverted())
            text_w = bb_fig.width
            text_h = bb_fig.height * 0.65
            dot_d = text_h * 1.30
            gap = dot_d * 0.55
            total_w = dot_d + gap + text_w
            center_x = img_bb.x0 + img_bb.width / 2
            unit_x0 = center_x - total_w / 2
            dot_cx = unit_x0 + dot_d / 2
            text_x = unit_x0 + dot_d + gap
            # Vertical center: above the dot_ax center so the dot+text sits
            # clearly above the box top edge.
            y_center = dot_bb.y0 + dot_bb.height * 0.95
            inv = dot_ax.transAxes.inverted()
            dot_axes_xy = inv.transform(
                fig.transFigure.transform((text_x, y_center))
            )
            t.set_position((dot_axes_xy[0], dot_axes_xy[1]))
            t.set_clip_on(False)
            circle = patches.Circle(
                (dot_cx, y_center), radius=dot_d / 2,
                facecolor=color, edgecolor="none",
                transform=fig.transFigure, zorder=6, clip_on=False,
            )
            circle._fig5_panel_a_dot = True
            fig.patches.append(circle)
    fig.canvas.mpl_connect("draw_event", _place_dots)

    for ax, fn in [(ax_top_img, "petri_no_raiding.png"),
                   (ax_bot_img, "petri_raiding.png")]:
        img = mpimg.imread(os.path.join(HERE, "assets", fn))
        ax.imshow(img, aspect="equal")
        _hide_spines(ax)

    # Draw rounded gray boxes around each image after first draw (so we know
    # the final position of each image axis in figure coords).
    def _draw_boxes(event):
        # Remove any previously added panel-a boxes
        fig.patches[:] = [
            p for p in fig.patches
            if getattr(p, "_fig5_panel_a_box", False) is False
        ]
        for ax in (ax_top_img, ax_bot_img):
            bb = ax.get_position()
            pad_x = 0.018
            pad_y_top = 0.005
            pad_y_bot = 0.022
            x0 = bb.x0 - pad_x
            y0 = bb.y0 - pad_y_bot
            w = bb.width + 2 * pad_x
            h = bb.height + pad_y_top + pad_y_bot
            box = patches.FancyBboxPatch(
                (x0, y0), w, h,
                boxstyle="round,pad=0.002,rounding_size=0.012",
                linewidth=0.9, edgecolor="#A0A0A0", facecolor="none",
                transform=fig.transFigure, zorder=5,
            )
            box._fig5_panel_a_box = True
            fig.patches.append(box)
    fig.canvas.mpl_connect("draw_event", _draw_boxes)


# ---------------------------------------------------------------------------
def _ethogram_row(ax, arr):
    arr = np.asarray(arr)
    n = len(arr)
    cuts = np.where(np.diff(arr) != 0)[0] + 1
    starts = np.concatenate(([0], cuts))
    ends = np.concatenate((cuts, [n]))
    for s, e in zip(starts, ends):
        c = COLORS["raiding"] if int(arr[s]) == 1 else COLORS["no_raiding"]
        ax.axvspan(s, e, ymin=0, ymax=1, facecolor=c, linewidth=0)


def panel_b(ax_title, ax_lbl, ax_pred, data, ax_frames=None):
    """Single example video ethogram (labels + prediction)."""
    panel_label(ax_title, "b", x=-0.07, y=0.35)

    vid = "000004.mp4"
    gt = np.array(data["gt"][vid])
    pr = np.array(data["pred"][vid])
    n = len(gt)
    acc = (gt == pr).mean() * 100

    for ax, arr in [(ax_lbl, gt), (ax_pred, pr)]:
        _ethogram_row(ax, arr)
        ax.set_xlim(0, n); ax.set_ylim(0, 1)
        ax.set_yticks([]); ax.set_xticks([])
        for s in ax.spines.values():
            s.set_visible(False)

    # X-axis on prediction strip
    ax_pred.set_xticks([0, n])
    ax_pred.set_xticklabels(["0", str(n)], fontsize=8.5)
    ax_pred.tick_params(axis="x", length=0, pad=3)
    for tl in ax_pred.get_xticklabels():
        tl.set_clip_on(False)
    # Anchor the end-tick labels so they sit INSIDE the figure margin.
    labels = ax_pred.get_xticklabels()
    labels[0].set_ha("left")
    labels[-1].set_ha("right")

    # Row labels
    ax_lbl.text(-0.015, 0.5, "labels", transform=ax_lbl.transAxes,
                ha="right", va="center", fontsize=9)
    ax_pred.text(-0.015, 0.5, "prediction", transform=ax_pred.transAxes,
                 ha="right", va="center", fontsize=9)

    # Title (italic — matches source)
    _hide_spines(ax_title)
    ax_title.set_xlim(0, 1); ax_title.set_ylim(0, 1)
    ax_title.text(0.0, 0.5,
                  f"Example video 1: accuracy {acc:.1f}%",
                  ha="left", va="center", fontsize=9.5, fontstyle="italic")

    # "frames" caption in its own axis row.
    if ax_frames is not None:
        _hide_spines(ax_frames)
        ax_frames.set_xlim(0, 1); ax_frames.set_ylim(0, 1)
        ax_frames.set_facecolor("none")
        ax_frames.patch.set_alpha(0.0)
        ax_frames.text(0.5, 0.3, "frames", transform=ax_frames.transAxes,
                       ha="center", va="center", fontsize=9.5,
                       clip_on=False)
    else:
        ax_pred.text(0.5, -1.45, "frames", transform=ax_pred.transAxes,
                     ha="center", va="top", fontsize=9.5)


# ---------------------------------------------------------------------------
def panel_c(ax_left_img, ax_cm, ax_cbar, ax_right_img, data, fig):
    """Confusion matrix flanked by two circular thumbnails with curved arrows."""
    panel_label(ax_left_img, "c", x=-0.05, y=1.02)

    # Compute combined confusion matrix
    all_g = np.concatenate([np.array(data["gt"][k]) for k in data["gt"]])
    all_p = np.concatenate([np.array(data["pred"][k]) for k in data["pred"]])
    cm_raw = np.zeros((2, 2), dtype=int)  # rows=gt {0,1}, cols=pred {0,1}
    for gv in (0, 1):
        for pv in (0, 1):
            cm_raw[gv, pv] = int(((all_g == gv) & (all_p == pv)).sum())

    # Order for display: rows = [raiding(1), no_raiding(0)],
    #                    cols = [raiding(1), no_raiding(0)]
    cm = np.array([
        [cm_raw[1, 1], cm_raw[1, 0]],   # GT raiding
        [cm_raw[0, 1], cm_raw[0, 0]],   # GT no_raiding
    ])

    # Off-diagonal heatmap; diagonal forced gray
    mask_diag = np.eye(2, dtype=bool)
    off = np.where(mask_diag, np.nan, cm).astype(float)

    cmap = LinearSegmentedColormap.from_list(
        "blues", [COLORS["heatmap_lo"], COLORS["heatmap_hi"]]
    )
    cmap.set_bad(COLORS["diag_gray"])
    vmax = float(cm[~mask_diag].max())
    im = ax_cm.imshow(off, cmap=cmap, vmin=0, vmax=vmax)

    # Diagonal as gray rectangles (clean edges)
    for i in range(2):
        ax_cm.add_patch(patches.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                          facecolor=COLORS["diag_gray"],
                                          edgecolor="white", linewidth=0.5))

    # Cell text
    for r in range(2):
        for c in range(2):
            v = cm[r, c]
            if mask_diag[r, c]:
                color = "black"
            else:
                color = "white" if v > vmax * 0.5 else "black"
            ax_cm.text(c, r, f"{v}", ha="center", va="center",
                       fontsize=8.5, color=color)

    # Tick labels in class colors
    ax_cm.set_xticks([0, 1])
    ax_cm.set_yticks([0, 1])
    ax_cm.set_xticklabels(["raiding", "no raiding"], fontsize=8.5)
    ax_cm.set_yticklabels(["raiding", "no raiding"], fontsize=8.5, rotation=90,
                          va="center")
    for tl, c in zip(ax_cm.get_xticklabels(),
                     [COLORS["raiding"], COLORS["no_raiding"]]):
        tl.set_color(c)
    for tl, c in zip(ax_cm.get_yticklabels(),
                     [COLORS["raiding"], COLORS["no_raiding"]]):
        tl.set_color(c)

    ax_cm.set_xlabel("predicted", labelpad=4)
    ax_cm.set_ylabel("groundtruth", labelpad=4)
    ax_cm.tick_params(length=0)
    for s in ax_cm.spines.values():
        s.set_visible(False)
    ax_cm.set_xlim(-0.5, 1.5); ax_cm.set_ylim(1.5, -0.5)

    # Colorbar
    cb = plt.colorbar(im, cax=ax_cbar, orientation="vertical")
    max_round = int(np.ceil(vmax / 100.0) * 100)
    ticks = [0, 100, 200, 300, max_round] if max_round > 300 else [0, 100, 200, 300]
    # Pick clean ticks
    ticks = [0, 100, 200, 300]
    cb.set_ticks(ticks)
    ax_cbar.tick_params(labelsize=8, length=2)
    ax_cbar.set_ylabel("misclassified frames", fontsize=8.5, labelpad=4)
    cb.outline.set_linewidth(0.5)

    # Left + right circular thumbnails
    for ax, fn in [(ax_left_img,  "petri_c_left.png"),
                   (ax_right_img, "petri_c_right.png")]:
        img = mpimg.imread(os.path.join(HERE, "assets", fn))
        ax.imshow(img)
        _hide_spines(ax)

    # Curved arrows: from off-diagonal cells (CM) to the thumbnails.
    # Off-diagonal cell positions in ax_cm data coords:
    #   (col=0, row=1)  -> GT no_raiding, predicted raiding  = misclassified as raiding -> LEFT thumb
    #   (col=1, row=0)  -> GT raiding, predicted no_raiding  = missed raiding -> RIGHT thumb
    # FancyArrowPatch with figure transform for cross-axes arrows.

    def _arrow(src_ax, src_xy, dst_ax, dst_xy, rad):
        # Convert points to figure coords
        src = src_ax.transData.transform(src_xy)
        dst = dst_ax.transAxes.transform(dst_xy)
        src_fig = fig.transFigure.inverted().transform(src)
        dst_fig = fig.transFigure.inverted().transform(dst)
        arr = FancyArrowPatch(
            src_fig, dst_fig,
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>,head_length=6,head_width=4",
            color="#9A9A9A", linewidth=0.9,
            transform=fig.transFigure,
        )
        fig.patches.append(arr)

    # Curved arrows between cells and thumbnails — added directly using
    # axes-blended transforms. Using FancyArrowPatch with both endpoints
    # specified via xycoords lets matplotlib resolve them at draw-time.
    #
    # Left thumb: example of a frame "misclassified AS raiding" =>
    #             arrow from off-diag cell (col=0=raiding, row=1=no_raiding) = "294"
    # Right thumb: example of a "missed raiding" frame =>
    #              arrow from off-diag cell (col=1=no_raiding, row=0=raiding) = "376"

    # Defer real arrow creation until after first layout so transforms settle.
    def _add_arrows():
        # Source layout:
        #   - Arrow from "294" cell (bottom-left off-diag) curves DOWN-LEFT
        #     to the LEFT thumbnail (curve sweeps below).
        #   - Arrow from "376" cell (top-right off-diag) curves UP-RIGHT
        #     to the RIGHT thumbnail (curve sweeps above).

        # 294 cell: data (0, 1); start from left-mid edge of cell.
        src1 = ax_cm.transData.transform((-0.55, 1.05))
        dst1 = ax_left_img.transAxes.transform((1.00, 0.42))
        src1f = fig.transFigure.inverted().transform(src1)
        dst1f = fig.transFigure.inverted().transform(dst1)
        a1 = FancyArrowPatch(
            src1f, dst1f,
            connectionstyle="arc3,rad=0.45",
            arrowstyle="-|>,head_length=7,head_width=4.5",
            color="#9A9A9A", linewidth=1.1,
            transform=fig.transFigure, zorder=20,
        )
        fig.patches.append(a1)

        # 376 cell: data (1, 0); start from right-mid edge of cell.
        src2 = ax_cm.transData.transform((1.55, -0.05))
        dst2 = ax_right_img.transAxes.transform((0.00, 0.55))
        src2f = fig.transFigure.inverted().transform(src2)
        dst2f = fig.transFigure.inverted().transform(dst2)
        a2 = FancyArrowPatch(
            src2f, dst2f,
            connectionstyle="arc3,rad=-0.45",
            arrowstyle="-|>,head_length=7,head_width=4.5",
            color="#9A9A9A", linewidth=1.1,
            transform=fig.transFigure, zorder=20,
        )
        fig.patches.append(a2)

    # Stash so main() can call after canvas.draw()
    fig._panel_c_add_arrows = _add_arrows


# ---------------------------------------------------------------------------
def panel_d(ax, maps):
    """mAP bar chart, 7 datasets, light blue."""
    panel_label(ax, "d", x=-0.10, y=1.05)

    labels = [m[0] for m in maps]
    vals = [m[1] for m in maps]

    # Use italic for binomial names (those starting with "C. elegans", "O. biroi")
    def _italic(label):
        return label.startswith("C. elegans") or label.startswith("O. biroi")

    x = np.arange(len(vals))
    ax.bar(x, vals, color=COLORS["feral"], width=0.8, linewidth=0)

    ax.set_ylim(0, 108)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel("mAP (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", rotation_mode="anchor",
                       fontsize=8.0)
    for tl, lbl in zip(ax.get_xticklabels(), labels):
        if _italic(lbl):
            tl.set_fontstyle("italic")

    # Number on top of each bar
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.5, f"{v:.1f}", ha="center", va="bottom",
                fontsize=8.5, color="black")

    ax.tick_params(axis="x", length=0, pad=4)
    ax.set_xlim(-0.6, len(vals) - 0.4)


# ---------------------------------------------------------------------------
def panel_e(ax):
    """Hand-positioned 2x2 conceptual scatter with arrow-tipped axes."""
    panel_label(ax, "e", x=-0.18, y=1.00)

    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    # Box covers most of the axes; leave room for outside-axis labels.
    box_x0, box_x1 = 0.16, 0.84
    box_y0, box_y1 = 0.12, 0.90
    mid_x = (box_x0 + box_x1) / 2
    mid_y = (box_y0 + box_y1) / 2

    # The frame: left + bottom are plain lines; top + right have arrowheads.
    line_kw = dict(color=COLORS["axis"], lw=1.1, clip_on=False, solid_capstyle="butt")
    ax.plot([box_x0, box_x0], [box_y0, box_y1], **line_kw)
    ax.plot([box_x0, box_x1], [box_y0, box_y0], **line_kw)
    ax.annotate("", xy=(box_x1 + 0.05, box_y1),
                xytext=(box_x0, box_y1),
                arrowprops=dict(arrowstyle="-|>",
                                color=COLORS["axis"], lw=1.1,
                                mutation_scale=15, shrinkA=0, shrinkB=0),
                annotation_clip=False)
    ax.annotate("", xy=(box_x1, box_y1 + 0.07),
                xytext=(box_x1, box_y0),
                arrowprops=dict(arrowstyle="-|>",
                                color=COLORS["axis"], lw=1.1,
                                mutation_scale=15, shrinkA=0, shrinkB=0),
                annotation_clip=False)

    # Axis labels (outside the box)
    # Top
    ax.text(mid_x, box_y1 + 0.13, "tracking instability",
            ha="center", va="bottom", fontsize=9, clip_on=False)
    # Bottom
    ax.text(mid_x, box_y0 - 0.08, "scene complexity",
            ha="center", va="top", fontsize=9, clip_on=False)
    # Right axis stack: "harder" (italic) near top, "segmentation" middle (plain),
    # "easier" (italic) near bottom — all rotated 90° outside the right edge.
    x_right = box_x1 + 0.07
    box_h = box_y1 - box_y0
    # Push easier/harder all the way to the corners; segmentation is centered.
    y_easier  = box_y0 + box_h * 0.05
    y_seg     = box_y0 + box_h * 0.50
    y_harder  = box_y0 + box_h * 0.95
    # Use figure-level annotate so the text positions are absolute and
    # not affected by axes clipping behavior.
    ax.annotate("easier", xy=(x_right, y_easier), xycoords="data",
                ha="center", va="center", fontsize=8, fontstyle="italic",
                rotation=90, annotation_clip=False)
    ax.annotate("segmentation", xy=(x_right, y_seg), xycoords="data",
                ha="center", va="center", fontsize=8.5,
                rotation=90, annotation_clip=False)
    ax.annotate("harder", xy=(x_right, y_harder), xycoords="data",
                ha="center", va="center", fontsize=8, fontstyle="italic",
                rotation=90, annotation_clip=False)
    # Left axis: "behavioral organization" — TWO stacked rotated lines, the
    # outer line (organization) is FARTHER from the box.
    # In source, "behavioral" reads top-to-bottom as the FIRST line, then
    # "organization" reads top-to-bottom as the SECOND line (offset to the left).
    ax.text(box_x0 - 0.08, mid_y, "behavioral",
            ha="center", va="center", fontsize=9, rotation=90,
            rotation_mode="anchor", clip_on=False)
    ax.text(box_x0 - 0.14, mid_y, "organization",
            ha="center", va="center", fontsize=9, rotation=90,
            rotation_mode="anchor", clip_on=False)

    # Labels inside the box — hand-placed to match source.
    ORANGE = COLORS["raiding"]
    LIME = "#7BBE3F"
    DARK_GREEN = COLORS["investigate"]
    BLUE = COLORS["feral"]
    # (italic_part, plain_part_or_None, x, y, color)
    items = [
        ("O. biroi colonies",     None,           0.42, 0.78, ORANGE),      # upper-mid
        ("primates",              None,           0.70, 0.68, DARK_GREEN),  # upper-right
        ("CalMS21",               None,           0.36, 0.58, LIME),        # middle-left
        ("O. biroi",              " adult-larva", 0.58, 0.46, DARK_GREEN),  # center
        ("C. elegans",            None,           0.36, 0.32, BLUE),        # lower-left
        ("zebras",                None,           0.70, 0.30, BLUE),        # lower-right
    ]
    for italic_part, plain_part, x, y, color in items:
        if plain_part is None:
            is_italic = ("O. biroi" in italic_part) or ("C. elegans" in italic_part)
            kw = dict(ha="center", va="center", fontsize=9.5, color=color,
                      clip_on=False)
            if is_italic:
                kw["fontstyle"] = "italic"
            ax.text(x, y, italic_part, **kw)
        else:
            ax.text(x, y, italic_part,
                    ha="right", va="center",
                    fontsize=9.5, color=color,
                    fontstyle="italic", clip_on=False)
            ax.text(x, y, plain_part,
                    ha="left", va="center",
                    fontsize=9.5, color=color, clip_on=False)


# ---------------------------------------------------------------------------
def main(out=None):
    apply_rcparams()
    data = load_collective_ants()
    maps = load_all_maps()

    fig = plt.figure(figsize=(7.9, 6.44))

    # Master 3-row gridspec
    gs = fig.add_gridspec(
        3, 1,
        height_ratios=[1.30, 0.90, 1.55],
        hspace=0.55,
        left=0.08, right=0.97, top=0.96, bottom=0.15,
    )

    # ---- Row 1: panel a (left), panel b (right) ----
    row1 = gs[0].subgridspec(1, 2, width_ratios=[1.0, 2.7], wspace=0.30)

    # Panel a: two stacked (dot-header + image) rows.
    # Image rows need enough height so the 2:1 wide petri photos render at
    # natural aspect inside the rounded gray boxes (matches source look).
    a_sub = row1[0].subgridspec(
        4, 1,
        height_ratios=[0.20, 1.0, 0.20, 1.0],
        hspace=0.50,
    )
    ax_a_top_dot = fig.add_subplot(a_sub[0])
    ax_a_top_img = fig.add_subplot(a_sub[1])
    ax_a_bot_dot = fig.add_subplot(a_sub[2])
    ax_a_bot_img = fig.add_subplot(a_sub[3])
    panel_a(ax_a_top_dot, ax_a_top_img, ax_a_bot_dot, ax_a_bot_img, fig)

    # Panel b: title row + labels strip + prediction strip + frames caption row
    b_sub = row1[1].subgridspec(
        4, 1,
        height_ratios=[0.32, 0.55, 0.55, 0.20],
        hspace=0.15,
    )
    ax_b_title = fig.add_subplot(b_sub[0])
    ax_b_lbl   = fig.add_subplot(b_sub[1])
    ax_b_pred  = fig.add_subplot(b_sub[2])
    ax_b_frames = fig.add_subplot(b_sub[3])
    panel_b(ax_b_title, ax_b_lbl, ax_b_pred, data, ax_b_frames)

    # ---- Row 2: panel c (left thumb | matrix+cbar | right thumb) ----
    row2 = gs[1].subgridspec(
        1, 4,
        width_ratios=[0.75, 1.30, 0.09, 0.75],
        wspace=0.35,
    )
    ax_c_left  = fig.add_subplot(row2[0])
    ax_c_cm    = fig.add_subplot(row2[1])
    ax_c_cbar  = fig.add_subplot(row2[2])
    ax_c_right = fig.add_subplot(row2[3])
    panel_c(ax_c_left, ax_c_cm, ax_c_cbar, ax_c_right, data, fig)

    # ---- Row 3: panel d (wider left), panel e (narrower right) ----
    row3 = gs[2].subgridspec(1, 2, width_ratios=[1.40, 1.0], wspace=0.40)
    ax_d = fig.add_subplot(row3[0])
    ax_e = fig.add_subplot(row3[1])
    panel_d(ax_d, maps)
    panel_e(ax_e)

    # ---- Output ----
    # Draw once so positions settle, then add cross-axes patches that depend
    # on those positions (panel-a rounded boxes + panel-c curved arrows).
    fig.canvas.draw()
    if hasattr(fig, "_panel_c_add_arrows"):
        fig._panel_c_add_arrows()

    if out is None:
        out = os.path.join(HERE, "figure5_remade.png")
    fig.savefig(out, dpi=300)
    print(f"wrote {out}")
    return fig


if __name__ == "__main__":
    main()

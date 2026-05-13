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


def panel_a(ax_top_dot, ax_top_img, ax_bot_dot, ax_bot_img, fig,
            show_headers=True):
    """Two stacked petri-dish panels with optional dot+label header above each.

    Each image axis gets a rounded gray box outline drawn on the figure
    (so the box can extend slightly beyond the image edge for the source look).

    When `show_headers=False`, the dot+label header is NOT drawn — the
    HTML composition layer (figure5.html) overlays a CSS dot + text so
    the circles render crisply at any zoom.
    """
    panel_label(ax_top_dot, "a", x=-0.30, y=1.50)

    def _hide(ax):
        _hide_spines(ax)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    if show_headers:
        # The dots are drawn as figure-coord circles after layout so they're
        # circular (not stretched by the axis aspect ratio).
        def _dot_header(ax, color, text):
            _hide(ax)
            # Just place the text centered; the colored dot is drawn after
            # layout in figure coords (so it stays circular).
            ax.text(0.5, 0.5, text, ha="left", va="center", fontsize=10)
            ax._dot_color = color
            ax._dot_text = text

        _dot_header(ax_top_dot, COLORS["no_raiding"], "no raiding")
        _dot_header(ax_bot_dot, COLORS["raiding"],    "raiding")
    else:
        _hide(ax_top_dot)
        _hide(ax_bot_dot)

    # Re-center the dot+text unit horizontally above the matching box.
    # Done at draw time so axes positions are settled. The dot+text is placed
    # at the dot AXIS vertical center (which already sits between rows of the
    # subgridspec).
    def _place_dots(event):
        # No-op when the HTML layer is drawing the dot+text headers.
        if not show_headers:
            return
        fig.patches[:] = [
            p for p in fig.patches
            if getattr(p, "_fig5_panel_a_dot", False) is False
        ]
        renderer = getattr(event, "renderer", None) or fig.canvas.get_renderer()
        for dot_ax, img_ax in [(ax_top_dot, ax_top_img),
                               (ax_bot_dot, ax_bot_img)]:
            color = getattr(dot_ax, "_dot_color", None)
            text  = getattr(dot_ax, "_dot_text", None)
            if color is None or text is None:
                continue
            # Use the actual rendered image extent (aspect='equal' shrinks
            # the data area inside the slot), so we center above the IMAGE.
            if img_ax.images:
                img_bb_disp = img_ax.images[0].get_window_extent(renderer)
                img_bb = img_bb_disp.transformed(fig.transFigure.inverted())
            else:
                img_bb = img_ax.get_position()
            dot_bb = dot_ax.get_position()
            # Match by content; ax_top_dot also carries the "a" panel label.
            txt_objs = [tx for tx in dot_ax.texts if tx.get_text() == text]
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
            # Vertical center: above the top edge of the rounded box so the
            # dot+label has full clearance.  The box top sits at img_bb.y1
            # plus a small pad — push label well above that.
            box_top = img_bb.y1 + 0.010   # pad_y from _draw_boxes
            y_center = box_top + 0.018
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

    # Draw a rounded gray box around each two-dish asset.  Because aspect='equal'
    # shrinks the data area inside the gridspec slot, we compute the box from
    # the IMAGE's actual rendered window extent (not the slot bbox).
    def _draw_boxes(event):
        fig.patches[:] = [
            p for p in fig.patches
            if getattr(p, "_fig5_panel_a_box", False) is False
        ]
        renderer = getattr(event, "renderer", None) or fig.canvas.get_renderer()
        for ax in (ax_top_img, ax_bot_img):
            if not ax.images:
                continue
            disp = ax.images[0].get_window_extent(renderer)
            bb = disp.transformed(fig.transFigure.inverted())
            pad_x = 0.012
            pad_y = 0.010
            x0 = bb.x0 - pad_x
            y0 = bb.y0 - pad_y
            w = bb.width + 2 * pad_x
            h = bb.height + 2 * pad_y
            box = patches.FancyBboxPatch(
                (x0, y0), w, h,
                boxstyle="round,pad=0.0,rounding_size=0.012",
                linewidth=0.9, edgecolor="#A8A8A8", facecolor="none",
                transform=fig.transFigure, zorder=5, clip_on=False,
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


def panel_b(ax_title, ax_lbl, ax_pred, data, ax_frames=None, fig=None):
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

    # Title (italic — matches source); the accuracy number is bold-italic.
    _hide_spines(ax_title)
    ax_title.set_xlim(0, 1); ax_title.set_ylim(0, 1)
    t1 = ax_title.text(0.0, 0.5,
                       "Example video 1: accuracy ",
                       ha="left", va="center", fontsize=9.5,
                       fontstyle="italic")
    # Render bold portion right after the first, using a draw-time offset.
    bold_text = ax_title.text(0.0, 0.5,
                              f"{acc:.1f}%",
                              ha="left", va="center", fontsize=9.5,
                              fontstyle="italic", fontweight="bold")

    if fig is not None:
        def _place_bold(event):
            renderer = getattr(event, "renderer", None) or fig.canvas.get_renderer()
            bb = t1.get_window_extent(renderer=renderer)
            bb_ax = bb.transformed(ax_title.transAxes.inverted())
            bold_text.set_x(bb_ax.x1)
        fig.canvas.mpl_connect("draw_event", _place_bold)

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
    im = ax_cm.imshow(off, cmap=cmap, vmin=0, vmax=vmax, aspect="equal")

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
    ax_cm.set_yticklabels(["raiding", "no raiding"], fontsize=8.5,
                          rotation=0, ha="right", va="center")
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

    # Tuck the colorbar tight against the right edge of the (aspect-equal)
    # matrix.  Aspect='equal' shrinks the matrix inside its slot, so the cbar
    # axis (which was placed in the next gridspec column) is otherwise too far
    # to the right.
    def _tuck_cbar(event):
        renderer = getattr(event, "renderer", None) or fig.canvas.get_renderer()
        if not ax_cm.images:
            return
        cm_ext = ax_cm.images[0].get_window_extent(renderer)
        cm_ext = cm_ext.transformed(fig.transFigure.inverted())
        cbar_pos = ax_cbar.get_position()
        # Place the cbar 1.5% of figure-width to the right of matrix right edge,
        # vertically aligned with the matrix and same height.
        new_x0 = cm_ext.x1 + 0.012
        ax_cbar.set_position([
            new_x0, cm_ext.y0, cbar_pos.width, cm_ext.height,
        ])
    fig.canvas.mpl_connect("draw_event", _tuck_cbar)

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
    # Right-axis labels: two columns.  "segmentation" sits CLOSER to the box
    # (full-height rotated label); "easier" (bottom) and "harder" (top) sit
    # in a SECOND column further to the right.
    x_seg   = box_x1 + 0.05
    x_outer = box_x1 + 0.11
    ax.annotate("segmentation", xy=(x_seg, (box_y0 + box_y1) / 2),
                xycoords="data",
                ha="center", va="center", fontsize=9,
                rotation=90, rotation_mode="anchor", annotation_clip=False)
    ax.annotate("easier", xy=(x_outer, box_y0 + 0.10 * (box_y1 - box_y0)),
                xycoords="data",
                ha="left", va="center", fontsize=8, fontstyle="italic",
                rotation=90, rotation_mode="anchor", annotation_clip=False)
    ax.annotate("harder", xy=(x_outer, box_y1 - 0.10 * (box_y1 - box_y0)),
                xycoords="data",
                ha="right", va="center", fontsize=8, fontstyle="italic",
                rotation=90, rotation_mode="anchor", annotation_clip=False)
    # Left axis: "behavioral organization" — TWO stacked rotated lines.
    # In source, "behavioral" is FARTHER from the box (leftmost column),
    # "organization" is CLOSER to the box (rightmost column).  Both read
    # bottom-to-top (90° rotation).
    ax.text(box_x0 - 0.14, mid_y, "behavioral",
            ha="center", va="center", fontsize=9, rotation=90,
            rotation_mode="anchor", clip_on=False)
    ax.text(box_x0 - 0.07, mid_y, "organization",
            ha="center", va="center", fontsize=9, rotation=90,
            rotation_mode="anchor", clip_on=False)

    # Labels inside the box — hand-placed to match source.
    ORANGE = COLORS["raiding"]
    LIME = "#7BBE3F"
    DARK_GREEN = COLORS["investigate"]
    DARK_BLUE = "#2C5AA0"          # C. elegans — navy
    LIGHT_BLUE = COLORS["feral"]   # zebras — sky blue
    # (italic_part, plain_part_or_None, x, y, color)
    items = [
        ("O. biroi colonies",     None,           0.42, 0.78, ORANGE),      # upper-mid
        ("primates",              None,           0.68, 0.68, DARK_GREEN),  # upper-right
        ("CalMS21",               None,           0.34, 0.58, LIME),        # middle-left
        # Pull "O. biroi adult-larva" left so the trailing "-larva"
        # doesn't run into the right-axis "segmentation" label.
        ("O. biroi",              " adult-larva", 0.50, 0.46, DARK_GREEN),  # center
        ("C. elegans",            None,           0.38, 0.30, DARK_BLUE),   # lower-left
        ("zebras",                None,           0.68, 0.30, LIGHT_BLUE),  # lower-right
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


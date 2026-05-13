"""Programmatic layout checks for figures.

Two things to guarantee:
  1. Embedded photos (imshow) are not squished — aspect must be preserved.
  2. No two axes overlap (except legitimate parents: colorbars, twins).
  3. No text element bleeds across into another axes' content area.

Usage:

    from figures._layout_check import check_figure
    fig = make_my_figure()
    check_figure(fig, raise_on_error=True)

The default is to print a report and return a list of issues; pass
`raise_on_error=True` to make CI fail on overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox


# ---------------------------------------------------------------------------
@dataclass
class Issue:
    kind: str
    detail: str
    severity: str = "warning"   # "warning" | "error"


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def add(self, *args, **kwargs):
        self.issues.append(Issue(*args, **kwargs))

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def summary(self) -> str:
        if not self.issues:
            return "layout check: clean (no overlaps, no squished images)"
        lines = [f"layout check: {len(self.issues)} issue(s)"]
        for i in self.issues:
            lines.append(f"  [{i.severity}] {i.kind}: {i.detail}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
def _bbox_in_fig_coords(ax: Axes) -> Bbox:
    """The axes' Position bbox (in figure-relative coords, 0..1)."""
    return ax.get_position()


def _bbox_overlaps(b1: Bbox, b2: Bbox, eps: float = 1e-4) -> bool:
    """True if two bboxes intersect by more than `eps` (figure-relative)."""
    if b1.x1 - b2.x0 < eps or b2.x1 - b1.x0 < eps:
        return False
    if b1.y1 - b2.y0 < eps or b2.y1 - b1.y0 < eps:
        return False
    return True


def _is_ancestor(child: Axes, parent: Axes) -> bool:
    """True if `child` is a colorbar/twin/share spawned from `parent`."""
    # Twin axes share xaxis or yaxis with parent.
    try:
        if child._sharex is parent or child._sharey is parent:
            return True
        if parent._sharex is child or parent._sharey is child:
            return True
    except AttributeError:
        pass
    # Colorbars: matplotlib tags them on the axes.
    if getattr(child, "_colorbar", None) is parent:
        return True
    if getattr(parent, "_colorbar", None) is child:
        return True
    return False


# ---------------------------------------------------------------------------
def check_aspects(
    fig: Figure,
    report: Report,
    *,
    image_aspect_tolerance: float = 0.03,
) -> Report:
    """Flag any imshow axes whose rendered cell shape distorts the image."""
    fig.canvas.draw()
    for ax in fig.axes:
        for im in ax.images:
            arr = im.get_array()
            if arr is None:
                continue
            ih, iw = arr.shape[:2]
            img_aspect = iw / ih               # width / height (image)
            bbox = ax.get_window_extent()
            ax_aspect = bbox.width / bbox.height
            # Allow flips and rounding; compare the bigger to the smaller.
            ratio = img_aspect / ax_aspect if ax_aspect > 0 else float("inf")
            distortion = abs(ratio - 1)
            if distortion > image_aspect_tolerance:
                report.add(
                    "aspect_squish",
                    f"axes={ax.get_label() or id(ax)}  image is "
                    f"{img_aspect:.2f} wide-per-tall but axes is "
                    f"{ax_aspect:.2f} ({distortion*100:.1f}% off). "
                    f"Set aspect='equal' or change the gridspec slot.",
                    severity="error" if distortion > 0.10 else "warning",
                )
    return report


def check_axes_overlap(
    fig: Figure,
    report: Report,
    *,
    ignore_labels: Sequence[str] = (),
) -> Report:
    """Flag any two axes whose figure-coord bboxes intersect.

    Twins, colorbar children and axes whose labels are in `ignore_labels`
    are exempted. Note: matplotlib gridspec lays things out in figure
    coordinates, so positions are already pre-draw-stable.
    """
    axes_list = [
        a for a in fig.axes
        if not (a.get_label() in ignore_labels)
    ]
    for i, a in enumerate(axes_list):
        for b in axes_list[i + 1:]:
            if _is_ancestor(a, b):
                continue
            ba = _bbox_in_fig_coords(a)
            bb = _bbox_in_fig_coords(b)
            if _bbox_overlaps(ba, bb):
                report.add(
                    "axes_overlap",
                    f"{a.get_label() or 'ax'} ↔ {b.get_label() or 'ax'} "
                    f"(figure coords  {ba}  vs  {bb})",
                    severity="error",
                )
    return report


def check_text_overflow(
    fig: Figure,
    report: Report,
    *,
    margin_px: float = 2.0,
) -> Report:
    """Flag text whose pixel bbox extends *into* another axes' interior.

    Text inside its own axes is fine; text overflowing into a neighbor
    axis is the failure case.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    axes_bboxes = [(ax, ax.get_window_extent(renderer)) for ax in fig.axes]

    for ax in fig.axes:
        for t in list(ax.texts):
            try:
                tb = t.get_window_extent(renderer)
            except Exception:
                continue
            for other_ax, other_bb in axes_bboxes:
                if other_ax is ax:
                    continue
                if _is_ancestor(ax, other_ax) or _is_ancestor(other_ax, ax):
                    continue
                # Does the text bbox intrude into this other axis?
                inter = Bbox.intersection(tb, other_bb)
                if inter is None or inter.width <= margin_px or inter.height <= margin_px:
                    continue
                report.add(
                    "text_intrudes_into_axes",
                    f"text {t.get_text()!r} from {ax.get_label() or 'ax'} "
                    f"overlaps axes {other_ax.get_label() or 'ax'} by "
                    f"{int(inter.width)}x{int(inter.height)} px",
                    severity="warning",
                )
    return report


# ---------------------------------------------------------------------------
def check_figure(
    fig: Figure,
    *,
    image_aspect_tolerance: float = 0.03,
    text_margin_px: float = 2.0,
    raise_on_error: bool = False,
    print_report: bool = True,
) -> Report:
    """Run all checks; return Report; optionally raise if any error."""
    report = Report()
    check_aspects(fig, report, image_aspect_tolerance=image_aspect_tolerance)
    check_axes_overlap(fig, report)
    check_text_overflow(fig, report, margin_px=text_margin_px)
    if print_report:
        print(report.summary())
    if raise_on_error and not report.ok:
        raise RuntimeError("layout check failed:\n" + report.summary())
    return report


if __name__ == "__main__":
    # Self-test: a tiny figure with intentionally overlapping axes
    fig, axs = plt.subplots(2, 2, figsize=(4, 3))
    # Move ax[0,0] so it overlaps ax[0,1]
    pos = axs[0, 0].get_position()
    axs[0, 0].set_position([pos.x0, pos.y0, pos.width * 1.5, pos.height])
    r = check_figure(fig, raise_on_error=False, print_report=True)
    print(f"\nself-test ok? {r.ok} (expected False if overlap detected)")
